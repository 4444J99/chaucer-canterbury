"""FastAPI + SQLite server exposing the chaucer-canterbury computational philology
and generative pilgrimage engine on port 5000.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chaucer_canterbury.generator import ChaucerGenerativePipeline
from chaucer_canterbury.models import AuthorDefinition, MetricalForm, WorldState
from chaucer_canterbury.validators import run_holdout_counterfactual_suite

DEFAULT_DB_PATH = Path(
    os.environ.get(
        "CHAUCER_DB_PATH",
        "/home/user/workspace/chaucer-canterbury-app/data/studio.db",
    )
)
DEFAULT_STATIC_DIR = Path(
    os.environ.get(
        "CHAUCER_STATIC_DIR",
        "/home/user/workspace/chaucer-canterbury-app/dist/public",
    )
)


class CalibrateRequest(BaseModel):
    v2_topicalization_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    feminine_ending_rate: float | None = Field(default=None, ge=0.10, le=0.85)
    sentence_solaas_homeostasis: float | None = Field(default=None, ge=0.0, le=1.0)
    compilatio_digression_density: float | None = Field(default=None, ge=0.0, le=0.60)
    ironic_disclaimer_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    reset_to_empirical: bool = False


class GenerateTurnRequest(BaseModel):
    forced_speaker_id: str | None = None
    forced_source_id: str | None = None
    forced_form: str | None = None
    unit_count: int = Field(default=3, ge=1, le=5)
    seed: int = 1390


class ScanWorkbenchRequest(BaseModel):
    text: str
    rhyme_scheme: str = "SINGLE"  # "SINGLE" | "AABB" | "ABABBCC"


class StudioStateStore:
    """SQLite persistence backing AUTHOR_DEFINITION, WORLD_STATE, turns, and counterfactuals."""

    def __init__(self, db_path: Path, pipeline: ChaucerGenerativePipeline) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pipeline = pipeline
        self._init_schema()
        self._ensure_seeded()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS author_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS world_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS turns (
                    turn_id INTEGER PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS counterfactual_runs (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _ensure_seeded(self) -> None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload_json FROM author_config WHERE id = 1").fetchone()
            if row is not None:
                return

        author_def = self.pipeline.calibrator.calibrate()
        world = self.pipeline.env.initial_world_state()

        # Seed 3 rich pilgrimage turns: Knight (lot) -> Miller (quiting interrupt) -> Silent Yeoman
        art1, world = self.pipeline.generate_turn(world, author_def=author_def, unit_count=3, seed=1387)
        art2, world = self.pipeline.generate_turn(world, author_def=author_def, unit_count=3, seed=1388)
        art3, world = self.pipeline.generate_turn(
            world, author_def=author_def, forced_speaker_id="yeoman", unit_count=3, seed=1389
        )
        cf_report = run_holdout_counterfactual_suite(self.pipeline)

        now = self._now()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO author_config (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (author_def.model_dump_json(), now),
            )
            conn.execute(
                "INSERT OR REPLACE INTO world_state (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (world.model_dump_json(), now),
            )
            for art in (art1, art2, art3):
                conn.execute(
                    "INSERT OR REPLACE INTO turns (turn_id, payload_json, created_at) VALUES (?, ?, ?)",
                    (art.turn_id, art.model_dump_json(), now),
                )
            conn.execute(
                "INSERT OR REPLACE INTO counterfactual_runs (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (cf_report.model_dump_json(), now),
            )

    def get_author_definition(self) -> AuthorDefinition:
        with self._connect() as conn:
            row = conn.execute("SELECT payload_json FROM author_config WHERE id = 1").fetchone()
            return AuthorDefinition.model_validate_json(row["payload_json"])

    def save_author_definition(self, author_def: AuthorDefinition) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO author_config (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (author_def.model_dump_json(), self._now()),
            )

    def get_world_state(self) -> WorldState:
        with self._connect() as conn:
            row = conn.execute("SELECT payload_json FROM world_state WHERE id = 1").fetchone()
            return WorldState.model_validate_json(row["payload_json"])

    def save_world_and_turn(self, world: WorldState, artifact_json: str, turn_id: int) -> None:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO world_state (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (world.model_dump_json(), now),
            )
            conn.execute(
                "INSERT OR REPLACE INTO turns (turn_id, payload_json, created_at) VALUES (?, ?, ?)",
                (turn_id, artifact_json, now),
            )

    def reset_pilgrimage(self, seed_opening: bool = True) -> dict[str, Any]:
        author_def = self.get_author_definition()
        world = self.pipeline.env.initial_world_state()
        turns_out = []
        with self._connect() as conn:
            conn.execute("DELETE FROM turns")
            if seed_opening:
                art1, world = self.pipeline.generate_turn(
                    world, author_def=author_def, unit_count=3, seed=1390
                )
                conn.execute(
                    "INSERT INTO turns (turn_id, payload_json, created_at) VALUES (?, ?, ?)",
                    (art1.turn_id, art1.model_dump_json(), self._now()),
                )
                turns_out.append(art1.model_dump())
            conn.execute(
                "INSERT OR REPLACE INTO world_state (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (world.model_dump_json(), self._now()),
            )
        return {"world": world.model_dump(), "turns": turns_out}

    def list_turns(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM turns ORDER BY turn_id ASC"
            ).fetchall()
            return [json.loads(r["payload_json"]) for r in rows]

    def get_counterfactuals(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json, updated_at FROM counterfactual_runs WHERE id = 1"
            ).fetchone()
            data = json.loads(row["payload_json"])
            data["updated_at"] = row["updated_at"]
            return data

    def save_counterfactuals(self, payload_json: str) -> dict[str, Any]:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO counterfactual_runs (id, payload_json, updated_at) VALUES (1, ?, ?)",
                (payload_json, now),
            )
        data = json.loads(payload_json)
        data["updated_at"] = now
        return data


pipeline_singleton = ChaucerGenerativePipeline()
store_singleton = StudioStateStore(DEFAULT_DB_PATH, pipeline_singleton)

app = FastAPI(
    title="Chaucer-Canterbury Generative Philology Studio API",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "lexicon_entries": len(pipeline_singleton.validator.transcriber.lexicon),
        "pilgrims_loaded": len(pipeline_singleton.env.pilgrims),
        "pre_1400_sources": len(pipeline_singleton.source_graphs),
    }


@app.get("/api/overview")
def get_studio_overview() -> dict[str, Any]:
    """Return full studio hydration payload: AUTHOR_DEFINITION, WORLD_STATE, pilgrims, S5, turns, counterfactuals."""
    world = store_singleton.get_world_state()
    author_def = store_singleton.get_author_definition()
    speaker_scores = pipeline_singleton.env.score_next_speakers(world)
    turns = store_singleton.list_turns()
    cf = store_singleton.get_counterfactuals()

    return {
        "author_definition": author_def.model_dump(),
        "world_state": world.model_dump(),
        "route_segments": pipeline_singleton.env.route_segments,
        "speaker_probabilities": [s.model_dump() for s in speaker_scores],
        "pilgrims": [p.model_dump() for p in pipeline_singleton.env.pilgrims.values()],
        "source_graphs": pipeline_singleton.source_graphs,
        "turns": turns,
        "counterfactual_report": cf,
        "lexicon_stats": {
            "med_entries": len(pipeline_singleton.validator.transcriber.lexicon),
            "epistemic_horizon_year": 1400,
            "s2_works": author_def.calibrated_works,
            "s2_calibrated_lines": author_def.total_calibrated_lines,
            "s2_calibrated_tokens": author_def.total_calibrated_tokens,
        },
    }


@app.post("/api/calibrate")
def update_calibration(req: CalibrateRequest) -> dict[str, Any]:
    if req.reset_to_empirical:
        calibrated = pipeline_singleton.calibrator.calibrate()
    else:
        overrides = {
            k: v
            for k, v in req.model_dump().items()
            if k != "reset_to_empirical" and v is not None
        }
        current = store_singleton.get_author_definition()
        calibrated = current.model_copy(update=overrides)
    store_singleton.save_author_definition(calibrated)
    return {"author_definition": calibrated.model_dump()}


@app.post("/api/generate-turn")
def generate_pilgrimage_turn(req: GenerateTurnRequest) -> dict[str, Any]:
    world = store_singleton.get_world_state()
    author_def = store_singleton.get_author_definition()

    if req.forced_speaker_id and req.forced_speaker_id not in pipeline_singleton.env.pilgrims:
        raise HTTPException(status_code=400, detail=f"Unknown pilgrim ID: {req.forced_speaker_id}")

    form_enum = MetricalForm(req.forced_form) if req.forced_form else None
    artifact, next_world = pipeline_singleton.generate_turn(
        world,
        author_def=author_def,
        forced_speaker_id=req.forced_speaker_id or None,
        forced_source_id=req.forced_source_id or None,
        forced_form=form_enum,
        unit_count=req.unit_count,
        seed=req.seed + world.turn_index,
    )
    store_singleton.save_world_and_turn(next_world, artifact.model_dump_json(), artifact.turn_id)
    next_scores = pipeline_singleton.env.score_next_speakers(next_world)
    return {
        "turn": artifact.model_dump(),
        "world_state": next_world.model_dump(),
        "speaker_probabilities": [s.model_dump() for s in next_scores],
    }


@app.post("/api/world/reset")
def reset_world() -> dict[str, Any]:
    res = store_singleton.reset_pilgrimage(seed_opening=True)
    world_obj = WorldState.model_validate(res["world"])
    scores = pipeline_singleton.env.score_next_speakers(world_obj)
    return {
        "world_state": res["world"],
        "turns": res["turns"],
        "speaker_probabilities": [s.model_dump() for s in scores],
    }


@app.post("/api/scan")
def scan_workbench(req: ScanWorkbenchRequest) -> dict[str, Any]:
    raw_lines = [ln.strip() for ln in req.text.splitlines() if ln.strip()]
    if not raw_lines:
        raise HTTPException(status_code=400, detail="Provide at least one Middle English line.")

    validator = pipeline_singleton.validator
    transcriber = validator.transcriber

    line_results = []
    word_profiles = []
    for idx, ln in enumerate(raw_lines, start=1):
        scan = validator.scan_line(ln, line_number=idx)
        line_results.append(scan.model_dump())
        toks = transcriber.tokenize_line(ln)
        word_profiles.append([transcriber.profile_word(w, p).model_dump() for w, p in toks])

    stanza_audit = None
    scheme = req.rhyme_scheme.upper()
    if scheme == "AABB" and len(raw_lines) >= 2 and len(raw_lines) % 2 == 0:
        dynamic_scheme = "".join(chr(65 + (i // 2) % 26) for i in range(len(raw_lines)))
        stanza_audit = validator.audit_stanza(
            [(i + 1, ln) for i, ln in enumerate(raw_lines)],
            dynamic_scheme,
            "WORKBENCH_COUPLET",
        ).model_dump()
    elif scheme == "ABABBCC" and len(raw_lines) == 7:
        stanza_audit = validator.audit_stanza(
            [(i + 1, ln) for i, ln in enumerate(raw_lines)],
            "ABABBCC",
            "WORKBENCH_RHYME_ROYAL",
        ).model_dump()

    return {
        "lines": line_results,
        "word_profiles": word_profiles,
        "stanza_audit": stanza_audit,
    }


@app.get("/api/corpus-audit/{work_id}")
def run_s2_corpus_audit(work_id: str) -> dict[str, Any]:
    data_dir = pipeline_singleton.calibrator.data_dir / "s2_calibration"
    mapping = {
        "troilus": data_dir / "troilus_book1_proem.json",
        "lgw": data_dir / "legend_good_women_prol.json",
    }
    if work_id not in mapping:
        raise HTTPException(status_code=404, detail="Supported S2 verse works: 'troilus', 'lgw'.")
    report = pipeline_singleton.validator.audit_corpus_file(mapping[work_id])
    return report.model_dump()


@app.post("/api/counterfactuals/run")
def execute_counterfactual_suite() -> dict[str, Any]:
    report = run_holdout_counterfactual_suite(pipeline_singleton)
    return store_singleton.save_counterfactuals(report.model_dump_json())


if DEFAULT_STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DEFAULT_STATIC_DIR), html=True), name="static")


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
