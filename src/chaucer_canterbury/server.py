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

from chaucer_canterbury.blind_scansion import BlindScansionEvaluator
from chaucer_canterbury.generator import ChaucerGenerativePipeline
from chaucer_canterbury.models import AuthorDefinition, MetricalForm, WorldState
from chaucer_canterbury.validators import run_holdout_counterfactual_suite

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports"

DEFAULT_DB_PATH = Path(
    os.environ.get(
        "CHAUCER_DB_PATH",
        str(REPO_ROOT / ".local" / "studio.db"),
    )
)
DEFAULT_STATIC_DIR = Path(
    os.environ.get(
        "CHAUCER_STATIC_DIR",
        os.environ.get(
            "CHAUCER_WEBAPP_DIST",
            str(REPO_ROOT / "webapp" / "dist" / "public"),
        ),
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
    rhyme_scheme: str = "SINGLE"  # "SINGLE" | "AABB" | "ABABBCC" | "AABCCB"


class RunBlindScansionRequest(BaseModel):
    target_set: str = "ALL"  # "ALL" | "H1" | "H2" | "H3" | "H4" | "N1"


def summarize_blind_scansion_payload(
    payload: dict[str, Any], include_verdicts: bool = False
) -> dict[str, Any]:
    """Build a compact or full representation of a BlindScansionReport payload."""
    if include_verdicts:
        return payload

    line_verdicts = payload.get("line_verdicts", [])
    n1_verdicts = payload.get("n1_verdicts", [])
    sample_failures = [
        v
        for v in line_verdicts
        if v.get("set_id") in {"H1", "H2", "H3"}
        and not v.get("contested", False)
        and not v.get("is_valid", True)
    ][:8]
    sample_contested = [
        v for v in line_verdicts if v.get("contested", False)
    ][:8]
    sample_corruptions = n1_verdicts[:8]

    final_e = payload.get("final_e_summary")
    if isinstance(final_e, dict):
        final_e_compact = {
            **final_e,
            "mismatches": final_e.get("mismatches", [])[:10],
        }
    else:
        final_e_compact = final_e

    compact = {
        k: v
        for k, v in payload.items()
        if k not in {"line_verdicts", "n1_verdicts", "final_e_summary"}
    }
    compact["final_e_summary"] = final_e_compact
    compact["sample_failures"] = sample_failures
    compact["sample_contested"] = sample_contested
    compact["sample_corruptions"] = sample_corruptions
    return compact


class StudioStateStore:
    """SQLite persistence backing AUTHOR_DEFINITION, WORLD_STATE, turns, counterfactuals, and blind scansion."""

    def __init__(
        self,
        db_path: Path,
        pipeline: ChaucerGenerativePipeline,
        reports_dir: Path = REPORTS_DIR,
    ) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pipeline = pipeline
        self.reports_dir = reports_dir
        self._init_schema()
        self._ensure_seeded()
        self._ensure_blind_scansion_seeded()

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
                CREATE TABLE IF NOT EXISTS blind_scansion_runs (
                    run_key TEXT PRIMARY KEY,
                    engine_version TEXT NOT NULL,
                    target_set TEXT NOT NULL,
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

    def _ensure_blind_scansion_seeded(self) -> None:
        """Seed untouched v0.1-baseline and v0.2 Validation Plan 02 reports into SQLite."""
        now = self._now()
        baseline_file = self.reports_dir / "validation-02-baseline.json"
        v02_file = self.reports_dir / "validation-02-v0.2.json"

        with self._connect() as conn:
            existing_keys = {
                r["run_key"]
                for r in conn.execute("SELECT run_key FROM blind_scansion_runs").fetchall()
            }
            if "v0.1-baseline:ALL" not in existing_keys and baseline_file.exists():
                raw = baseline_file.read_text(encoding="utf-8")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO blind_scansion_runs
                    (run_key, engine_version, target_set, payload_json, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("v0.1-baseline:ALL", "v0.1-baseline", "ALL", raw, now),
                )
            if "v0.2:ALL" not in existing_keys:
                if v02_file.exists():
                    raw_v02 = v02_file.read_text(encoding="utf-8")
                else:
                    rep = BlindScansionEvaluator(
                        validator=self.pipeline.validator,
                        engine_version="v0.2",
                    ).run("ALL")
                    raw_v02 = rep.model_dump_json()
                conn.execute(
                    """
                    INSERT OR REPLACE INTO blind_scansion_runs
                    (run_key, engine_version, target_set, payload_json, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("v0.2:ALL", "v0.2", "ALL", raw_v02, now),
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

    def save_blind_scansion_run(
        self, engine_version: str, target_set: str, payload_json: str
    ) -> dict[str, Any]:
        now = self._now()
        run_key = f"{engine_version}:{target_set.upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO blind_scansion_runs
                (run_key, engine_version, target_set, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_key, engine_version, target_set.upper(), payload_json, now),
            )
        parsed = json.loads(payload_json)
        parsed["updated_at"] = now
        return parsed

    def get_blind_scansion_bundle(self, include_verdicts: bool = False) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_key, engine_version, target_set, payload_json, updated_at
                FROM blind_scansion_runs
                ORDER BY updated_at ASC
                """
            ).fetchall()

        by_key: dict[str, dict[str, Any]] = {}
        runs_meta: list[dict[str, Any]] = []
        for r in rows:
            parsed = json.loads(r["payload_json"])
            parsed["updated_at"] = r["updated_at"]
            summarized = summarize_blind_scansion_payload(parsed, include_verdicts=include_verdicts)
            by_key[r["run_key"]] = summarized
            runs_meta.append(
                {
                    "run_key": r["run_key"],
                    "engine_version": r["engine_version"],
                    "target_set": r["target_set"],
                    "updated_at": r["updated_at"],
                    "all_thresholds_passed": parsed.get("all_thresholds_passed", False),
                    "h1_h3_line_recall": parsed.get("h1_h3_line_recall", 0.0),
                    "h1_h3_rhyme_recall": parsed.get("h1_h3_rhyme_recall", 0.0),
                    "n1_overall_rejection_rate": parsed.get("n1_overall_rejection_rate", 0.0),
                }
            )

        return {
            "baseline": by_key.get("v0.1-baseline:ALL"),
            "current": by_key.get("v0.2:ALL"),
            "runs": runs_meta,
        }


def create_app(
    db_path: Path | None = None,
    static_dir: Path | None = None,
    reports_dir: Path = REPORTS_DIR,
) -> FastAPI:
    """Create a configured FastAPI application instance."""
    resolved_db = db_path or DEFAULT_DB_PATH
    resolved_static = static_dir or DEFAULT_STATIC_DIR

    pipeline = ChaucerGenerativePipeline()
    store = StudioStateStore(resolved_db, pipeline, reports_dir=reports_dir)

    fastapi_app = FastAPI(
        title="Chaucer-Canterbury Generative Philology Studio API",
        version="0.2.0",
    )
    fastapi_app.state.pipeline = pipeline
    fastapi_app.state.store = store

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @fastapi_app.get("/api/health")
    def health_check() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "0.2.0",
            "lexicon_entries": len(pipeline.validator.transcriber.lexicon),
            "pilgrims_loaded": len(pipeline.env.pilgrims),
            "pre_1400_sources": len(pipeline.source_graphs),
        }

    @fastapi_app.get("/api/overview")
    def get_studio_overview() -> dict[str, Any]:
        """Return full studio hydration payload including Validation Plan 02 blind-scansion summary."""
        world = store.get_world_state()
        author_def = store.get_author_definition()
        speaker_scores = pipeline.env.score_next_speakers(world)
        turns = store.list_turns()
        cf = store.get_counterfactuals()
        blind_bundle = store.get_blind_scansion_bundle(include_verdicts=False)

        return {
            "author_definition": author_def.model_dump(),
            "world_state": world.model_dump(),
            "route_segments": pipeline.env.route_segments,
            "speaker_probabilities": [s.model_dump() for s in speaker_scores],
            "pilgrims": [p.model_dump() for p in pipeline.env.pilgrims.values()],
            "source_graphs": pipeline.source_graphs,
            "turns": turns,
            "counterfactual_report": cf,
            "blind_scansion": blind_bundle,
            "lexicon_stats": {
                "med_entries": len(pipeline.validator.transcriber.lexicon),
                "epistemic_horizon_year": 1400,
                "s2_works": author_def.calibrated_works,
                "s2_calibrated_lines": author_def.total_calibrated_lines,
                "s2_calibrated_tokens": author_def.total_calibrated_tokens,
            },
        }

    @fastapi_app.post("/api/calibrate")
    def update_calibration(req: CalibrateRequest) -> dict[str, Any]:
        if req.reset_to_empirical:
            calibrated = pipeline.calibrator.calibrate()
        else:
            overrides = {
                k: v
                for k, v in req.model_dump().items()
                for _ in (0,)
                if k != "reset_to_empirical" and v is not None
            }
            current = store.get_author_definition()
            calibrated = current.model_copy(update=overrides)
        store.save_author_definition(calibrated)
        return {"author_definition": calibrated.model_dump()}

    @fastapi_app.post("/api/generate-turn")
    def generate_pilgrimage_turn(req: GenerateTurnRequest) -> dict[str, Any]:
        world = store.get_world_state()
        author_def = store.get_author_definition()

        if req.forced_speaker_id and req.forced_speaker_id not in pipeline.env.pilgrims:
            raise HTTPException(status_code=400, detail=f"Unknown pilgrim ID: {req.forced_speaker_id}")

        form_enum = MetricalForm(req.forced_form) if req.forced_form else None
        artifact, next_world = pipeline.generate_turn(
            world,
            author_def=author_def,
            forced_speaker_id=req.forced_speaker_id or None,
            forced_source_id=req.forced_source_id or None,
            forced_form=form_enum,
            unit_count=req.unit_count,
            seed=req.seed + world.turn_index,
        )
        store.save_world_and_turn(next_world, artifact.model_dump_json(), artifact.turn_id)
        next_scores = pipeline.env.score_next_speakers(next_world)
        return {
            "turn": artifact.model_dump(),
            "world_state": next_world.model_dump(),
            "speaker_probabilities": [s.model_dump() for s in next_scores],
        }

    @fastapi_app.post("/api/world/reset")
    def reset_world() -> dict[str, Any]:
        res = store.reset_pilgrimage(seed_opening=True)
        world_obj = WorldState.model_validate(res["world"])
        scores = pipeline.env.score_next_speakers(world_obj)
        return {
            "world_state": res["world"],
            "turns": res["turns"],
            "speaker_probabilities": [s.model_dump() for s in scores],
        }

    @fastapi_app.post("/api/scan")
    def scan_workbench(req: ScanWorkbenchRequest) -> dict[str, Any]:
        raw_lines = [ln.strip() for ln in req.text.splitlines() if ln.strip()]
        if not raw_lines:
            raise HTTPException(status_code=400, detail="Provide at least one Middle English line.")

        validator = pipeline.validator
        transcriber = validator.transcriber

        scheme = req.rhyme_scheme.upper()
        beat_targets = (
            [4, 4, 3, 4, 4, 3]
            if scheme == "AABCCB" and len(raw_lines) == 6
            else [5] * len(raw_lines)
        )

        line_results = []
        word_profiles = []
        for idx, (ln, bt) in enumerate(zip(raw_lines, beat_targets), start=1):
            scan = validator.scan_line(ln, line_number=idx, target_beats=bt)
            line_results.append(scan.model_dump())
            toks = transcriber.tokenize_line(ln)
            word_profiles.append([transcriber.profile_word(w, p).model_dump() for w, p in toks])

        stanza_audit = None
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
        elif scheme == "AABCCB" and len(raw_lines) == 6:
            stanza_audit = validator.audit_stanza(
                [(i + 1, ln) for i, ln in enumerate(raw_lines)],
                "AABCCB",
                "WORKBENCH_TAIL_RHYME",
                beat_targets=[4, 4, 3, 4, 4, 3],
            ).model_dump()

        return {
            "lines": line_results,
            "word_profiles": word_profiles,
            "stanza_audit": stanza_audit,
        }

    @fastapi_app.get("/api/corpus-audit/{work_id}")
    def run_s2_corpus_audit(work_id: str) -> dict[str, Any]:
        data_dir = pipeline.calibrator.data_dir / "s2_calibration"
        mapping = {
            "troilus": data_dir / "troilus_book1_proem.json",
            "lgw": data_dir / "legend_good_women_prol.json",
        }
        if work_id not in mapping:
            raise HTTPException(status_code=404, detail="Supported S2 verse works: 'troilus', 'lgw'.")
        report = pipeline.validator.audit_corpus_file(mapping[work_id])
        return report.model_dump()

    @fastapi_app.post("/api/counterfactuals/run")
    def execute_counterfactual_suite() -> dict[str, Any]:
        report = run_holdout_counterfactual_suite(pipeline)
        return store.save_counterfactuals(report.model_dump_json())

    @fastapi_app.get("/api/validation/blind-scansion")
    def get_blind_scansion_validation(include_verdicts: bool = False) -> dict[str, Any]:
        return store.get_blind_scansion_bundle(include_verdicts=include_verdicts)

    @fastapi_app.post("/api/validation/blind-scansion/run")
    def execute_blind_scansion_validation(
        req: RunBlindScansionRequest | None = None,
    ) -> dict[str, Any]:
        target = (req.target_set if req else "ALL").upper()
        if target not in {"ALL", "H1", "H2", "H3", "H4", "N1"}:
            raise HTTPException(
                status_code=400,
                detail="target_set must be one of ALL, H1, H2, H3, H4, N1.",
            )
        evaluator = BlindScansionEvaluator(
            validator=pipeline.validator,
            engine_version="v0.2",
        )
        report = evaluator.run(target)
        saved = store.save_blind_scansion_run("v0.2", target, report.model_dump_json())
        bundle = store.get_blind_scansion_bundle(include_verdicts=False)
        bundle["latest_run"] = summarize_blind_scansion_payload(saved, include_verdicts=False)
        return bundle

    if resolved_static.exists():
        fastapi_app.mount(
            "/", StaticFiles(directory=str(resolved_static), html=True), name="static"
        )

    return fastapi_app


app = create_app()


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
