"""Validation Plan 02 tests: manifest freeze, strict holdout isolation, and CLI/evaluator checks."""

from __future__ import annotations

import builtins
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from chaucer_canterbury import cli
from chaucer_canterbury.author_operator import AuthorOperatorCalibrator
from chaucer_canterbury.blind_scansion import (
    BlindScansionEvaluator,
    verify_holdout_manifest,
)
from chaucer_canterbury.generator import ChaucerGenerativePipeline
from chaucer_canterbury.validators import run_holdout_counterfactual_suite

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src" / "chaucer_canterbury"
HOLDOUT_DIR = REPO_ROOT / "data" / "s1_witnesses" / "blind_scansion"

NON_EVAL_MODULES = (
    "lexicon.py",
    "phonology.py",
    "elision.py",
    "scansion.py",
    "author_operator.py",
    "world_state.py",
    "generator.py",
    "validators.py",
)


class TestBlindScansionHoldoutSuite(unittest.TestCase):
    def test_frozen_manifest_integrity_and_evaluation_only_flags(self) -> None:
        manifest = verify_holdout_manifest(HOLDOUT_DIR)
        self.assertEqual(manifest["holdout_flag"], "EVALUATION_ONLY")
        expected_files = {
            "h1_general_prologue_1_200.json",
            "h2_clerks_tale_stanzas_1_20.json",
            "h3_sir_thopas_1_60.json",
            "h4_general_prologue_201_400.json",
            "n1_corrupted_340.json",
            "reference_annotations_70.json",
        }
        self.assertEqual(set(manifest["files"].keys()), expected_files)

    def test_static_isolation_no_generator_or_calibration_module_references_blind_scansion(
        self,
    ) -> None:
        for mod_name in NON_EVAL_MODULES:
            source = (SRC_DIR / mod_name).read_text(encoding="utf-8")
            self.assertNotIn(
                "blind_scansion",
                source,
                f"Module {mod_name} must never reference or import blind_scansion holdouts",
            )

    def test_runtime_isolation_blocks_blind_scansion_reads_during_calibration_and_generation(
        self,
    ) -> None:
        orig_read_text = Path.read_text
        orig_read_bytes = Path.read_bytes
        orig_open = builtins.open

        def guarded_read_text(path_obj: Path, *args, **kwargs) -> str:
            if "blind_scansion" in str(path_obj):
                raise PermissionError(f"Forbidden holdout read: {path_obj}")
            return orig_read_text(path_obj, *args, **kwargs)

        def guarded_read_bytes(path_obj: Path, *args, **kwargs) -> bytes:
            if "blind_scansion" in str(path_obj):
                raise PermissionError(f"Forbidden holdout read: {path_obj}")
            return orig_read_bytes(path_obj, *args, **kwargs)

        def guarded_open(file, *args, **kwargs):
            if "blind_scansion" in str(file):
                raise PermissionError(f"Forbidden holdout open: {file}")
            return orig_open(file, *args, **kwargs)

        with (
            patch.object(Path, "read_text", guarded_read_text),
            patch.object(Path, "read_bytes", guarded_read_bytes),
            patch("builtins.open", guarded_open),
        ):
            cal = AuthorOperatorCalibrator().calibrate()
            self.assertEqual(cal.total_calibrated_lines, 44)

            pipe = ChaucerGenerativePipeline()
            world = pipe.env.initial_world_state()
            turn, _ = pipe.generate_turn(world, forced_speaker_id="yeoman", unit_count=1)
            self.assertGreaterEqual(len(turn.tale_lines), 2)

            cf = run_holdout_counterfactual_suite(pipe)
            self.assertEqual(cf.total_scenarios, 6)

            # Confirm the guard actually blocks reading blind_scansion
            with self.assertRaises(PermissionError):
                _ = (HOLDOUT_DIR / "manifest.json").read_text(encoding="utf-8")

    def test_cli_validate_holdout_h1_writes_json_report_with_verdicts_and_buckets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "h1_report.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                _ = cli.main(
                    [
                        "validate-holdout",
                        "--set",
                        "H1",
                        "--output",
                        str(out_json),
                        "--json",
                    ]
                )
            self.assertTrue(out_json.exists())
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["manifest_verified"])
            self.assertEqual(payload["evaluated_sets"], ["H1"])
            self.assertEqual(len(payload["line_verdicts"]), 200)
            h1_sum = payload["set_summaries"][0]
            self.assertEqual(h1_sum["total_lines"], 200)
            self.assertEqual(h1_sum["contested_lines"], 4)
            self.assertEqual(h1_sum["non_contested_lines"], 196)
            self.assertEqual(
                set(h1_sum["failure_counts"].keys()),
                {"lexicon_gap", "final_e_rule", "stress_or_lattice", "rhyme_phonology"},
            )
            self.assertIsNotNone(payload["final_e_summary"])
            self.assertEqual(payload["final_e_summary"]["annotated_lines"], 50)

    def test_full_evaluator_runs_all_sets_and_populates_n1_and_ref70(self) -> None:
        report = BlindScansionEvaluator(engine_version="test-run").run("ALL")
        self.assertEqual(report.h1_h3_non_contested_lines, 196 + 138 + 59)
        self.assertEqual(report.n1_total_items, 340)
        self.assertEqual(len(report.n1_by_type), 4)
        self.assertIsNotNone(report.final_e_summary)
        assert report.final_e_summary is not None
        self.assertEqual(report.final_e_summary.annotated_lines, 70)
        self.assertIsNotNone(report.h4_untouched_summary)
        assert report.h4_untouched_summary is not None
        self.assertEqual(report.h4_untouched_summary.total_lines, 200)
        self.assertTrue(report.all_thresholds_passed)
        self.assertGreaterEqual(report.h1_h3_line_recall, 0.90)
        self.assertGreaterEqual(report.h1_h3_rhyme_recall, 0.95)
        self.assertGreaterEqual(report.n1_overall_rejection_rate, 0.85)
        self.assertTrue(all(c.passed_threshold_70pct for c in report.n1_by_type))
        self.assertGreaterEqual(report.final_e_summary.agreement_rate, 0.85)
        self.assertLessEqual(report.generalization_gap_points, 10.0)
        self.assertGreaterEqual(report.h4_untouched_summary.line_recall, 0.90)

    def test_v02_tail_rhyme_and_feminine_ending_constraints(self) -> None:
        from chaucer_canterbury.scansion import ProsodicValidator

        validator = ProsodicValidator()
        # Genuine Sir Thopas 6-line tail-rhyme stanza (4-4-3-4-4-3 beats, AABCCB)
        stanza = validator.audit_stanza(
            lines=[
                (1902, "Listeth, lordes, in good entent,"),
                (1903, "And I wol telle verrayment"),
                (1904, "Of mirthe and of solas;"),
                (1905, "Al of a knyght was fair and gent"),
                (1906, "In bataille and in tourneyment,"),
                (1907, "His name was sir Thopas."),
            ],
            rhyme_scheme="AABCCB",
            stanza_id="H3_S01",
            beat_targets=[4, 4, 3, 4, 4, 3],
        )
        self.assertTrue(stanza.is_valid)
        self.assertEqual([ln.beat_count for ln in stanza.lines], [4, 4, 3, 4, 4, 3])

        # Ungrammatical stressed lexical monosyllable in 11th feminine offbeat must be rejected
        bad_fem = validator.scan_line("Whan that Aprille with his shoures soote book")
        self.assertFalse(bad_fem.is_valid)


if __name__ == "__main__":
    unittest.main()
