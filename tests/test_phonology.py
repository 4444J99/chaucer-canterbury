"""Unit tests for pre-Great-Vowel-Shift Middle English phonology and Law L1."""

from __future__ import annotations

import unittest

from chaucer_canterbury.models import FinalEClass, WordClass
from chaucer_canterbury.phonology import MiddleEnglishTranscriber


class TestMiddleEnglishPhonology(unittest.TestCase):
    def setUp(self) -> None:
        self.transcriber = MiddleEnglishTranscriber()

    def test_sounded_historical_consonants_and_gh_allophones(self) -> None:
        # Front-vowel 'gh' -> palatal fricative [ç], sounded initial [kn]
        knyght = self.transcriber.profile_word("knyght")
        self.assertEqual(knyght.variants[0].ipa, "kniçt")
        self.assertEqual(len(knyght.variants[0].syllables), 1)

        # Rule-based front 'gh' on unseen word ('wight') vs back 'gh' ('saugh')
        wight = self.transcriber.profile_word("wight")
        self.assertIn("ç", wight.variants[0].ipa)

        saugh = self.transcriber.profile_word("saugh")
        self.assertIn("x", saugh.variants[0].ipa)

        # Sounded initial [wr] and pre-GVS [iː] in 'write'
        write = self.transcriber.profile_word("write")
        self.assertEqual(write.variants[0].ipa, "ˈwriː.tə")

    def test_open_vs_close_mid_vowels(self) -> None:
        # Close /oː/ vs Open /ɔː/
        roote = self.transcriber.profile_word("roote")
        goon = self.transcriber.profile_word("goon")
        self.assertEqual(roote.vowel_quality, "close_o")
        self.assertEqual(goon.vowel_quality, "open_o")
        self.assertIn("oː", roote.variants[0].ipa)
        self.assertIn("ɔː", goon.variants[0].ipa)

        # Close /eː/ vs Open /ɛː/
        swete = self.transcriber.profile_word("swete")
        rede = self.transcriber.profile_word("rede")
        self.assertEqual(swete.vowel_quality, "close_e")
        self.assertEqual(rede.vowel_quality, "open_e")

    def test_scribal_orthography_normalization(self) -> None:
        # Initial 'ff' -> 'f', yogh 'ȝ' -> 'y'/'gh', diaeresis 'yë' -> disyllabic [ˈiː.ə]
        ffro = self.transcriber.profile_word("ffro")
        self.assertEqual(ffro.normalized, "fro")
        self.assertEqual(ffro.word_class, WordClass.FUNCTION)

        ye_eye = self.transcriber.profile_word("yë")
        self.assertEqual(len(ye_eye.variants[0].syllables), 2)
        self.assertEqual(ye_eye.variants[0].ipa, "ˈiː.ə")

    def test_petrified_silent_e_vs_etymological_e(self) -> None:
        thise = self.transcriber.profile_word("thise")
        self.assertEqual(thise.final_e_class, FinalEClass.PETRIFIED_SILENT)
        self.assertEqual(len(thise.variants[0].syllables), 1)

        sorwe = self.transcriber.profile_word("sorwe")
        self.assertEqual(sorwe.final_e_class, FinalEClass.ETYMOLOGICAL)
        self.assertEqual(len(sorwe.variants[0].syllables), 2)
        self.assertTrue(sorwe.variants[0].syllables[-1].is_final_schwa)

    def test_romance_stress_doublets(self) -> None:
        torment = self.transcriber.profile_word("torment")
        stresses = {v.stress_pattern for v in torment.variants}
        self.assertIn("10", stresses)  # Germanic root-initial ('túrment')
        self.assertIn("01", stresses)  # Romance rhyme-final ('tormént')

    def test_l1_chronological_gate(self) -> None:
        entry_ok = self.transcriber.lexicon.lookup("sorwe")
        self.assertIsNone(self.transcriber.lexicon.check_l1_chronology("sorwe", entry_ok))

        entry_bad = self.transcriber.lexicon.lookup("internet")
        viol = self.transcriber.lexicon.check_l1_chronology("internet", entry_bad)
        self.assertIsNotNone(viol)
        assert viol is not None
        self.assertIn("1974 > 1400", viol)


if __name__ == "__main__":
    unittest.main()
