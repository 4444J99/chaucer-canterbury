"""End-to-end prosodic scansion, stanza rhyme, and adversarial rejection tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from chaucer_canterbury.models import MetricalLicense
from chaucer_canterbury.scansion import ProsodicValidator

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "s2_calibration"


class TestProsodicScansionValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = ProsodicValidator()

    def test_troilus_book1_proem_rhyme_royal_100_percent(self) -> None:
        report = self.validator.audit_corpus_file(DATA_DIR / "troilus_book1_proem.json")
        self.assertEqual(report.total_lines, 28)
        self.assertEqual(report.valid_lines, 28)
        self.assertEqual(report.rhyme_groups_valid, 12)
        self.assertEqual(report.l1_chronology_violations, [])

    def test_legend_of_good_women_couplets_100_percent(self) -> None:
        report = self.validator.audit_corpus_file(DATA_DIR / "legend_good_women_prol.json")
        self.assertEqual(report.total_lines, 16)
        self.assertEqual(report.valid_lines, 16)
        self.assertEqual(report.rhyme_groups_valid, 8)

    def test_initial_trochaic_inversion_detected(self) -> None:
        # TC 1.10: "Help me that am the sorwful instrument" -> / x x / x / x / x /
        res = self.validator.scan_line("Help me that am the sorwful instrument")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.license_used, MetricalLicense.INITIAL_INVERSION)
        self.assertEqual(res.metrical_pattern, "/xx/x/x/x/")
        self.assertEqual(res.syllable_count, 10)

    def test_headless_nine_syllable_line_supported(self) -> None:
        # Classic 9-syllable headless line: / x / x / x / x /
        res = self.validator.scan_line("Twentie bokes clad in blak or reed")
        self.assertTrue(res.is_valid)
        self.assertIn(
            res.license_used,
            {MetricalLicense.HEADLESS, MetricalLicense.REGULAR_DECASYLLABIC},
        )

    def test_rejects_open_vs_close_long_vowel_rhyme_violation(self) -> None:
        # Chaucer separates open /ɔː/ ('wo', 'goon') from close /oː/ ('do', 'roote')
        stanza = self.validator.audit_stanza(
            lines=[
                (1, "And I acorde wel that hit is wo,"),
                (2, "For every wight ne may no bettre do."),
            ],
            rhyme_scheme="AA",
            stanza_id="BAD_O_VOWEL",
        )
        self.assertFalse(stanza.is_valid)
        self.assertEqual(stanza.rhyme_audits[0].status, "MISMATCH")

        # Chaucer separates open /ɛː/ ('drede') from close /eː/ ('swete')
        stanza_e = self.validator.audit_stanza(
            lines=[
                (1, "In al this world withouten any drede,"),
                (2, "The brighte morwe shal be fressh and swete."),
            ],
            rhyme_scheme="AA",
            stanza_id="BAD_E_VOWEL",
        )
        self.assertFalse(stanza_e.is_valid)

    def test_rejects_unmetrical_hypermetric_or_hypometric_lines(self) -> None:
        short_line = self.validator.scan_line("The sorwe of Troye")
        self.assertFalse(short_line.is_valid)

        long_line = self.validator.scan_line(
            "The double sorwe of worthy Troilus and fair Criseyde to tellen evere"
        )
        self.assertFalse(long_line.is_valid)

    def test_rejects_l1_anachronistic_post_1400_vocabulary(self) -> None:
        # Metrically 10 syllables (x/x/x/x/x/), but violates L1 (<=1400 CE)
        anachronistic = self.validator.scan_line("He fond hit writen on the internet")
        self.assertFalse(anachronistic.is_valid)
        self.assertEqual(len(anachronistic.l1_violations), 1)
        self.assertIn("internet", anachronistic.l1_violations[0])


if __name__ == "__main__":
    unittest.main()
