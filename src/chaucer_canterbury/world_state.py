"""Phase 3: Pilgrimage environment WORLD_STATE, 30 PILGRIM_DEFINITIONs, and quiting graph."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from chaucer_canterbury.models import (
    PilgrimDefinition,
    QuitingEdge,
    SpeakerCandidateScore,
    WorldState,
)

DEFAULT_PILGRIMS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "pilgrims" / "general_prologue_30.json"
)


class PilgrimageEnvironment:
    """Manages W_t, Harry Bailly turn scheduling, and the directed quiting graph G_t."""

    def __init__(self, pilgrims_path: Path | None = None) -> None:
        self.path = pilgrims_path or DEFAULT_PILGRIMS_PATH
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.route_segments: list[dict[str, Any]] = raw["route_segments"]
        self.pilgrims: dict[str, PilgrimDefinition] = {
            p["id"]: PilgrimDefinition.model_validate(p) for p in raw["pilgrims"]
        }

    def initial_world_state(self) -> WorldState:
        """Initialize W_0 at the Tabard Inn in Southwark with baseline social frictions."""
        seed_edges = [
            QuitingEdge(
                source_pilgrim="miller",
                target_pilgrim="knight",
                weight=0.58,
                reason="Latent churlish impulse to subvert noble hierarchy",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="reeve",
                target_pilgrim="miller",
                weight=0.64,
                reason="Manorial bailiff and carpenter suspicion of toll-miller",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="friar",
                target_pilgrim="summoner",
                weight=0.72,
                reason="Mendicant vs consistory apparitor jurisdiction rivalry",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="summoner",
                target_pilgrim="friar",
                weight=0.74,
                reason="Retaliatory animus against mendicant limitours",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="clerk",
                target_pilgrim="wife_of_bath",
                weight=0.52,
                reason="Oxford clerk vs experiential anti-clerical glossing",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="plowman",
                target_pilgrim="summoner",
                weight=0.60,
                reason="Honest tither defense of poor parishioners",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="carpenter",
                target_pilgrim="miller",
                weight=0.62,
                reason="London master joiner defense of craft honor",
                turn_updated=0,
            ),
            QuitingEdge(
                source_pilgrim="yeoman",
                target_pilgrim="reeve",
                weight=0.55,
                reason="Forester scrutiny of manorial poaching and tallies",
                turn_updated=0,
            ),
        ]
        stage0 = self.route_segments[0]
        return WorldState(
            turn_index=0,
            route_stage_index=0,
            route_stage_name=stage0["name"],
            mile_marker=stage0["mile"],
            time_of_day=stage0["time_of_day"],
            quiting_edges=seed_edges,
        )

    def score_next_speakers(
        self,
        state: WorldState,
        alpha: float = 1.65,
        beta: float = 2.40,
        gamma: float = 2.10,
        interrupt_threshold: float = 0.72,
    ) -> list[SpeakerCandidateScore]:
        """Compute P(p_t | W_{t-1}) across all 29 tale-telling pilgrims (excluding Host arbiter)."""
        raw_scores: list[tuple[PilgrimDefinition, float, float, float, float, bool]] = []

        for pid, p in self.pilgrims.items():
            if pid == "harry_bailly":
                continue

            # 1. HostCall(p_t, W_{t-1}): Turn 0 favors Knight by lot/degree; later balances sentence/solaas
            est = p.estate_vector
            if state.turn_index == 0:
                host_call = 1.8 * est["bellatores"] + 0.5 * est["oratores"]
            else:
                need_solaas = state.rolling_sentence_level - state.rolling_solaas_level
                if need_solaas > 0.12:
                    host_call = 0.85 * (est["laboratores"] + est["urban_guild"]) + 0.35 * p.pragmatic_posture["irony_capacity"]
                elif need_solaas < -0.12:
                    host_call = 0.90 * (est["oratores"] + est["bellatores"])
                else:
                    host_call = 0.55 * (est["urban_guild"] + est["bellatores"] + est["oratores"])

                # Boost silent General Prologue pilgrims when prior speakers have spoken
                if p.manuscript_status == "silent_uncompleted" and state.tales_told_by_pilgrim.get(pid, 0) == 0:
                    host_call += 0.32

            # 2. Grievance(p_t, p_q) * Disinhibition(p_t)
            relevant_edges = [
                e.weight * (1.35 if e.target_pilgrim == state.last_speaker_id else 0.75)
                for e in state.quiting_edges
                if e.source_pilgrim == pid
            ]
            max_grievance = max(relevant_edges, default=0.0)
            disinhib = p.pragmatic_posture.get("disinhibition", 0.3)
            grievance_drive = min(1.25, max_grievance * (0.45 + 0.75 * disinhib))
            would_interrupt = (
                state.last_speaker_id is not None
                and max_grievance * disinhib >= interrupt_threshold
                and pid != state.last_speaker_id
            )

            # 3. Fatigue(p_t): strongly penalize immediate repeat or multiple turns before peers speak
            told = state.tales_told_by_pilgrim.get(pid, 0)
            fatigue = told * 0.95 + (2.5 if pid == state.last_speaker_id else 0.0)

            logit = alpha * host_call + beta * grievance_drive - gamma * fatigue
            raw_scores.append((p, logit, host_call, grievance_drive, fatigue, would_interrupt))

        max_logit = max(x[1] for x in raw_scores)
        exps = [math.exp(x[1] - max_logit) for x in raw_scores]
        denom = sum(exps) or 1.0

        results: list[SpeakerCandidateScore] = []
        for (p, _, hc, gd, fat, intr), ex in zip(raw_scores, exps):
            results.append(
                SpeakerCandidateScore(
                    pilgrim_id=p.id,
                    pilgrim_name=p.name,
                    probability=round(ex / denom, 4),
                    host_call_score=round(hc, 3),
                    grievance_drive=round(gd, 3),
                    fatigue_penalty=round(fat, 3),
                    would_interrupt=intr,
                )
            )
        results.sort(key=lambda r: r.probability, reverse=True)
        return results

    def select_speaker(
        self,
        state: WorldState,
        forced_speaker_id: str | None = None,
        rng: random.Random | None = None,
    ) -> tuple[PilgrimDefinition, str, str | None, list[SpeakerCandidateScore]]:
        """Select next pilgrim speaker and determine selection mode and quiting target."""
        scores = self.score_next_speakers(state)
        if forced_speaker_id and forced_speaker_id in self.pilgrims:
            chosen = self.pilgrims[forced_speaker_id]
            target = self._top_grievance_target(chosen.id, state)
            return chosen, "researcher_override", target, scores

        # Check if top interrupter overrides Harry Bailly
        interrupters = [s for s in scores if s.would_interrupt]
        if interrupters:
            top_int = interrupters[0]
            chosen = self.pilgrims[top_int.pilgrim_id]
            target = self._top_grievance_target(chosen.id, state)
            return chosen, "quiting_interruption", target, scores

        if rng is None:
            chosen_id = scores[0].pilgrim_id
        else:
            top_pool = scores[:4]
            weights = [s.probability for s in top_pool]
            chosen_id = rng.choices([s.pilgrim_id for s in top_pool], weights=weights, k=1)[0]

        chosen = self.pilgrims[chosen_id]
        target = self._top_grievance_target(chosen.id, state)
        mode = "quiting_interruption" if any(s.pilgrim_id == chosen_id and s.would_interrupt for s in scores) else "host_call"
        return chosen, mode, target, scores

    @staticmethod
    def _top_grievance_target(speaker_id: str, state: WorldState) -> str | None:
        edges = [e for e in state.quiting_edges if e.source_pilgrim == speaker_id and e.weight >= 0.45]
        if not edges:
            return state.last_speaker_id
        edges.sort(
            key=lambda e: e.weight + (0.25 if e.target_pilgrim == state.last_speaker_id else 0.0),
            reverse=True,
        )
        return edges[0].target_pilgrim

    def advance_world_state(
        self,
        state: WorldState,
        speaker: PilgrimDefinition,
        source_id: str,
        genre: str,
        sentence_score: float,
        solaas_score: float,
        provoked_pilgrims: list[str],
    ) -> WorldState:
        """Advance road itinerary, update sentence/solaas homeostasis, and update quiting matrix."""
        next_turn = state.turn_index + 1
        stage_idx = min(len(self.route_segments) - 1, next_turn // 2)
        seg = self.route_segments[stage_idx]

        told_map = dict(state.tales_told_by_pilgrim)
        told_map[speaker.id] = told_map.get(speaker.id, 0) + 1

        edge_map: dict[tuple[str, str], QuitingEdge] = {
            (e.source_pilgrim, e.target_pilgrim): e.model_copy() for e in state.quiting_edges
        }

        # Speaker discharges grievance toward previous target
        for (u, v), edge in list(edge_map.items()):
            if u == speaker.id:
                edge.weight = round(max(0.15, edge.weight * 0.45), 3)

        # Provoked antagonists accumulate fresh quiting debt toward current speaker
        targets = set(provoked_pilgrims) | set(speaker.social_couplings.get("natural_antagonists", [])[:2])
        for ant_id in targets:
            if ant_id in self.pilgrims and ant_id != speaker.id and ant_id != "harry_bailly":
                key = (ant_id, speaker.id)
                prev_w = edge_map[key].weight if key in edge_map else 0.35
                new_w = round(min(0.99, prev_w + 0.38), 3)
                edge_map[key] = QuitingEdge(
                    source_pilgrim=ant_id,
                    target_pilgrim=speaker.id,
                    weight=new_w,
                    reason=f"Provoked by {speaker.name}'s {genre.replace('_', ' ')}",
                    turn_updated=next_turn,
                )

        new_sentence = round(0.55 * state.rolling_sentence_level + 0.45 * sentence_score, 3)
        new_solaas = round(0.55 * state.rolling_solaas_level + 0.45 * solaas_score, 3)
        host_patience = round(max(0.35, min(0.98, 0.85 - 0.25 * abs(new_sentence - new_solaas))), 3)

        used_sources = list(state.used_source_ids)
        if source_id not in used_sources:
            used_sources.append(source_id)

        used_genres = list(state.used_genres)
        used_genres.append(genre)

        sorted_edges = sorted(edge_map.values(), key=lambda e: e.weight, reverse=True)
        return WorldState(
            turn_index=next_turn,
            route_stage_index=stage_idx,
            route_stage_name=seg["name"],
            mile_marker=seg["mile"],
            time_of_day=seg["time_of_day"],
            epistemic_horizon_year=1400,
            host_patience=host_patience,
            rolling_sentence_level=new_sentence,
            rolling_solaas_level=new_solaas,
            last_speaker_id=speaker.id,
            last_genre=genre,
            tales_told_by_pilgrim=told_map,
            used_source_ids=used_sources,
            used_genres=used_genres,
            quiting_edges=sorted_edges[:18],
        )
