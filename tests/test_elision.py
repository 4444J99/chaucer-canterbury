"""Unit tests for Middle English final -e sandhi, prevocalic elision, and weak-h rules."""

from __future__ import annotations

import unittest

from chaucer_canterbury.elision import FinalEResolver
from chaucer_canterbury.phonology import MiddleEnglishTranscriber


class TestFinalEElision(unittest.TestCase):
    def setUp(self) -> None:
        self.transcriber = MiddleEnglishTranscriber()
        self.resolver = FinalEResolver()

    def _profile_phrase(self, text: str):
        tokens = self.transcriber.tokenize_line(text)
        profiles = [self.transcriber.profile_word(w, p) for w, p in tokens]
        return self.resolver.resolve_line_lattice(profiles)

    def test_prevocalic_elision_collapses_schwa(self) -> None:
        # "sorwe of" -> primary zero-cost realization elides final -e of 'sorwe'
        lattice = self._profile_phrase("sorwe of")
        sorwe_top = min(lattice[0], key=lambda c: c.cost)
        self.assertEqual(sorwe_top.sandhi_event, "elided_prevocalic")
        self.assertEqual(len(sorwe_top.syllables), 1)
        self.assertEqual(sorwe_top.ipa_realized, "ˈsɔrw")

    def test_preconsonantal_final_e_preserved_by_default(self) -> None:
        # "double sorwe" -> 'double' before consonant 's' preserves disyllabic [ˈduː.blə] at cost 0
        lattice = self._profile_phrase("double sorwe")
        double_top = min(lattice[0], key=lambda c: c.cost)
        self.assertEqual(double_top.sandhi_event, "preserved_final_e")
        self.assertEqual(len(double_top.syllables), 2)
        self.assertEqual(double_top.ipa_realized, "ˈduː.blə")

    def test_weak_h_triggers_elision_but_strong_germanic_h_does_not(self) -> None:
        # Weak pronoun 'his' and French h-muet 'honour' trigger weak-h elision
        lat_weak = self._profile_phrase("parte his")
        top_weak = min(lat_weak[0], key=lambda c: c.cost)
        self.assertEqual(top_weak.sandhi_event, "elided_weak_h")
        self.assertEqual(len(top_weak.syllables), 1)

        lat_fr = self._profile_phrase("grante honour")
        top_fr = min(lat_fr[0], key=lambda c: c.cost)
        self.assertEqual(top_fr.sandhi_event, "elided_weak_h")
        self.assertEqual(len(top_fr.syllables), 1)

        # Strong Germanic 'herte' does NOT trigger weak-h elision
        lat_strong = self._profile_phrase("parte herte")
        top_strong = min(lat_strong[0], key=lambda c: c.cost)
        self.assertEqual(top_strong.sandhi_event, "preserved_final_e")
        self.assertEqual(len(top_strong.syllables), 2)

    def test_line_final_etymological_e_never_apocopates(self) -> None:
        lattice = self._profile_phrase("to Troye")
        troye_cands = lattice[-1]
        self.assertTrue(all(len(c.syllables) == 2 for c in troye_cands))
        self.assertTrue(all(c.ipa_realized.endswith("ə") for c in troye_cands))

    def test_palatal_y_is_consonantal_onset_not_vowel(self) -> None:
        # 'parte ye' -> 'ye' starts with [j], so 'parte' preserves its final -e!
        lattice = self._profile_phrase("parte ye")
        top = min(lattice[0], key=lambda c: c.cost)
        self.assertEqual(top.sandhi_event, "preserved_final_e")
        self.assertEqual(len(top.syllables), 2)


if __name__ == "__main__":
    unittest.main()
