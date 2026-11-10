"""Late-14th-century London Middle English grapheme-to-phoneme (G2P) transcriber."""

from __future__ import annotations

import re

from chaucer_canterbury.lexicon import (
    MEDLexicon,
    OPTIONAL_APOCOPE_WORDS,
    normalize_orthography,
)
from chaucer_canterbury.models import (
    FinalEClass,
    PhonologicalVariant,
    Syllable,
    WordClass,
    WordProfile,
)

VOWEL_CHARS = set("aeiouyëé")

# Prefixes that remain unstressed so primary stress falls on the root syllable
UNSTRESSED_PREFIXES = (
    "for", "bi", "be", "to-", "un-", "y-", "i-", "a-", "up-", "with-",
)

# Romance suffixes supporting Anglo-Norman / Continental right-edge stress in Chaucer
ROMANCE_STRESS_SUFFIXES = (
    "ioun", "oun", "itee", "aunce", "ence", "ent", "aille", "esse", "our", "ure", "age",
)


class MiddleEnglishTranscriber:
    """Transcribes Middle English words into pre-Great-Vowel-Shift London IPA lattices."""

    def __init__(self, lexicon: MEDLexicon | None = None) -> None:
        self.lexicon = lexicon or MEDLexicon()

    def tokenize_line(self, line: str) -> list[tuple[str, str]]:
        """Split a Middle English verse line into (word_token, trailing_punctuation) pairs."""
        # Strip editorial marks like † or * while keeping hyphens, apostrophes, diaeresis
        cleaned = re.sub(r"[†*°\"“”‘’]", "", line.strip())
        raw_parts = re.findall(r"[A-Za-zȝþðëé'-]+|[,.;:!?—–]+", cleaned)
        tokens: list[tuple[str, str]] = []
        for part in raw_parts:
            if re.match(r"^[,.;:!?—–]+$", part):
                if tokens:
                    prev_word, prev_punct = tokens[-1]
                    tokens[-1] = (prev_word, prev_punct + part)
            else:
                tokens.append((part, ""))
        return tokens

    def profile_word(self, surface: str, trailing_punct: str = "") -> WordProfile:
        """Build a complete four-tier phonological WordProfile for a surface token."""
        norm = normalize_orthography(surface)
        entry = self.lexicon.lookup(surface)
        word_class = self.lexicon.classify_word_class(norm, entry)
        final_e_class = self.lexicon.classify_final_e(norm, entry)
        weak_h = self.lexicon.is_weak_h(norm, entry)
        starts_vowel = self._starts_with_vowel_sound(norm)

        if entry is not None:
            variants = self._variants_from_lexicon_entry(entry, final_e_class)
            return WordProfile(
                surface=surface,
                normalized=norm,
                lemma=entry.get("lemma", norm),
                med_id=entry.get("med_id"),
                etymon=entry.get("etymon", "OE"),
                earliest_year=int(entry.get("earliest_year", 1390)),
                word_class=word_class,
                final_e_class=final_e_class,
                weak_h=weak_h,
                starts_with_vowel=starts_vowel,
                vowel_quality=entry.get("vowel_quality"),
                trailing_punct=trailing_punct,
                variants=variants,
            )

        variants, inferred_quality = self._rule_based_g2p(norm, word_class, final_e_class)
        return WordProfile(
            surface=surface,
            normalized=norm,
            lemma=norm,
            med_id=None,
            etymon=self._infer_etymon(norm),
            earliest_year=1390,
            word_class=word_class,
            final_e_class=final_e_class,
            weak_h=weak_h,
            starts_with_vowel=starts_vowel,
            vowel_quality=inferred_quality,
            trailing_punct=trailing_punct,
            variants=variants,
        )

    @staticmethod
    def _starts_with_vowel_sound(norm: str) -> bool:
        if not norm:
            return False
        # 'y' before a vowel is palatal approximant [j] ('ye', 'yit', 'yow'), NOT a vowel!
        # 'y-' / 'yë' before a consonant or diaeresis IS vowel [i] ('y-be', 'y-see', 'yë').
        if norm.startswith("y"):
            if len(norm) == 1 or norm.startswith(("y-", "yë")):
                return True
            return norm[1] not in VOWEL_CHARS
        return norm[0] in {"a", "e", "i", "o", "u", "ë", "é"}

    @staticmethod
    def _infer_etymon(norm: str) -> str:
        if norm.endswith(ROMANCE_STRESS_SUFFIXES) or "cioun" in norm or "aille" in norm:
            return "OF"
        return "ME_CORE"

    def _variants_from_lexicon_entry(
        self, entry: dict, final_e_class: FinalEClass
    ) -> list[PhonologicalVariant]:
        variants: list[PhonologicalVariant] = []
        base_sylls = self._parse_ipa_and_stress(
            entry["ipa"], entry["stress"], final_e_class
        )
        variants.append(
            PhonologicalVariant(
                ipa=entry["ipa"],
                syllables=base_sylls,
                stress_pattern=entry["stress"],
                cost=0.0,
                note="lexicon_canonical",
            )
        )
        for alt in entry.get("alt_ipas", []):
            alt_e_class = (
                FinalEClass.NONE
                if not alt["ipa"].endswith("ə")
                else final_e_class
            )
            alt_sylls = self._parse_ipa_and_stress(
                alt["ipa"], alt["stress"], alt_e_class
            )
            variants.append(
                PhonologicalVariant(
                    ipa=alt["ipa"],
                    syllables=alt_sylls,
                    stress_pattern=alt["stress"],
                    cost=float(alt.get("cost", 0.15)),
                    note=alt.get("note", "lexicon_alt"),
                )
            )
        return variants

    @staticmethod
    def _parse_ipa_and_stress(
        ipa_str: str, stress_str: str, final_e_class: FinalEClass
    ) -> list[Syllable]:
        raw_sylls = [s.lstrip("ˈˌ") for s in ipa_str.split(".") if s]
        stresses = [int(ch) for ch in stress_str]
        if len(stresses) < len(raw_sylls):
            stresses.extend([0] * (len(raw_sylls) - len(stresses)))
        syllables: list[Syllable] = []
        for idx, (s_ipa, st) in enumerate(zip(raw_sylls, stresses)):
            is_last = idx == len(raw_sylls) - 1
            is_final_schwa = (
                is_last
                and s_ipa.endswith("ə")
                and st == 0
                and final_e_class
                in {
                    FinalEClass.ETYMOLOGICAL,
                    FinalEClass.INFLECTIONAL,
                    FinalEClass.OPTIONAL_APOCOPE,
                }
            )
            syllables.append(
                Syllable(ipa=s_ipa, stress=st, is_final_schwa=is_final_schwa)
            )
        return syllables

    def _rule_based_g2p(
        self, norm: str, word_class: WordClass, final_e_class: FinalEClass
    ) -> tuple[list[PhonologicalVariant], str | None]:
        """Deterministic pre-GVS London Middle English syllabifier and IPA transcriber."""
        # Convert intervocalic scribal 'u' -> 'v' (e.g., 'loue' -> 'love', 'loues' -> 'loves')
        work = re.sub(r"([aeiouy])u([aeiouyë])", r"\1v\2", norm)

        # Proclitic contractions like "t'endite" or "th'array"
        proclitic_prefix = ""
        if "'" in work:
            parts = work.split("'", 1)
            if parts[0] in {"t", "th", "n"} and parts[1]:
                proclitic_prefix = {"t": "t", "th": "ð", "n": "n"}[parts[0]]
                work = parts[1]

        orth_sylls = self._syllabify_orthography(work, final_e_class)
        stresses = self._assign_stress(work, orth_sylls, word_class)

        ipa_sylls: list[str] = []
        vowel_quality: str | None = None
        for idx, (orth_s, st) in enumerate(zip(orth_sylls, stresses)):
            is_open = idx < len(orth_sylls) - 1 and self._ends_in_vowel_grapheme(orth_s)
            s_ipa, v_qual = self._transcribe_syllable(
                orth_s, is_stressed=(st > 0), is_open=is_open, is_final=(idx == len(orth_sylls) - 1)
            )
            if idx == 0 and proclitic_prefix:
                s_ipa = proclitic_prefix + s_ipa
            if st == 1 and v_qual:
                vowel_quality = v_qual
            ipa_sylls.append(s_ipa)

        formatted_ipa = ".".join(
            f"ˈ{s}" if st == 1 else (f"ˌ{s}" if st == 2 else s)
            for s, st in zip(ipa_sylls, stresses)
        )
        stress_str = "".join(str(st) for st in stresses)
        base_syllables = self._parse_ipa_and_stress(formatted_ipa, stress_str, final_e_class)

        variants = [
            PhonologicalVariant(
                ipa=formatted_ipa,
                syllables=base_syllables,
                stress_pattern=stress_str,
                cost=0.0,
                note="rule_canonical",
            )
        ]

        # Add optional apocope variant for high-frequency variable words
        if (
            final_e_class == FinalEClass.OPTIONAL_APOCOPE
            or norm in OPTIONAL_APOCOPE_WORDS
        ) and len(base_syllables) >= 2 and base_syllables[-1].ipa.endswith("ə"):
            apoc_sylls = self._build_apocopated_syllables(base_syllables)
            if apoc_sylls:
                apoc_st = "".join(str(s.stress) for s in apoc_sylls)
                apoc_ipa = ".".join(
                    f"ˈ{s.ipa}" if s.stress == 1 else s.ipa for s in apoc_sylls
                )
                variants.append(
                    PhonologicalVariant(
                        ipa=apoc_ipa,
                        syllables=apoc_sylls,
                        stress_pattern=apoc_st,
                        cost=0.12,
                        note="rule_optional_apocope",
                    )
                )

        # Add Romance stress shift variant for disyllabic/trisyllabic French loans
        if len(base_syllables) >= 2 and work.endswith(ROMANCE_STRESS_SUFFIXES):
            alt_st = [0] * (len(base_syllables) - 1) + [1]
            if base_syllables[-1].is_final_schwa and len(base_syllables) >= 3:
                alt_st = [0] * (len(base_syllables) - 2) + [1, 0]
            alt_st_str = "".join(str(x) for x in alt_st)
            if alt_st_str != stress_str:
                alt_sylls = [
                    Syllable(ipa=s.ipa, stress=st, is_final_schwa=s.is_final_schwa)
                    for s, st in zip(base_syllables, alt_st)
                ]
                alt_ipa = ".".join(
                    f"ˈ{s.ipa}" if s.stress == 1 else s.ipa for s in alt_sylls
                )
                variants.append(
                    PhonologicalVariant(
                        ipa=alt_ipa,
                        syllables=alt_sylls,
                        stress_pattern=alt_st_str,
                        cost=0.12,
                        note="romance_stress_shift",
                    )
                )

        return variants, vowel_quality

    @staticmethod
    def _build_apocopated_syllables(syllables: list[Syllable]) -> list[Syllable]:
        """Drop final schwa and merge remaining onset consonant into preceding coda."""
        if len(syllables) < 2:
            return []
        last = syllables[-1]
        stem_coda = last.ipa[:-1]  # strip trailing 'ə'
        kept = [s.model_copy() for s in syllables[:-1]]
        kept[-1].ipa = kept[-1].ipa + stem_coda
        kept[-1].is_final_schwa = False
        return kept

    def _syllabify_orthography(
        self, word: str, final_e_class: FinalEClass
    ) -> list[str]:
        """Split a normalized Middle English word into orthographic syllables."""
        # Explicit hyphenated prefixes/compounds ('y-be', 'him-self', 'but-if', 'ther-to')
        if "-" in word:
            subparts = [p for p in word.split("-") if p]
            if len(subparts) > 1:
                combined: list[str] = []
                for idx, sp in enumerate(subparts):
                    sub_e = (
                        final_e_class
                        if idx == len(subparts) - 1
                        else FinalEClass.NONE
                    )
                    combined.extend(self._syllabify_orthography(sp, sub_e))
                return combined

        # Strip petrified silent final -e before syllabifying ('thise' -> 'this', 'oure' -> 'our')
        working = word
        if final_e_class == FinalEClass.PETRIFIED_SILENT and working.endswith("e") and len(working) > 2:
            working = working[:-1]

        # Handle diaeresis 'ë' explicitly ('yë' -> ['y', 'ë'], 'lyë' -> ['ly', 'ë'])
        if "ë" in working:
            idx = working.index("ë")
            left = working[:idx]
            right = working[idx:]
            left_sylls = self._syllabify_orthography(left, FinalEClass.NONE) if left else []
            return left_sylls + [right]

        # Identify vowel nucleus spans (treating digraphs as single vocalic nuclei)
        spans: list[tuple[int, int]] = []
        i = 0
        n = len(working)
        digraph_vowels = {
            "aa", "ee", "oo", "ou", "ow", "au", "aw", "ai", "ay", "ei", "ey", "oi", "oy", "eu", "ew", "ie",
        }
        while i < n:
            ch = working[i]
            is_v = ch in VOWEL_CHARS and not (
                ch == "y" and i == 0 and i + 1 < n and working[i + 1] in VOWEL_CHARS
            )
            if is_v:
                if i + 1 < n and working[i : i + 2] in digraph_vowels:
                    spans.append((i, i + 2))
                    i += 2
                else:
                    spans.append((i, i + 1))
                    i += 1
            else:
                i += 1

        if len(spans) <= 1:
            return [working]

        # Partition intervocalic consonants using Maximal Onset Principle for ME clusters
        legal_onsets = {
            "bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr",
            "sl", "sm", "sn", "sp", "st", "sw", "tr", "tw", "kn", "gn", "wr",
            "ch", "sh", "th", "wh", "gh", "qu", "sch",
        }
        syllables: list[str] = []
        start_idx = 0
        for k in range(len(spans) - 1):
            v1_end = spans[k][1]
            v2_start = spans[k + 1][0]
            cons = working[v1_end:v2_start]
            if len(cons) == 0:
                split_at = v1_end
            elif len(cons) == 1:
                split_at = v1_end  # V.CV open syllable (e.g., 'ta.le', 'so.re')
            elif cons in legal_onsets:
                split_at = v1_end  # V.CCV for legal onset/digraph ('dou.ble', 'fa.ther')
            elif len(cons) >= 3 and cons[-2:] in legal_onsets:
                split_at = v2_start - 2
            else:
                split_at = v2_start - 1  # VC.CV ('tel.len', 'sor.we', 'hel.peth')
            syllables.append(working[start_idx:split_at])
            start_idx = split_at
        syllables.append(working[start_idx:])
        return syllables

    def _assign_stress(
        self, word: str, orth_sylls: list[str], word_class: WordClass
    ) -> list[int]:
        """Assign Middle English lexical stress across syllables."""
        m = len(orth_sylls)
        if m == 1:
            return [0 if word_class == WordClass.FUNCTION else 1]

        # Compound / prefixed forms with explicit hyphen ('y-be', 'him-self', 'but-if')
        if "-" in word:
            first_part = word.split("-", 1)[0]
            if first_part in {"y", "i", "be", "bi", "for", "to", "un", "but", "him", "hym", "ther", "wher"}:
                st = [0] * m
                st[1] = 1
                return st

        # Unhyphenated unstressed verbal prefixes ('forsook', 'forbede', 'biholden', 'acorde')
        if (
            word.startswith(("for", "bi", "be"))
            and m >= 2
            and word not in {"forme", "ferme", "brother", "bernard", "bokes", "bote"}
        ):
            st = [0] * m
            st[1] = 1
            return st

        if word.startswith("a") and len(orth_sylls[0]) <= 2 and word in {"assay", "acorde", "avaunt", "aboute", "agayn", "amonge", "allone"}:
            st = [0] * m
            st[1] = 1
            return st

        # Default Germanic root-initial primary stress
        st = [1] + [0] * (m - 1)
        if m >= 4:
            st[-2 if orth_sylls[-1].endswith("e") else -1] = 2
        return st

    @staticmethod
    def _ends_in_vowel_grapheme(orth_s: str) -> bool:
        return bool(orth_s) and orth_s[-1] in VOWEL_CHARS

    def _transcribe_syllable(
        self, orth_s: str, is_stressed: bool, is_open: bool, is_final: bool
    ) -> tuple[str, str | None]:
        """Map an orthographic Middle English syllable to pre-GVS IPA."""
        s = orth_s
        if s == "ë":
            return "ə", None

        # Handle unstressed final schwa syllables (-e, -es, -ed, -en, -eth, -er, -el)
        if not is_stressed and is_final:
            for suf, ipa_suf in (
                ("eth", "əθ"), ("es", "əs"), ("en", "ən"), ("ed", "əd"), ("er", "ər"), ("el", "əl"), ("e", "ə"),
            ):
                if s.endswith(suf) and not s.endswith(("ee", "ie", "ye")) or (s in {"ye", "the", "ne", "me", "he", "she", "be", "we"} and False):
                    onset = s[: -len(suf)]
                    # Guard monosyllabic open pronouns ('he', 'me', 'she', 'ye', 'we', 'be')
                    if onset in {"h", "m", "sh", "y", "w", "b"} and suf == "e" and len(s) <= 3:
                        if s in {"the", "ne"}:
                            return self._transcribe_consonants(onset) + "ə", None
                        return self._transcribe_consonants(onset) + "eː", "close_e"
                    return self._transcribe_consonants(onset) + ipa_suf, None

        # Locate vocalic nucleus inside syllable
        digraph_map: list[tuple[str, str, str | None]] = [
            ("ee", "eː", "close_e"),
            ("oo", "oː", "close_o"),
            ("aa", "aː", None),
            ("ai", "ɛi", None),
            ("ay", "ɛi", None),
            ("ei", "ɛi", None),
            ("ey", "ɛi", None),
            ("oi", "ɔi", None),
            ("oy", "ɔi", None),
            ("au", "au", None),
            ("aw", "au", None),
            ("eu", "iu", None),
            ("ew", "iu", None),
        ]

        # Special check: 'ou'/'ow' before 'gh' is [ɔu], otherwise [uː]
        for dg in ("ou", "ow"):
            if dg in s:
                idx = s.index(dg)
                onset = s[:idx]
                coda = s[idx + 2 :]
                nuc = "ɔu" if coda.startswith("gh") else "uː"
                return (
                    self._transcribe_consonants(onset)
                    + nuc
                    + self._transcribe_coda(coda, front_vowel=False),
                    None,
                )

        for dg, ipa_v, qual in digraph_map:
            if dg in s:
                idx = s.index(dg)
                onset = s[:idx]
                coda = s[idx + len(dg) :]
                front = dg in {"ee", "ei", "ey", "ai", "ay"}
                return (
                    self._transcribe_consonants(onset)
                    + ipa_v
                    + self._transcribe_coda(coda, front_vowel=front),
                    qual,
                )

        # Single-letter vowel nucleus
        m = re.search(r"[aeiouy]", s if not s.startswith("y") else ("J" + s[1:]))
        if not m:
            return self._transcribe_consonants(s), None
        idx = m.start()
        v_ch = s[idx]
        onset = s[:idx]
        coda = s[idx + 1 :]

        # Open-syllable lengthening or word-final stressed open monosyllable
        lengthen = is_stressed and (is_open or (is_final and coda == ""))
        qual = None
        if v_ch == "a":
            ipa_v = "aː" if lengthen else "a"
        elif v_ch == "e":
            if not is_stressed and coda == "":
                ipa_v = "ə"
            elif lengthen:
                ipa_v = "ɛː"
                qual = "open_e"
            else:
                ipa_v = "ɛ"
        elif v_ch in {"i", "y"}:
            ipa_v = "iː" if lengthen else "i"
        elif v_ch == "o":
            if lengthen:
                ipa_v = "ɔː"
                qual = "open_o"
            else:
                ipa_v = "ɔ"
        else:  # 'u'
            ipa_v = "iu" if lengthen else "u"

        front_v = v_ch in {"e", "i", "y"}
        return (
            self._transcribe_consonants(onset)
            + ipa_v
            + self._transcribe_coda(coda, front_vowel=front_v),
            qual,
        )

    @staticmethod
    def _transcribe_consonants(cluster: str) -> str:
        """Transcribe Middle English onset consonants (preserving sounded kn-, gn-, wr-, wh-)."""
        if not cluster:
            return ""
        c = cluster
        c = c.replace("sch", "ʃ").replace("sh", "ʃ").replace("ch", "tʃ")
        c = c.replace("th", "θ").replace("wh", "ʍ").replace("qu", "kw").replace("ph", "f")
        if c.startswith("y"):
            c = "j" + c[1:]
        c = c.replace("c", "k")
        return c

    @staticmethod
    def _transcribe_coda(cluster: str, front_vowel: bool) -> str:
        """Transcribe Middle English coda consonants (distinguishing [ç] vs [x] for 'gh')."""
        if not cluster:
            return ""
        c = cluster
        c = c.replace("gh", "ç" if front_vowel else "x")
        c = c.replace("sch", "ʃ").replace("sh", "ʃ").replace("ch", "tʃ")
        c = c.replace("th", "θ").replace("ng", "ŋg").replace("nk", "ŋk")
        c = c.replace("ck", "k").replace("c", "k")
        return c
