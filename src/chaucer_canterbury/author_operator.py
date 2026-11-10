"""Phase 2: Empirical calibration of AUTHOR_DEFINITION across Strata S2 and S3."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from chaucer_canterbury.models import AuthorDefinition, WordClass
from chaucer_canterbury.scansion import ProsodicValidator

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

ROMANCE_ETYMONS = {"OF", "AN", "LAT"}
GERMANIC_ETYMONS = {"OE", "ON", "ME_RULE"}
V2_TRIGGERS = {
    "ther", "thanne", "than", "now", "thus", "so", "for", "whan", "yit", "yet",
    "never", "ne", "in", "at", "after", "upon", "ther-fore",
}
FINITE_VERBS_INVERSION = {
    "was", "were", "nas", "nis", "is", "hadde", "hath", "han", "shal", "shulde",
    "sholde", "wol", "wolde", "moot", "moste", "may", "kan", "gan", "seyde", "saugh",
}


class AuthorOperatorCalibrator:
    """Extracts F1-F6 numerical invariants from non-Canterbury S2 and S3 corpora."""

    def __init__(
        self,
        data_dir: Path | None = None,
        validator: ProsodicValidator | None = None,
    ) -> None:
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.validator = validator or ProsodicValidator()
        s3_path = self.data_dir / "s3_syntax" / "ppcme2_clause_templates.json"
        self.s3_grammar = json.loads(s3_path.read_text(encoding="utf-8"))

    def calibrate(self, overrides: dict[str, float] | None = None) -> AuthorDefinition:
        """Fit AUTHOR_DEFINITION on S2 (Troilus, LGW, Boece) + S3 (PPCME2)."""
        s2_dir = self.data_dir / "s2_calibration"
        verse_files = [
            s2_dir / "troilus_book1_proem.json",
            s2_dir / "legend_good_women_prol.json",
        ]
        prose_file = s2_dir / "boece_book2_prose.json"

        etymon_counts: dict[str, int] = {"OE": 0, "ON": 0, "OF": 0, "AN": 0, "LAT": 0}
        total_tokens = 0
        total_verse_lines = 0
        feminine_lines = 0
        initial_inv_lines = 0
        headless_lines = 0
        elision_events = 0
        v2_clauses = 0
        total_clauses = 0
        calibrated_titles: list[str] = []

        for vf in verse_files:
            report = self.validator.audit_corpus_file(vf)
            calibrated_titles.append(report.title)
            total_verse_lines += report.total_lines
            elision_events += report.elision_count
            initial_inv_lines += report.license_distribution.get("initial_inversion", 0)
            headless_lines += report.license_distribution.get("headless", 0)

            for stanza in report.stanzas:
                for line in stanza.lines:
                    if line.metrical_pattern.endswith("x"):
                        feminine_lines += 1
                    total_clauses += 1
                    words = [
                        re.sub(r"[^a-zA-Z'-]", "", w.lower())
                        for w in line.original_text.split()
                    ]
                    words = [w for w in words if w]
                    if len(words) >= 3 and words[0] in V2_TRIGGERS and (
                        words[1] in FINITE_VERBS_INVERSION or words[2] in FINITE_VERBS_INVERSION
                    ):
                        v2_clauses += 1
                    for w, punct in self.validator.transcriber.tokenize_line(line.original_text):
                        prof = self.validator.transcriber.profile_word(w, punct)
                        total_tokens += 1
                        if prof.word_class == WordClass.CONTENT:
                            et = prof.etymon if prof.etymon in etymon_counts else "OE"
                            etymon_counts[et] = etymon_counts.get(et, 0) + 1

        if prose_file.exists():
            prose_doc = json.loads(prose_file.read_text(encoding="utf-8"))
            calibrated_titles.append(prose_doc["title"])
            for cl in prose_doc.get("clauses", []):
                total_clauses += 1
                for w, punct in self.validator.transcriber.tokenize_line(cl):
                    prof = self.validator.transcriber.profile_word(w, punct)
                    total_tokens += 1
                    if prof.word_class == WordClass.CONTENT:
                        et = prof.etymon if prof.etymon in etymon_counts else "OE"
                        etymon_counts[et] = etymon_counts.get(et, 0) + 1

        content_total = max(1, sum(etymon_counts.values()))
        rom_count = sum(etymon_counts[k] for k in ("OF", "AN", "LAT"))
        etym_dist = {k: round(v / content_total, 4) for k, v in etymon_counts.items()}

        s3_targets = self.s3_grammar.get("empirical_targets", {})
        emp_v2 = v2_clauses / max(1, total_clauses)
        blended_v2 = round(0.5 * emp_v2 + 0.5 * float(s3_targets.get("v2_nominal_inversion_rate", 0.68)), 3)

        definition = AuthorDefinition(
            dialect_base="london_east_midland_1390",
            etymological_rom_gmc_ratio=round(rom_count / content_total, 3),
            etymology_distribution=etym_dist,
            v2_topicalization_rate=blended_v2,
            negative_concord_rate=round(float(s3_targets.get("negative_concord_rate", 0.84)), 3),
            initial_inversion_rate=round(max(0.07, initial_inv_lines / max(1, total_verse_lines)), 3),
            headless_line_rate=round(max(0.02, headless_lines / max(1, total_verse_lines)), 3),
            feminine_ending_rate=round(feminine_lines / max(1, total_verse_lines), 3),
            elision_per_line_rate=round(elision_events / max(1, total_verse_lines), 3),
            compilatio_digression_density=0.20,
            ironic_disclaimer_threshold=0.58,
            sentence_solaas_homeostasis=0.50,
            calibrated_works=calibrated_titles,
            total_calibrated_tokens=total_tokens,
            total_calibrated_lines=total_verse_lines,
        )

        if overrides:
            patch = {k: v for k, v in overrides.items() if k in AuthorDefinition.model_fields}
            definition = definition.model_copy(update=patch)
        return definition

    @staticmethod
    def kl_divergence(p_gen: dict[str, float], q_ref: dict[str, float], eps: float = 1e-4) -> float:
        """Compute smoothed Kullback-Leibler divergence D_KL(P_gen || Q_S2)."""
        keys = set(p_gen.keys()) | set(q_ref.keys())
        p_sum = sum(p_gen.get(k, 0.0) + eps for k in keys)
        q_sum = sum(q_ref.get(k, 0.0) + eps for k in keys)
        kl = 0.0
        for k in keys:
            pk = (p_gen.get(k, 0.0) + eps) / p_sum
            qk = (q_ref.get(k, 0.0) + eps) / q_sum
            kl += pk * math.log(pk / qk)
        return round(max(0.0, kl), 4)
