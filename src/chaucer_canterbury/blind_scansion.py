"""Validation Plan 02: Blind scansion, rhyme, and corruption evaluation on held-out Chaucer verse."""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path
from typing import Any

from chaucer_canterbury.lexicon import normalize_orthography
from chaucer_canterbury.models import (
    BlindScansionReport,
    BlindScansionThresholdCheck,
    CorruptionItemVerdict,
    CorruptionTypeSummary,
    FinalEAgreementSummary,
    FinalEClass,
    HoldoutLineVerdict,
    HoldoutRhymeVerdict,
    HoldoutSetSummary,
    LineScansionResult,
    WordClass,
    WordProfile,
)
from chaucer_canterbury.scansion import ProsodicValidator

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_HOLDOUT_DIR = DEFAULT_DATA_DIR / "s1_witnesses" / "blind_scansion"

POSITIVE_SET_FILES: dict[str, str] = {
    "H1": "h1_general_prologue_1_200.json",
    "H2": "h2_clerks_tale_stanzas_1_20.json",
    "H3": "h3_sir_thopas_1_60.json",
    "H4": "h4_general_prologue_201_400.json",
}

FAILURE_BUCKETS = ("lexicon_gap", "final_e_rule", "stress_or_lattice", "rhyme_phonology")


def verify_holdout_manifest(holdout_dir: Path | None = None) -> dict[str, Any]:
    """Verify SHA-256 manifest integrity and EVALUATION_ONLY isolation flags."""
    target_dir = holdout_dir or DEFAULT_HOLDOUT_DIR
    manifest_path = target_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing blind-scansion manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("holdout_flag") != "EVALUATION_ONLY":
        raise ValueError("Manifest missing holdout_flag='EVALUATION_ONLY'")

    for filename, meta in manifest.get("files", {}).items():
        fpath = target_dir / filename
        if not fpath.exists():
            raise FileNotFoundError(f"Missing holdout file declared in manifest: {fpath}")
        raw = fpath.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != meta["sha256"]:
            raise ValueError(
                f"SHA-256 mismatch for {filename}: expected {meta['sha256']}, got {digest}"
            )
        if len(raw) != int(meta["bytes"]):
            raise ValueError(
                f"Byte size mismatch for {filename}: expected {meta['bytes']}, got {len(raw)}"
            )
        doc = json.loads(raw.decode("utf-8"))
        if doc.get("metadata", {}).get("holdout_flag") != "EVALUATION_ONLY":
            raise ValueError(f"{filename} missing metadata.holdout_flag='EVALUATION_ONLY'")

    return manifest


class BlindScansionEvaluator:
    """Evaluates ProsodicValidator on frozen H1-H4, N1, and 70-line reference annotations."""

    def __init__(
        self,
        data_dir: Path | None = None,
        holdout_dir: Path | None = None,
        validator: ProsodicValidator | None = None,
        engine_version: str = "v0.1-baseline",
    ) -> None:
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.holdout_dir = holdout_dir or (self.data_dir / "s1_witnesses" / "blind_scansion")
        self.validator = validator or ProsodicValidator()
        self.engine_version = engine_version
        self._supports_beat_targets = (
            "beat_targets" in inspect.signature(self.validator.audit_stanza).parameters
        )
        self._supports_line_beats = (
            "target_beats" in inspect.signature(self.validator.scan_line).parameters
        )

    def run(self, selected_set: str = "ALL") -> BlindScansionReport:
        """Execute Validation Plan 02 on a single holdout set or the full suite (`ALL`)."""
        verify_holdout_manifest(self.holdout_dir)
        norm_set = selected_set.upper()

        if norm_set == "ALL":
            pos_sets = ["H1", "H2", "H3", "H4"]
            run_n1 = True
            run_ref = True
        elif norm_set in POSITIVE_SET_FILES:
            pos_sets = [norm_set]
            run_n1 = False
            run_ref = norm_set in {"H1", "H2"}
        elif norm_set == "N1":
            pos_sets = []
            run_n1 = True
            run_ref = False
        elif norm_set == "REF70":
            pos_sets = []
            run_n1 = False
            run_ref = True
        else:
            raise ValueError(f"Unknown holdout set '{selected_set}'")

        set_summaries: list[HoldoutSetSummary] = []
        all_line_verdicts: list[HoldoutLineVerdict] = []
        all_rhyme_verdicts: list[HoldoutRhymeVerdict] = []
        h4_summary: HoldoutSetSummary | None = None

        for sid in pos_sets:
            summary, l_verdicts, r_verdicts = self.evaluate_positive_set(sid)
            if sid == "H4":
                h4_summary = summary
                if norm_set == "H4":
                    set_summaries.append(summary)
            else:
                set_summaries.append(summary)
            all_line_verdicts.extend(l_verdicts)
            all_rhyme_verdicts.extend(r_verdicts)

        # Aggregate H1-H3 metrics
        h1_h3_summaries = [s for s in set_summaries if s.set_id in {"H1", "H2", "H3"}]
        h1_h3_non_contested = sum(s.non_contested_lines for s in h1_h3_summaries)
        h1_h3_accepted = sum(s.accepted_lines for s in h1_h3_summaries)
        h1_h3_line_recall = (
            round(h1_h3_accepted / h1_h3_non_contested, 4) if h1_h3_non_contested else 0.0
        )

        h1_h3_rhyme_nc = sum(s.rhyme_groups_non_contested for s in h1_h3_summaries)
        h1_h3_rhyme_acc = sum(s.rhyme_groups_accepted for s in h1_h3_summaries)
        h1_h3_rhyme_recall = (
            round(h1_h3_rhyme_acc / h1_h3_rhyme_nc, 4) if h1_h3_rhyme_nc else 0.0
        )

        h1_h3_tok_total = sum(s.total_tokens for s in h1_h3_summaries)
        h1_h3_tok_in = sum(s.in_lexicon_tokens for s in h1_h3_summaries)
        h1_h3_lex_cov = (
            round(h1_h3_tok_in / h1_h3_tok_total, 4) if h1_h3_tok_total else 0.0
        )

        failure_totals = {b: 0 for b in FAILURE_BUCKETS}
        for s in h1_h3_summaries if h1_h3_summaries else set_summaries:
            for b, cnt in s.failure_counts.items():
                failure_totals[b] = failure_totals.get(b, 0) + cnt

        s2_recall = self.evaluate_s2_calibration_recall()
        h1_summary = next((s for s in set_summaries if s.set_id == "H1"), None)
        gen_gap_points = (
            round((s2_recall - h1_summary.line_recall) * 100.0, 2)
            if h1_summary is not None
            else 0.0
        )

        n1_total = 0
        n1_rejected = 0
        n1_rate = 0.0
        n1_min_type = 0.0
        n1_by_type: list[CorruptionTypeSummary] = []
        corruption_verdicts: list[CorruptionItemVerdict] = []
        if run_n1:
            n1_total, n1_rejected, n1_rate, n1_by_type, corruption_verdicts = (
                self.evaluate_n1_corruptions()
            )
            n1_min_type = min((t.rejection_rate for t in n1_by_type), default=0.0)

        final_e_summary: FinalEAgreementSummary | None = None
        if run_ref:
            filter_sets = None if norm_set in {"ALL", "REF70"} else {norm_set}
            final_e_summary = self.evaluate_final_e_annotations(filter_sets=filter_sets)

        threshold_checks = self._build_threshold_checks(
            norm_set=norm_set,
            set_summaries=set_summaries,
            h1_h3_line_recall=h1_h3_line_recall,
            h1_h3_rhyme_recall=h1_h3_rhyme_recall,
            h1_h3_lex_cov=h1_h3_lex_cov,
            gen_gap_points=gen_gap_points,
            h1_present=(h1_summary is not None),
            run_n1=run_n1,
            n1_rate=n1_rate,
            n1_min_type=n1_min_type,
            final_e_summary=final_e_summary,
            h4_summary=h4_summary,
        )
        gated_checks = [c for c in threshold_checks if c.passed is not None]
        all_passed = bool(gated_checks) and all(bool(c.passed) for c in gated_checks)

        evaluated_list = (
            ["H1", "H2", "H3", "N1", "REF70", "H4"]
            if norm_set == "ALL"
            else [norm_set]
        )

        return BlindScansionReport(
            engine_version=self.engine_version,
            manifest_verified=True,
            evaluated_sets=evaluated_list,
            h1_h3_non_contested_lines=h1_h3_non_contested,
            h1_h3_accepted_lines=h1_h3_accepted,
            h1_h3_line_recall=h1_h3_line_recall,
            h1_h3_rhyme_groups_non_contested=h1_h3_rhyme_nc,
            h1_h3_rhyme_groups_accepted=h1_h3_rhyme_acc,
            h1_h3_rhyme_recall=h1_h3_rhyme_recall,
            h1_h3_lexicon_coverage=h1_h3_lex_cov,
            s2_calibration_recall=s2_recall,
            generalization_gap_points=gen_gap_points,
            n1_total_items=n1_total,
            n1_rejected_items=n1_rejected,
            n1_overall_rejection_rate=n1_rate,
            n1_min_type_rejection_rate=n1_min_type,
            n1_by_type=n1_by_type,
            final_e_summary=final_e_summary,
            h4_untouched_summary=h4_summary,
            set_summaries=set_summaries,
            failure_taxonomy_totals=failure_totals,
            threshold_checks=threshold_checks,
            all_thresholds_passed=all_passed,
            line_verdicts=all_line_verdicts,
            rhyme_verdicts=all_rhyme_verdicts,
            corruption_verdicts=corruption_verdicts,
        )

    def evaluate_positive_set(
        self, set_id: str
    ) -> tuple[HoldoutSetSummary, list[HoldoutLineVerdict], list[HoldoutRhymeVerdict]]:
        """Evaluate one positive holdout set (H1, H2, H3, or H4)."""
        path = self.holdout_dir / POSITIVE_SET_FILES[set_id]
        doc = json.loads(path.read_text(encoding="utf-8"))
        meta = doc["metadata"]

        line_verdicts: list[HoldoutLineVerdict] = []
        rhyme_verdicts: list[HoldoutRhymeVerdict] = []
        failure_counts = {b: 0 for b in FAILURE_BUCKETS}

        total_lines = 0
        contested_lines = 0
        contested_accepted = 0
        non_contested_lines = 0
        accepted_lines = 0

        rhyme_total = 0
        rhyme_nc = 0
        rhyme_acc = 0

        total_tokens = 0
        in_lexicon_tokens = 0
        unique_types_set: set[str] = set()
        in_lexicon_types_set: set[str] = set()

        for st in doc["stanzas"]:
            st_id = st["stanza_id"]
            scheme = st["rhyme_scheme"]
            raw_lines = st["lines"]
            beat_targets: list[int] = st.get("beat_targets") or [5] * len(raw_lines)
            pairs = [(int(item["line_number"]), item["text"]) for item in raw_lines]

            if self._supports_beat_targets:
                st_res = self.validator.audit_stanza(
                    lines=pairs,
                    rhyme_scheme=scheme,
                    stanza_id=st_id,
                    beat_targets=beat_targets,
                )
            else:
                st_res = self.validator.audit_stanza(
                    lines=pairs,
                    rhyme_scheme=scheme,
                    stanza_id=st_id,
                )

            contested_by_ln: dict[int, bool] = {}
            for raw_item, exp_beats, res in zip(raw_lines, beat_targets, st_res.lines):
                is_contested = bool(raw_item.get("contested", False))
                contested_by_ln[int(raw_item["line_number"])] = is_contested
                total_lines += 1

                raw_toks = self.validator.transcriber.tokenize_line(raw_item["text"])
                oov_toks: list[str] = []
                profiles: list[WordProfile] = []
                for surf, punct in raw_toks:
                    prof = self.validator.transcriber.profile_word(surf, punct)
                    profiles.append(prof)
                    total_tokens += 1
                    unique_types_set.add(prof.normalized)
                    if self.validator.lexicon.lookup(surf) is not None:
                        in_lexicon_tokens += 1
                        in_lexicon_types_set.add(prof.normalized)
                    else:
                        oov_toks.append(surf)

                fail_cat: str | None = None
                fail_detail: str | None = None

                if is_contested:
                    contested_lines += 1
                    if res.is_valid:
                        contested_accepted += 1
                else:
                    non_contested_lines += 1
                    if res.is_valid:
                        accepted_lines += 1
                    else:
                        fail_cat, fail_detail = self._classify_line_failure(
                            res=res,
                            profiles=profiles,
                            oov_toks=oov_toks,
                            expected_beats=exp_beats,
                        )
                        failure_counts[fail_cat] += 1

                line_verdicts.append(
                    HoldoutLineVerdict(
                        set_id=set_id,
                        stanza_id=st_id,
                        ref=raw_item["ref"],
                        line_number=int(raw_item["line_number"]),
                        text=raw_item["text"],
                        expected_beats=exp_beats,
                        contested=is_contested,
                        contested_reason=raw_item.get("contested_reason"),
                        is_valid=res.is_valid,
                        metrical_pattern=res.metrical_pattern,
                        syllable_count=res.syllable_count,
                        beat_count=res.beat_count,
                        license_used=res.license_used.value if res.license_used else None,
                        total_cost=res.total_cost,
                        rhyme_key=res.rhyme_key,
                        elision_events=res.elision_events,
                        oov_tokens=oov_toks,
                        failure_category=fail_cat,
                        failure_detail=fail_detail,
                    )
                )

            valid_by_ln = {r.line_number: r.is_valid for r in st_res.lines}
            for ra in st_res.rhyme_audits:
                rhyme_total += 1
                has_contested = any(contested_by_ln.get(ln, False) for ln in ra.line_numbers)
                if not has_contested:
                    rhyme_nc += 1
                    if ra.is_valid:
                        rhyme_acc += 1
                    else:
                        # Count pure rhyme phonology failures when member lines scanned validly
                        if all(valid_by_ln.get(ln, False) for ln in ra.line_numbers):
                            failure_counts["rhyme_phonology"] += 1
                        elif any(k != "" for k in ra.rhyme_keys) and len(set(k for k in ra.rhyme_keys if k)) > 1:
                            failure_counts["rhyme_phonology"] += 1

                rhyme_verdicts.append(
                    HoldoutRhymeVerdict(
                        set_id=set_id,
                        stanza_id=st_id,
                        label=ra.label,
                        line_numbers=ra.line_numbers,
                        end_words=ra.end_words,
                        rhyme_keys=ra.rhyme_keys,
                        status=ra.status,
                        has_contested_line=has_contested,
                        is_valid=ra.is_valid,
                    )
                )

        line_recall = (
            round(accepted_lines / non_contested_lines, 4) if non_contested_lines else 0.0
        )
        rhyme_recall = round(rhyme_acc / rhyme_nc, 4) if rhyme_nc else 0.0
        lex_tok_cov = round(in_lexicon_tokens / total_tokens, 4) if total_tokens else 0.0
        lex_type_cov = (
            round(len(in_lexicon_types_set) / len(unique_types_set), 4)
            if unique_types_set
            else 0.0
        )

        summary = HoldoutSetSummary(
            set_id=set_id,
            title=doc["title"],
            metrical_form=meta["metrical_form"],
            total_lines=total_lines,
            contested_lines=contested_lines,
            contested_accepted=contested_accepted,
            non_contested_lines=non_contested_lines,
            accepted_lines=accepted_lines,
            line_recall=line_recall,
            rhyme_groups_total=rhyme_total,
            rhyme_groups_non_contested=rhyme_nc,
            rhyme_groups_accepted=rhyme_acc,
            rhyme_recall=rhyme_recall,
            total_tokens=total_tokens,
            in_lexicon_tokens=in_lexicon_tokens,
            lexicon_token_coverage=lex_tok_cov,
            unique_types=len(unique_types_set),
            in_lexicon_types=len(in_lexicon_types_set),
            lexicon_type_coverage=lex_type_cov,
            failure_counts=failure_counts,
        )
        return summary, line_verdicts, rhyme_verdicts

    def _classify_line_failure(
        self,
        res: LineScansionResult,
        profiles: list[WordProfile],
        oov_toks: list[str],
        expected_beats: int,
    ) -> tuple[str, str]:
        """Deterministically assign a failed line to one of the 4 Validation Plan 02 buckets."""
        if expected_beats in {3, 4} and not self._supports_beat_targets:
            return (
                "stress_or_lattice",
                f"Target form requires {expected_beats}-beat tail-rhyme template; v0.1 solver only defines 5-beat pentameter templates.",
            )

        lattice = self.validator.elision_resolver.resolve_line_lattice(profiles)
        if not lattice or any(not cands for cands in lattice):
            empty_toks = [
                p.surface for p, cands in zip(profiles, lattice) if not cands
            ]
            return (
                "final_e_rule",
                f"FinalEResolver produced zero realizations for token(s) {empty_toks} (line-final -e / quote-edge classification).",
            )

        min_sylls = sum(min(len(c.syllables) for c in cands) for cands in lattice)
        max_sylls = sum(max(len(c.syllables) for c in cands) for cands in lattice)

        target_sylls = (
            {9, 10, 11}
            if expected_beats == 5
            else ({7, 8, 9} if expected_beats == 4 else {5, 6, 7})
        )
        reachable = set(range(min_sylls, max_sylls + 1))

        # Check whether final -e or inflectional -e- syncope rules prevented reaching target syllable count
        if not (reachable & target_sylls):
            has_e_bearing = any(
                p.final_e_class in {FinalEClass.INFLECTIONAL, FinalEClass.ETYMOLOGICAL, FinalEClass.PETRIFIED_SILENT}
                or p.normalized.endswith(("ed", "es", "en", "eth", "er", "el", "e"))
                for p in profiles
            )
            if has_e_bearing:
                return (
                    "final_e_rule",
                    f"Lattice syllable span [{min_sylls}, {max_sylls}] misses target {sorted(target_sylls)} due to final -e / unstressed -e- realization.",
                )
            if oov_toks:
                return (
                    "lexicon_gap",
                    f"OOV syllabification on {oov_toks} produced syllable span [{min_sylls}, {max_sylls}].",
                )
            return (
                "stress_or_lattice",
                f"Lattice syllable span [{min_sylls}, {max_sylls}] outside licensed templates.",
            )

        # Syllable count is reachable, so failure is either OOV lexical stress/class or template/lattice alignment
        oov_polysyllables = [
            p.surface
            for p in profiles
            if p.med_id is None
            and p.word_class == WordClass.CONTENT
            and any(len(v.syllables) >= 2 for v in p.variants)
        ]
        if oov_polysyllables and not res.metrical_pattern:
            return (
                "lexicon_gap",
                f"OOV polysyllabic stress profile blocked template placement: {oov_polysyllables}.",
            )

        return (
            "stress_or_lattice",
            res.l4_notes[0]
            if res.l4_notes
            else f"Stress/template alignment rejected (syllable span [{min_sylls}, {max_sylls}]).",
        )

    def _fallback_word_rhyme_key(self, line_text: str) -> str:
        """Extract phonological rhyme key directly from a line's final word when line scansion fails."""
        toks = self.validator.transcriber.tokenize_line(line_text)
        if not toks:
            return ""
        last_word, last_punct = toks[-1]
        prof = self.validator.transcriber.profile_word(last_word, last_punct)
        sylls = prof.variants[0].syllables
        # Locate last stressed syllable (or last non-schwa syllable)
        beat_idx = len(sylls) - 1
        for i in range(len(sylls) - 1, -1, -1):
            if not sylls[i].is_final_schwa and (sylls[i].stress > 0 or i == 0):
                beat_idx = i
                break
        beat_ipa = sylls[beat_idx].ipa
        m = re.search(r"(aː|eː|ɛː|iː|oː|ɔː|uː|ɛi|ai|ɔi|au|ɔu|iu|[aɛiɔuə])", beat_ipa)
        nuc = beat_ipa[m.start() :] if m else beat_ipa
        tail = "".join(s.ipa for s in sylls[beat_idx + 1 :])
        raw_key = re.sub(r"([bcdfghklmnprstvz])\1", r"\1", nuc + tail)
        return raw_key

    def evaluate_n1_corruptions(
        self,
    ) -> tuple[int, int, float, list[CorruptionTypeSummary], list[CorruptionItemVerdict]]:
        """Evaluate precision/rejection across all 340 corrupted items in N1."""
        path = self.holdout_dir / "n1_corrupted_340.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        items = doc["items"]

        verdicts: list[CorruptionItemVerdict] = []
        by_type_counts: dict[str, dict[str, int]] = {}

        for item in items:
            ctype = item["corruption_type"]
            stats = by_type_counts.setdefault(
                ctype, {"total": 0, "rejected": 0, "target_rejected": 0}
            )
            stats["total"] += 1

            if ctype == "mid_vowel_rhyme_violation":
                c_res = self.validator.scan_line(item["corrupted_text"], line_number=1)
                p_res = self.validator.scan_line(item["partner_line"], line_number=2)
                c_key = c_res.rhyme_key or self._fallback_word_rhyme_key(item["corrupted_text"])
                p_key = p_res.rhyme_key or self._fallback_word_rhyme_key(item["partner_line"])
                synth_c = c_res.model_copy(update={"rhyme_key": c_key})
                synth_p = p_res.model_copy(update={"rhyme_key": p_key})
                rhyme_check = self.validator.compare_rhyme_group("A", [synth_c, synth_p])
                target_rej = not rhyme_check.is_valid
                rejected = target_rej or (not c_res.is_valid)
                detail = f"rhyme_keys=({c_key!r}, {p_key!r}) status={rhyme_check.status}"
            elif ctype == "post_1400_anachronism":
                c_res = self.validator.scan_line(item["corrupted_text"], line_number=1)
                target_rej = len(c_res.l1_violations) > 0
                rejected = not c_res.is_valid
                detail = (
                    c_res.l1_violations[0]
                    if c_res.l1_violations
                    else f"L1 missed; prosody_valid={c_res.is_valid} ({c_res.metrical_pattern})"
                )
            else:
                c_res = self.validator.scan_line(item["corrupted_text"], line_number=1)
                rejected = not c_res.is_valid
                target_rej = rejected and len(c_res.l1_violations) == 0
                detail = (
                    c_res.l4_notes[0]
                    if c_res.l4_notes
                    else f"prosody_valid={c_res.is_valid} ({c_res.metrical_pattern}, cost={c_res.total_cost})"
                )

            if rejected:
                stats["rejected"] += 1
            if target_rej:
                stats["target_rejected"] += 1

            verdicts.append(
                CorruptionItemVerdict(
                    corruption_id=item["corruption_id"],
                    source_set=item["source_set"],
                    source_ref=item["source_ref"],
                    corruption_type=ctype,
                    original_text=item["original_text"],
                    corrupted_text=item["corrupted_text"],
                    rejected=rejected,
                    rejected_by_target_gate=target_rej,
                    detail=detail,
                )
            )

        summaries: list[CorruptionTypeSummary] = []
        for ctype in (
            "hypermetric_or_hypometric",
            "mid_vowel_rhyme_violation",
            "post_1400_anachronism",
            "stress_inversion_collision",
        ):
            st = by_type_counts.get(ctype, {"total": 0, "rejected": 0, "target_rejected": 0})
            tot = st["total"]
            rej = st["rejected"]
            trej = st["target_rejected"]
            rate = round(rej / tot, 4) if tot else 0.0
            trate = round(trej / tot, 4) if tot else 0.0
            summaries.append(
                CorruptionTypeSummary(
                    corruption_type=ctype,
                    total_items=tot,
                    rejected_items=rej,
                    rejection_rate=rate,
                    target_gate_rejected_items=trej,
                    target_gate_rejection_rate=trate,
                    passed_threshold_70pct=rate >= 0.70,
                )
            )

        total_items = len(verdicts)
        rejected_items = sum(1 for v in verdicts if v.rejected)
        overall_rate = round(rejected_items / total_items, 4) if total_items else 0.0
        return total_items, rejected_items, overall_rate, summaries, verdicts

    def evaluate_final_e_annotations(
        self, filter_sets: set[str] | None = None
    ) -> FinalEAgreementSummary:
        """Compare solver's contextual final -e realizations against 70 annotated reference lines."""
        path = self.holdout_dir / "reference_annotations_70.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        entries = [
            e
            for e in doc["lines"]
            if filter_sets is None or e["set_id"] in filter_sets
        ]

        exact_sylls = 0
        total_decisions = 0
        matched_decisions = 0
        mismatches: list[dict[str, Any]] = []

        for entry in entries:
            res = self.validator.scan_line(entry["text"])
            if res.syllable_count == int(entry["expected_syllable_count"]):
                exact_sylls += 1

            raw_toks = self.validator.transcriber.tokenize_line(entry["text"])
            profiles = [
                self.validator.transcriber.profile_word(w, p) for w, p in raw_toks
            ]

            # Match each annotated surface token in left-to-right order
            used_indices: set[int] = set()
            for dec in entry["final_e_decisions"]:
                total_decisions += 1
                target_norm = normalize_orthography(dec["surface"])
                expected_label = dec["expected"]

                chosen_idx: int | None = None
                for idx, prof in enumerate(profiles):
                    if idx not in used_indices and prof.normalized == target_norm:
                        chosen_idx = idx
                        break

                if chosen_idx is None or not res.tokens or chosen_idx >= len(res.tokens):
                    actual_label = "unscanned"
                else:
                    used_indices.add(chosen_idx)
                    tok = res.tokens[chosen_idx]
                    prof = profiles[chosen_idx]
                    if tok.sandhi_event in {"elided_prevocalic", "elided_weak_h"}:
                        actual_label = "elided"
                    elif tok.sandhi_event == "apocopated":
                        actual_label = "silent"
                    elif prof.final_e_class == FinalEClass.PETRIFIED_SILENT:
                        actual_label = "silent"
                    elif tok.syllables and (
                        tok.syllables[-1].is_final_schwa
                        or tok.ipa_realized.endswith("ə")
                    ):
                        actual_label = "sounded"
                    else:
                        actual_label = "silent"

                if actual_label == expected_label:
                    matched_decisions += 1
                else:
                    mismatches.append(
                        {
                            "ref": entry["ref"],
                            "surface": dec["surface"],
                            "expected": expected_label,
                            "actual": actual_label,
                            "line_text": entry["text"],
                            "scanned_pattern": res.metrical_pattern,
                        }
                    )

        n_lines = len(entries)
        syll_rate = round(exact_sylls / n_lines, 4) if n_lines else 0.0
        agree_rate = round(matched_decisions / total_decisions, 4) if total_decisions else 0.0
        return FinalEAgreementSummary(
            annotated_lines=n_lines,
            exact_syllable_matches=exact_sylls,
            syllable_match_rate=syll_rate,
            total_decisions=total_decisions,
            matched_decisions=matched_decisions,
            agreement_rate=agree_rate,
            passed_threshold_85pct=agree_rate >= 0.85,
            mismatches=mismatches,
        )

    def evaluate_s2_calibration_recall(self) -> float:
        """Compute line recall on the 44 Stratum S2 calibration lines."""
        total = 0
        valid = 0
        for fname in ("troilus_book1_proem.json", "legend_good_women_prol.json"):
            fpath = self.data_dir / "s2_calibration" / fname
            if fpath.exists():
                rep = self.validator.audit_corpus_file(fpath)
                total += rep.total_lines
                valid += rep.valid_lines
        return round(valid / total, 4) if total else 0.0

    @staticmethod
    def _build_threshold_checks(
        norm_set: str,
        set_summaries: list[HoldoutSetSummary],
        h1_h3_line_recall: float,
        h1_h3_rhyme_recall: float,
        h1_h3_lex_cov: float,
        gen_gap_points: float,
        h1_present: bool,
        run_n1: bool,
        n1_rate: float,
        n1_min_type: float,
        final_e_summary: FinalEAgreementSummary | None,
        h4_summary: HoldoutSetSummary | None,
    ) -> list[BlindScansionThresholdCheck]:
        checks: list[BlindScansionThresholdCheck] = []

        if norm_set == "ALL":
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="line_recall_h1_h3",
                    label="Line Recall (H1-H3 non-contested)",
                    value=h1_h3_line_recall,
                    display_value=f"{h1_h3_line_recall * 100:.1f}%",
                    threshold_display=">= 90.0%",
                    passed=h1_h3_line_recall >= 0.90,
                )
            )
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="rhyme_recall_h1_h3",
                    label="Rhyme Recall (H1-H3 non-contested)",
                    value=h1_h3_rhyme_recall,
                    display_value=f"{h1_h3_rhyme_recall * 100:.1f}%",
                    threshold_display=">= 95.0%",
                    passed=h1_h3_rhyme_recall >= 0.95,
                )
            )
        elif set_summaries:
            s = set_summaries[0]
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id=f"line_recall_{s.set_id.lower()}",
                    label=f"Line Recall ({s.set_id} non-contested)",
                    value=s.line_recall,
                    display_value=f"{s.line_recall * 100:.1f}%",
                    threshold_display=">= 90.0%",
                    passed=s.line_recall >= 0.90,
                )
            )
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id=f"rhyme_recall_{s.set_id.lower()}",
                    label=f"Rhyme Recall ({s.set_id} non-contested)",
                    value=s.rhyme_recall,
                    display_value=f"{s.rhyme_recall * 100:.1f}%",
                    threshold_display=">= 95.0%",
                    passed=s.rhyme_recall >= 0.95,
                )
            )

        if run_n1:
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="corruption_rejection_n1",
                    label="Corruption Rejection (N1 overall & min type)",
                    value=n1_rate,
                    display_value=f"{n1_rate * 100:.1f}% (min type {n1_min_type * 100:.1f}%)",
                    threshold_display=">= 85.0% overall, >= 70.0% per type",
                    passed=(n1_rate >= 0.85) and (n1_min_type >= 0.70),
                )
            )

        if final_e_summary is not None:
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="final_e_agreement_ref70",
                    label="Final -e Agreement (70 Reference Lines)",
                    value=final_e_summary.agreement_rate,
                    display_value=f"{final_e_summary.agreement_rate * 100:.1f}% ({final_e_summary.matched_decisions}/{final_e_summary.total_decisions})",
                    threshold_display=">= 85.0%",
                    passed=final_e_summary.passed_threshold_85pct,
                )
            )

        if h1_present:
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="generalization_gap_s2_h1",
                    label="Generalization Gap (S2 Calibration - H1)",
                    value=gen_gap_points,
                    display_value=f"{gen_gap_points:+.1f} pts",
                    threshold_display="<= 10.0 pts",
                    passed=gen_gap_points <= 10.0,
                )
            )

        if norm_set == "ALL" or set_summaries:
            cov = h1_h3_lex_cov if norm_set == "ALL" else set_summaries[0].lexicon_token_coverage
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="lexicon_coverage_s4",
                    label="S4 Lexicon Token Coverage",
                    value=cov,
                    display_value=f"{cov * 100:.1f}%",
                    threshold_display="Report only",
                    passed=None,
                )
            )

        if h4_summary is not None and norm_set == "ALL":
            h1_rec = next((s.line_recall for s in set_summaries if s.set_id == "H1"), h1_h3_line_recall)
            h1_h4_gap = round((h1_rec - h4_summary.line_recall) * 100.0, 2)
            checks.append(
                BlindScansionThresholdCheck(
                    metric_id="untouched_rescore_h4",
                    label="Untouched Holdout H4 (GP 201-400) Step 5 Rescore",
                    value=h4_summary.line_recall,
                    display_value=(
                        f"{h4_summary.line_recall * 100:.1f}% line / "
                        f"{h4_summary.rhyme_recall * 100:.1f}% couplet (H1-H4 gap {h1_h4_gap:+.1f} pts)"
                    ),
                    threshold_display="Report only (Step 5 overfitting check)",
                    passed=None,
                )
            )

        return checks


def render_blind_scansion_markdown(report: BlindScansionReport) -> str:
    """Format a BlindScansionReport into a concise scholarly Markdown summary."""
    lines: list[str] = [
        f"# Validation Plan 02 Report ({report.engine_version})",
        "",
        f"- **Plan ID:** `{report.plan_id}`",
        f"- **Engine Version:** `{report.engine_version}`",
        f"- **SHA-256 Manifest Verified:** `{report.manifest_verified}`",
        f"- **Overall Threshold Verdict:** `{'PASS' if report.all_thresholds_passed else 'FAIL'}`",
        "",
        "## Threshold Summary",
        "",
        "| Metric | Result | Target | Status |",
        "|---|---|---|---|",
    ]
    for chk in report.threshold_checks:
        st = "REPORT" if chk.passed is None else ("PASS" if chk.passed else "FAIL")
        lines.append(f"| {chk.label} | {chk.display_value} | {chk.threshold_display} | {st} |")

    if report.set_summaries or report.h4_untouched_summary:
        lines.extend(
            [
                "",
                "## Held-Out Positive Sets",
                "",
                "| Set | Form | Non-Contested Lines | Line Recall | Contested (Accepted/Total) | Rhyme Recall | S4 Token Coverage |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        all_sets = list(report.set_summaries)
        if report.h4_untouched_summary and all(s.set_id != "H4" for s in all_sets):
            all_sets.append(report.h4_untouched_summary)
        for s in all_sets:
            lines.append(
                f"| {s.set_id} | `{s.metrical_form}` | {s.accepted_lines}/{s.non_contested_lines} | "
                f"{s.line_recall * 100:.1f}% | {s.contested_accepted}/{s.contested_lines} | "
                f"{s.rhyme_recall * 100:.1f}% ({s.rhyme_groups_accepted}/{s.rhyme_groups_non_contested}) | "
                f"{s.lexicon_token_coverage * 100:.1f}% |"
            )

    if report.n1_by_type:
        lines.extend(
            [
                "",
                "## N1 Corruption Rejection Breakdown",
                "",
                "| Corruption Type | Rejected / Total | Rejection Rate | Target-Gate Rate | >= 70% Floor |",
                "|---|---:|---:|---:|---|",
            ]
        )
        for c in report.n1_by_type:
            lines.append(
                f"| `{c.corruption_type}` | {c.rejected_items}/{c.total_items} | "
                f"{c.rejection_rate * 100:.1f}% | {c.target_gate_rejection_rate * 100:.1f}% | "
                f"{'PASS' if c.passed_threshold_70pct else 'FAIL'} |"
            )

    lines.extend(
        [
            "",
            "## Failure Taxonomy (H1-H3 Non-Contested)",
            "",
            "| Failure Bucket | Count |",
            "|---|---:|",
        ]
    )
    for bucket in FAILURE_BUCKETS:
        lines.append(f"| `{bucket}` | {report.failure_taxonomy_totals.get(bucket, 0)} |")

    return "\n".join(lines) + "\n"
