"""Unit tests for Phases 2-5: AuthorOperatorCalibrator, PilgrimageEnvironment,
ChaucerGenerativePipeline, Conservation Laws L1-L7, and Holdout Counterfactual Suite.
"""

from __future__ import annotations

import unittest

from chaucer_canterbury.generator import ChaucerGenerativePipeline
from chaucer_canterbury.models import MetricalForm
from chaucer_canterbury.validators import run_holdout_counterfactual_suite


class TestPhasesTwoThroughFive(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = ChaucerGenerativePipeline()
        cls.author_def = cls.pipeline.calibrator.calibrate()

    def test_author_operator_calibration_from_s2_and_s3(self) -> None:
        self.assertGreaterEqual(self.author_def.total_calibrated_lines, 44)
        self.assertGreater(self.author_def.etymological_rom_gmc_ratio, 0.20)
        self.assertLess(self.author_def.etymological_rom_gmc_ratio, 0.90)
        self.assertAlmostEqual(sum(self.author_def.etymology_distribution.values()), 1.0, places=2)
        self.assertGreater(self.author_def.v2_topicalization_rate, 0.15)

    def test_thirty_pilgrims_and_silent_voices_loaded(self) -> None:
        self.assertEqual(len(self.pipeline.env.pilgrims), 30)
        silent = [p.id for p in self.pipeline.env.pilgrims.values() if "silent" in p.manuscript_status]
        for expected in ("yeoman", "plowman", "haberdasher", "carpenter", "weaver", "dyer", "tapestry_maker"):
            self.assertIn(expected, silent)

    def test_riding_rhyme_and_rhyme_royal_generation_pass_all_laws(self) -> None:
        world = self.pipeline.env.initial_world_state()
        # Turn 1: Knight (Riding Rhyme or Rhyme Royal)
        art1, world1 = self.pipeline.generate_turn(world, author_def=self.author_def, unit_count=3)
        self.assertEqual(art1.speaker_id, "knight")
        self.assertTrue(all(c.passed for c in art1.conservation_laws), [c.model_dump() for c in art1.conservation_laws if not c.passed])

        # Turn 2: Miller interrupts Knight via Quiting Ledger!
        art2, world2 = self.pipeline.generate_turn(world1, author_def=self.author_def, unit_count=3)
        self.assertEqual(art2.speaker_id, "miller")
        self.assertEqual(art2.selection_mode, "quiting_interruption")
        self.assertTrue(all(c.passed for c in art2.conservation_laws), [c.model_dump() for c in art2.conservation_laws if not c.passed])

        # Turn 3: Reeve quites Miller with Northernisms (/a:n/ gaan/staan)
        art3, world3 = self.pipeline.generate_turn(world2, author_def=self.author_def, unit_count=3)
        self.assertEqual(art3.speaker_id, "reeve")
        self.assertEqual(art3.selection_mode, "quiting_interruption")
        self.assertTrue(all(c.passed for c in art3.conservation_laws), [c.model_dump() for c in art3.conservation_laws if not c.passed])

        # Explicit Rhyme Royal check for Clerk of Oxenford
        art_rr, _ = self.pipeline.generate_turn(
            world3,
            author_def=self.author_def,
            forced_speaker_id="clerk",
            forced_form=MetricalForm.RHYME_ROYAL,
            unit_count=2,
        )
        self.assertEqual(len(art_rr.tale_lines), 14)
        self.assertTrue(all(c.passed for c in art_rr.conservation_laws), [c.model_dump() for c in art_rr.conservation_laws if not c.passed])

    def test_tail_rhyme_and_cadenced_prose_vehicles(self) -> None:
        world = self.pipeline.env.initial_world_state()
        art_tr, world = self.pipeline.generate_turn(
            world,
            author_def=self.author_def,
            forced_speaker_id="chaucer_pilgrim",
            forced_form=MetricalForm.TAIL_RHYME,
            unit_count=1,
        )
        self.assertEqual(art_tr.metrical_form, MetricalForm.TAIL_RHYME)
        self.assertTrue(all(c.passed for c in art_tr.conservation_laws))

        art_pr, _ = self.pipeline.generate_turn(
            world,
            author_def=self.author_def,
            forced_speaker_id="parson",
            forced_form=MetricalForm.CADENCED_PROSE,
            unit_count=3,
        )
        self.assertEqual(art_pr.metrical_form, MetricalForm.CADENCED_PROSE)
        self.assertTrue(all(c.passed for c in art_pr.conservation_laws))

    def test_holdout_counterfactual_suite_convergence_and_non_copying(self) -> None:
        report = run_holdout_counterfactual_suite(self.pipeline)
        self.assertEqual(report.total_scenarios, 6)
        self.assertEqual(report.convergent_scenarios, 6)
        self.assertTrue(report.all_l6_non_copying_passed)
        self.assertGreaterEqual(report.mean_prosody_pass_rate, 0.95)


if __name__ == "__main__":
    unittest.main()
