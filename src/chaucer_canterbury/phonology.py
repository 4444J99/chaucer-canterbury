"""Late-14th-century London Middle English grapheme-to-phoneme (G2P) transcriber."""

from __future__ import annotations

import re

from chaucer_canterbury.lexicon import (
    CLOSE_E_STEMS,
    CLOSE_O_STEMS,
    MEDLexicon,
    OPEN_E_STEMS,
    OPEN_O_STEMS,
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

#Romance / Anglo-Norman suffixes admitting right-edge or penultimate stress in Chaucer
ROMANCE_STRESS_SUFFIXES = (
    "ioun", "iouns", "oun", "ouns", "itee", "itees", "ite", "ites", "tee", "tees", "ee", "ees",
    "aunce", "aunces", "ance", "ances", "ence", "ences", "ent", "ents", "ente", "aille", "ailles",
    "esse", "esses", "our", "ours", "ure", "ures", "age", "ages", "ous",
    "eys", "ais", "eit", "eyt", "aunt", "ant", "une", "unes", "ene", "one", "ones",
    "ace", "aces", "aceth", "aced",
    "yne", "ine", "yse", "ise", "able", "ible", "al", "er", "ere",
    "eres", "ye", "ie", "eyn", "ayn", "ein", "ain", "ort", "aat", "at", "as",
    "u", "ue", "ille", "oine", "oyne", "oint", "oynt",
    "lees", "heed", "lok", "mest", "oon", "on", "ons",
)

# Closed/heavy 3+ syllable oxytones and Romance/native compounds with final primary beat (2-0-1)
OXYTONE_TRISYLLABLES = frozenset(
    {
        "everichon", "everichoon", "forthermore", "nathelees", "natheles", "heer-up-on",
        "ther-up-on", "everywhere", "verrayment", "tourneyment", "payndemayn",
        "habergeoun", "condicioun", "religioun", "opinioun", "devocioun",
        "cloisterlees", "waterlees", "wastel-breed", "pilgrimages", "officeres",
    }
)

# Prefixes taking unstressed initial syllable (0-1...)
IAMBIC_A_WORDS = frozenset(
    {
        "anon", "anoon", "echoon", "almest", "alone", "allone", "alyve", "aright", "aboute", "agayn", "ageyn",
        "among", "amonge", "almost", "also", "alwey", "assente", "assenten",
        "assure", "assureth", "acorde", "array", "aryve", "avaunt", "abyde",
        "anoint", "another", "amiable", "apothecaries", "aprille",
    }
)

NON_PREFIX_BE_FOR = frozenset(
    {
        "forme", "ferme", "forster", "forward", "forheed", "fortune",
        "brother", "bernard", "bokes", "bote", "beste", "bedde", "bedes",
        "belle", "bere", "bete", "bene", "beye", "berye", "beeste",
        "belmarye", "beneit", "bothe",
    }
)


class MiddleEnglishTranscriber:
    """Transcribes Middle English words into pre-Great-Vowel-Shift London IPA lattices."""

    def __init__(self, lexicon: MEDLexicon | None = None) -> None:
        self.lexicon = lexicon or MEDLexicon()

    def tokenize_line(self, line: str) -> list[tuple[str, str]]:
        """Split a Middle English verse line into (word_token, trailing_punctuation) pairs."""
        # Protect word-internal apostrophes ('t'endite', 'th'array', 'n'is'), strip speech quotes & italics '_'
        protected = re.sub(r"(?<=[A-Za-z])'(?=[A-Za-z])", "\uE000", line.strip())
        cleaned = re.sub(r"[†*°_\"“”‘’'()\[\]]", "", protected)
        cleaned = cleaned.replace("\uE000", "'")
        raw_parts = re.findall(r"[A-Za-zȝþðëé'-]+|[,.;:!?—–]+", cleaned)
        tokens: list[tuple[str, str]] = []
        for part in raw_parts:
            if re.match(r"^[,.;:!?—–]+$", part):
                if tokens:
                    prev_word, prev_punct = tokens[-1]
                    tokens[-1] = (prev_word, prev_punct + part)
            else:
                word_clean = part.strip("'-")
                if word_clean:
                    tokens.append((word_clean, ""))
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
            variants = self._variants_from_lexicon_entry(entry, final_e_class, norm=norm)
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

        variants, inferred_quality = self._rule_based_g2p(
            norm, word_class, final_e_class, is_proper=(bool(surface) and surface[0].isupper())
        )
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
        # Scribal 'i' before a vowel ('iuste', 'ioie', 'iuge') is palatal/affricate [dʒ], NOT a vowel
        if norm.startswith("i") and len(norm) > 1 and norm[1] in {"a", "e", "o", "u"}:
            return False
        # 'y' before a vowel is palatal approximant [j] ('ye', 'yit', 'yow'), NOT a vowel
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
        self, entry: dict, final_e_class: FinalEClass, norm: str = ""
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
        _LEX_DIALECT_DOUBLETS = {
            "sene": ("ˈsɛː.nə", "10", 0.14),
            "drede": ("ˈdreː.də", "10", 0.16),
            "slepe": ("ˈslɛː.pə", "10", 0.16),
            "see": ("ˈseː", "1", 0.18),
        }
        if norm in _LEX_DIALECT_DOUBLETS:
            d_ipa, d_st, d_cost = _LEX_DIALECT_DOUBLETS[norm]
            if all(v.ipa != d_ipa for v in variants):
                d_sylls = self._parse_ipa_and_stress(d_ipa, d_st, final_e_class)
                variants.append(
                    PhonologicalVariant(
                        ipa=d_ipa,
                        syllables=d_sylls,
                        stress_pattern=d_st,
                        cost=d_cost,
                        note="dialect_mid_vowel_doublet",
                    )
                )
        # Adjectives/adverbs in '-y' / '-ly' in S4 ('worthy', 'redy', 'holy') admit right-edge rhyme stress [-ˈiː]
        if len(base_sylls) >= 2 and norm.endswith("y") and base_sylls[-1].ipa.endswith(("i", "iː")):
            y_sylls = [s.model_copy() for s in base_sylls]
            for sy in y_sylls:
                sy.stress = 0
                sy.is_final_schwa = False
            y_sylls[-1].stress = 1
            if not y_sylls[-1].ipa.endswith("iː") and y_sylls[-1].ipa.endswith("i"):
                y_sylls[-1].ipa = y_sylls[-1].ipa[:-1] + "iː"
            k = len(y_sylls) - 3
            while k >= 0:
                y_sylls[k].stress = 2
                k -= 2
            y_st_str = "".join(str(sy.stress) for sy in y_sylls)
            y_ipa_str = ".".join(
                f"ˈ{sy.ipa}" if sy.stress == 1 else (f"ˌ{sy.ipa}" if sy.stress == 2 else sy.ipa)
                for sy in y_sylls
            )
            if all(v.ipa != y_ipa_str for v in variants):
                variants.append(
                    PhonologicalVariant(
                        ipa=y_ipa_str,
                        syllables=y_sylls,
                        stress_pattern=y_st_str,
                        cost=0.14,
                        note="lexicon_rhyme_y_stress",
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

    def _build_variant_from_orth(
        self,
        orth_sylls: list[str],
        stresses: list[int],
        proclitic_prefix: str,
        final_e_class: FinalEClass,
        norm: str,
        cost: float,
        note: str,
    ) -> tuple[PhonologicalVariant, str | None]:
        """Transcribe orthographic syllables under a specific stress vector."""
        ipa_sylls: list[str] = []
        vowel_quality: str | None = None
        num_sylls = len(orth_sylls)
        for idx, (orth_s, st) in enumerate(zip(orth_sylls, stresses)):
            is_open = idx < num_sylls - 1 and self._ends_in_vowel_grapheme(orth_s)
            s_ipa, v_qual = self._transcribe_syllable(
                orth_s,
                is_stressed=(st > 0),
                is_open=is_open,
                is_final=(idx == num_sylls - 1),
                is_monosyllable=(num_sylls == 1),
                whole_word=norm,
                is_primary_stress=(st == 1),
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
        parsed_sylls = self._parse_ipa_and_stress(formatted_ipa, stress_str, final_e_class)
        return (
            PhonologicalVariant(
                ipa=formatted_ipa,
                syllables=parsed_sylls,
                stress_pattern=stress_str,
                cost=cost,
                note=note,
            ),
            vowel_quality,
        )

    def _rule_based_g2p(
        self,
        norm: str,
        word_class: WordClass,
        final_e_class: FinalEClass,
        is_proper: bool = False,
    ) -> tuple[list[PhonologicalVariant], str | None]:
        """Deterministic pre-GVS London Middle English syllabifier and IPA transcriber."""
        # Scribal 'u' -> 'v' between vowels ('loue' -> 'love') and scribal 'i' -> 'j' before vowels ('iuste' -> 'juste', 'reioysed' -> 'rejoysed')
        work = re.sub(r"([aeiouy])u([aeiouyë])", r"\1v\2", norm)
        work = re.sub(r"^i([aeou])", r"j\1", work)
        work = re.sub(r"([aeiouy])i([aeiou])", r"\1j\2", work)

        # Proclitic contractions like "t'endite" or "th'array"
        proclitic_prefix = ""
        if "'" in work:
            parts = work.split("'", 1)
            if parts[0] in {"t", "th", "n"} and parts[1]:
                proclitic_prefix = {"t": "t", "th": "ð", "n": "n"}[parts[0]]
                work = parts[1]

        orth_sylls = self._syllabify_orthography(work, final_e_class)
        stresses = self._assign_stress(work, orth_sylls, word_class)

        base_var, vowel_quality = self._build_variant_from_orth(
            orth_sylls=orth_sylls,
            stresses=stresses,
            proclitic_prefix=proclitic_prefix,
            final_e_class=final_e_class,
            norm=norm,
            cost=0.0,
            note="rule_canonical",
        )
        variants: list[PhonologicalVariant] = [base_var]
        seen_sigs: set[tuple[str, str]] = {(base_var.ipa, base_var.stress_pattern)}

        def _add_var(v: PhonologicalVariant) -> None:
            sig = (v.ipa, v.stress_pattern)
            if sig not in seen_sigs:
                seen_sigs.add(sig)
                variants.append(v)

        base_syllables = base_var.syllables

        # Add documented Anglian/Saxon/Kentish mid-vowel doublets at modest dialect cost
        _DIALECT_DOUBLET_MAP = {
            "sene": ("ˈsɛː.nə", "10", 0.14),
            "drede": ("ˈdreː.də", "10", 0.16),
            "slepe": ("ˈslɛː.pə", "10", 0.16),
            "see": ("ˈseː", "1", 0.18),
        }
        if norm in _DIALECT_DOUBLET_MAP:
            d_ipa, d_st, d_cost = _DIALECT_DOUBLET_MAP[norm]
            d_sylls = self._parse_ipa_and_stress(d_ipa, d_st, final_e_class)
            _add_var(
                PhonologicalVariant(
                    ipa=d_ipa,
                    syllables=d_sylls,
                    stress_pattern=d_st,
                    cost=d_cost,
                    note="dialect_mid_vowel_doublet",
                )
            )

        # Add optional apocope variant for high-frequency variable words
        if (
            final_e_class == FinalEClass.OPTIONAL_APOCOPE
            or norm in OPTIONAL_APOCOPE_WORDS
        ) and len(base_syllables) >= 2 and base_syllables[-1].ipa.endswith("ə"):
            apoc_sylls = self._build_apocopated_syllables(base_syllables)
            if apoc_sylls:
                apoc_st = "".join(str(s.stress) for s in apoc_sylls)
                apoc_ipa = ".".join(
                    f"ˈ{s.ipa}" if s.stress == 1 else (f"ˌ{s.ipa}" if s.stress == 2 else s.ipa)
                    for s in apoc_sylls
                )
                _add_var(
                    PhonologicalVariant(
                        ipa=apoc_ipa,
                        syllables=apoc_sylls,
                        stress_pattern=apoc_st,
                        cost=0.10,
                        note="rule_optional_apocope",
                    )
                )

        # Add Romance / Anglo-Norman <-> Germanic stress alternation (re-transcribing under shifted stress!)
        if len(orth_sylls) >= 2 and (
            (work.endswith(ROMANCE_STRESS_SUFFIXES) and work not in {"forster", "miller", "reve", "palmer", "palmers", "water", "fader", "moder", "brother", "sister", "silver", "winter", "sommer", "after", "under", "over", "other", "ever", "never", "neither", "either", "wonder", "thunder"})
            or "-" in work
            or stresses[0] == 0
        ):
            alt_candidates: list[list[int]] = []
            # Right-edge stress (or penultimate before final unstressed -e/-es/-en/-ed)
            ends_unstressed_infl = orth_sylls[-1].endswith(("e", "es", "en", "ed", "eth")) and not orth_sylls[-1].endswith(("ee", "ie", "ye", "eed", "ees", "een", "eer", "eel", "eeth"))
            if ends_unstressed_infl and len(orth_sylls) >= 3:
                alt_r = [0] * (len(orth_sylls) - 2) + [1, 0]
                k = len(orth_sylls) - 4
                while k >= 0:
                    alt_r[k] = 2
                    k -= 2
                alt_candidates.append(alt_r)
            elif not ends_unstressed_infl:
                alt_r = [0] * (len(orth_sylls) - 1) + [1]
                k = len(orth_sylls) - 3
                while k >= 0:
                    alt_r[k] = 2
                    k -= 2
                alt_candidates.append(alt_r)

            # Root-initial Germanic stress counterpart when base was right-edge/iambic
            if stresses[0] != 1:
                alt_g = [1] + [0] * (len(orth_sylls) - 1)
                if len(orth_sylls) >= 3 and not ends_unstressed_infl:
                    alt_g[-1] = 2
                alt_candidates.append(alt_g)

            for alt_st in alt_candidates:
                if alt_st != stresses:
                    alt_var, _ = self._build_variant_from_orth(
                        orth_sylls=orth_sylls,
                        stresses=alt_st,
                        proclitic_prefix=proclitic_prefix,
                        final_e_class=final_e_class,
                        norm=norm,
                        cost=0.12,
                        note="stress_doublet",
                    )
                    _add_var(alt_var)

        # Medial unstressed vowel syncope in 3+ syllable words (e.g., 'Engelond', 'Caunterbury', 'sovereyn', 'bokeler', 'considereth')
        if len(orth_sylls) >= 3:
            for st_vec in ([stresses] + ([ [2, 0, 1] ] if len(orth_sylls) == 3 and work.endswith(ROMANCE_STRESS_SUFFIXES) else [])):
                for mid_idx in range(1, len(orth_sylls) - 1):
                    mid_s = orth_sylls[mid_idx]
                    if (
                        st_vec[mid_idx] == 0
                        and len(mid_s) <= 3
                        and not any(dg in mid_s for dg in ("ee", "oo", "aa", "ou", "ow", "au", "ai", "ay", "ei", "ey", "oi", "oy"))
                    ):
                        cons_only = re.sub(r"[aeiouyëé]", "", mid_s)
                        sync_orth = (
                            orth_sylls[: mid_idx - 1]
                            + [orth_sylls[mid_idx - 1] + cons_only]
                            + orth_sylls[mid_idx + 1 :]
                        )
                        sync_st = st_vec[:mid_idx] + st_vec[mid_idx + 1 :]
                        if 1 not in sync_st and sync_st:
                            sync_st[0] = 1
                        sync_var, _ = self._build_variant_from_orth(
                            orth_sylls=sync_orth,
                            stresses=sync_st,
                            proclitic_prefix=proclitic_prefix,
                            final_e_class=final_e_class,
                            norm=norm,
                            cost=0.14,
                            note="medial_syncope",
                        )
                        _add_var(sync_var)
                        break

        # Optional inflectional syncope in 2+ syllable words ending in unstressed -eth, -ed, -en, -er, -el, -es
        if (
            len(orth_sylls) >= 2
            and stresses[-1] == 0
            and orth_sylls[-1].endswith(("eth", "ed", "en", "er", "el", "es"))
            and not orth_sylls[-1].endswith(("ees", "eed", "een", "eer", "eel", "eeth", "ges", "ches", "shes", "ces", "ses", "zes"))
            and norm not in {"shoures", "floures", "lordes", "bedes", "songes", "thinges", "eres"}
        ):
            coda_tail = re.sub(r"e(?=th$|d$|n$|r$|l$|s$)", "", orth_sylls[-1])
            merged_orth = orth_sylls[:-2] + [orth_sylls[-2] + coda_tail]
            merged_st = stresses[:-1]
            if 1 not in merged_st and merged_st:
                merged_st[0] = 1
            sync_var, _ = self._build_variant_from_orth(
                orth_sylls=merged_orth,
                stresses=merged_st,
                proclitic_prefix=proclitic_prefix,
                final_e_class=FinalEClass.NONE,
                norm=norm,
                cost=0.18,
                note="inflectional_syncope",
            )
            _add_var(sync_var)

        # Adjectives/adverbs in '-y' / '-ly' ('worthy', 'fetisly', 'prively', 'redily') admit rhyme-beat [-ˈiː]
        if len(orth_sylls) >= 2 and orth_sylls[-1].endswith("y") and word_class == WordClass.CONTENT:
            y_st = [0] * len(orth_sylls)
            y_st[-1] = 1
            k = len(orth_sylls) - 3
            while k >= 0:
                y_st[k] = 2
                k -= 2
            if y_st != stresses:
                y_var, _ = self._build_variant_from_orth(
                    orth_sylls=orth_sylls,
                    stresses=y_st,
                    proclitic_prefix=proclitic_prefix,
                    final_e_class=final_e_class,
                    norm=norm,
                    cost=0.14,
                    note="rhyme_y_stress",
                )
                _add_var(y_var)

        # Classical/Romance proper names in '-es' ('Saluces', 'Socrates', 'Hercules') admit secondary stress [-ɛs]
        if is_proper and len(orth_sylls) >= 3 and orth_sylls[-1].endswith("es"):
            prop_st = [1] + [0] * (len(orth_sylls) - 2) + [2]
            prop_var, _ = self._build_variant_from_orth(
                orth_sylls=orth_sylls,
                stresses=prop_st,
                proclitic_prefix=proclitic_prefix,
                final_e_class=FinalEClass.NONE,
                norm=norm,
                cost=0.08,
                note="classical_proper_name_es",
            )
            _add_var(prop_var)

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

        # Romance/abstract or post-consonantal '-ye' / '-ie' at word end is disyllabic [-iː.ə] ('gye', 'hye', 'melodye', 'curteisye')
        if (
            len(working) >= 3
            and working.endswith(("ye", "ie"))
            and not working.endswith(("eye", "aye", "oye", "uye"))
        ):
            stem_part = working[:-1]
            stem_sylls = self._syllabify_orthography(stem_part, FinalEClass.NONE)
            return stem_sylls + ["e"]

        # Identify vowel nucleus spans (treating digraphs as single vocalic nuclei)
        spans: list[tuple[int, int]] = []
        i = 0
        n = len(working)
        digraph_vowels = {
            "aa", "ee", "oo", "ou", "ow", "au", "aw", "ai", "ay", "ei", "ey", "oi", "oy", "eu", "ew",
        }
        while i < n:
            ch = working[i]
            # Treat 'y' before a vowel ONLY word-initially or post-vocalically (excluding 'qu') as consonantal glide [j]; after a consonant ('squyer', 'thryes', 'lyeys') 'y' is vocalic!
            is_glide_y = (
                ch == "y"
                and (
                    i == 0
                    or (
                        working[i - 1] in VOWEL_CHARS
                        and not (i >= 2 and working[i - 2 : i] == "qu")
                    )
                )
                and i + 1 < n
                and working[i + 1] in VOWEL_CHARS
            )
            is_qu_glide = ch == "u" and i > 0 and working[i - 1] == "q" and i + 1 < n and working[i + 1] in VOWEL_CHARS
            is_v = (ch in VOWEL_CHARS) and not is_glide_y and not is_qu_glide
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
            "ch", "sh", "th", "wh", "gh", "qu", "sch", "squ",
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
                split_at = v1_end  # V.CV open syllable ('ta.le', 'so.re')
            elif cons in legal_onsets:
                split_at = v1_end  # V.CCV for legal onset/digraph ('dou.ble', 'fa.ther')
            elif len(cons) >= 3 and cons[-3:] in legal_onsets:
                split_at = v2_start - 3
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

        clean_w = word.replace("-", "")
        if word in OXYTONE_TRISYLLABLES or clean_w in OXYTONE_TRISYLLABLES:
            st = [0] * m
            if orth_sylls[-1].endswith("e") and not orth_sylls[-1].endswith(("ee", "ie", "ye")) and m >= 4:
                p_idx = m - 2
            else:
                p_idx = m - 1
            st[p_idx] = 1
            k = p_idx - 2
            while k >= 0:
                st[k] = 2
                k -= 2
            return st

        # Compound / prefixed forms with explicit hyphen ('y-be', 'him-self', 'ther-on', 'in-to', 'up-on')
        if "-" in word:
            first_part = word.split("-", 1)[0]
            if first_part in {
                "y", "i", "be", "bi", "for", "to", "un", "but", "him", "hym",
                "ther", "wher", "with", "up", "in", "na",
            }:
                st = [0] * m
                st[1] = 1
                return st

        # Prepositions/adverbs/verbs in 'up-', 'in-', 'un-', 'with-', 'namo*'
        if word in {"upon", "into", "unto", "namo", "namore", "therfore", "wherfor", "wherfore", "withalle"}:
            st = [0] * m
            st[1] = 1
            return st

        # Romance / Latin verbal prefixes ('engendred', 'endyte', 'escapeth', 'estaat', 'disport', 'disdeyne', 'divyne', 'requeste', 'reserved', 'rejoysed', 'purveye', 'purtreye', 'obeye', 'comandement', 'comaundeth', 'considereth', 'deliver')
        if (
            word.startswith(("en", "em", "es", "ex", "dis", "de", "re", "pur", "ob", "com", "con", "un", "bi", "be", "for"))
            and m >= 2
            and word not in NON_PREFIX_BE_FOR
            and not word.startswith(("engl", "enny", "ent", "ert", "est", "even", "ever"))
            or word in {"entent", "entente", "estaat", "estat", "estatlich"}
        ):
        # Guard root nouns/adjectives like 'redy', 'service', 'reverence', 'diligence', 'conscience', 'resoun', 'companye'
            if word not in {
                "redy", "companye", "commune", "conscience", "reverence", "reverently",
                "diligence", "resoun", "remembraunce", "reule", "rede", "reste", "forster",
            }:
                st = [0] * m
                st[1] = 1
                if m >= 4 and not orth_sylls[-1].endswith("e"):
                    st[-1] = 2
                return st

        if word in IAMBIC_A_WORDS:
            st = [0] * m
            st[1] = 1
            return st

        # Polysyllabic '-ye' / '-ie' abstract nouns ('melodye', 'hostelrye', 'chivachye', 'curteisye', 'vileinye', 'maistrye')
        if m >= 3 and orth_sylls[-1] == "e" and orth_sylls[-2].endswith(("y", "i")):
            st = [0] * m
            st[-2] = 1
            k = m - 4
            while k >= 0:
                st[k] = 2
                k -= 2
            return st

        # Default Germanic root-initial primary stress, with secondary stress on heavy final/penultimate syllable
        st = [1] + [0] * (m - 1)
        ends_schwa = orth_sylls[-1].endswith(("e", "es", "en", "ed", "eth")) and not orth_sylls[-1].endswith(("ee", "ie", "ye", "eed", "ees", "een", "eer", "eel", "eeth"))
        if m == 2 and not ends_schwa and len(orth_sylls[1]) >= 3 and word_class == WordClass.CONTENT:
            # Heavy closed second syllable in compounds ('wedlok', 'forheed', 'verray', 'scarlet')
            st[1] = 2
        elif m == 3 and not ends_schwa:
            st[2] = 2
        elif m >= 4:
            st[-2 if ends_schwa else -1] = 2
        return st

    @staticmethod
    def _ends_in_vowel_grapheme(orth_s: str) -> bool:
        return bool(orth_s) and orth_s[-1] in VOWEL_CHARS

    def _transcribe_syllable(
        self,
        orth_s: str,
        is_stressed: bool,
        is_open: bool,
        is_final: bool,
        is_monosyllable: bool = False,
        whole_word: str = "",
        is_primary_stress: bool = False,
    ) -> tuple[str, str | None]:
        """Map an orthographic Middle English syllable to pre-GVS IPA."""
        s = orth_s
        if s in {"ë", "e"} and is_final and not is_monosyllable and not is_stressed:
            return "ə", None
        if s == "ë":
            return "ə", None

        # Monosyllabic schwa particles ('the', 'ne')
        if is_monosyllable and whole_word in {"the", "ne"}:
            onset = s[:-1]
            return self._transcribe_consonants(onset) + "ə", None

        # French '-age' / '-ages' suffix ('corage', 'corages', 'pilgrimages', 'mariage', 'servage', 'usage')
        if is_final and not is_monosyllable and s in {"ge", "ges"} and whole_word.endswith(("age", "ages")):
            return ("dʒə" if s == "ge" else "dʒəs"), None

        # Handle unstressed final schwa syllables ONLY in polysyllables (-e, -es, -ed, -en, -eth, -er, -el)
        if not is_stressed and is_final and not is_monosyllable:
            for suf, ipa_suf in (
                ("eth", "əθ"), ("es", "əs"), ("ed", "əd"), ("en", "ən"), ("er", "ər"), ("el", "əl"), ("e", "ə"),
            ):
                if s.endswith(suf) and not s.endswith(("ee", "ie", "ye", "eed", "ees", "een", "eer", "eel", "eeth")):
                    onset = s[: -len(suf)]
                    return self._transcribe_consonants(onset, next_front=True) + ipa_suf, None

        # Historical open vs. close mid-vowel override on primary-stressed rhyme stem
        forced_mid: tuple[str, str] | None = None
        if is_primary_stress or is_monosyllable:
            if whole_word in CLOSE_E_STEMS:
                forced_mid = ("eː", "close_e")
            elif whole_word in OPEN_E_STEMS:
                forced_mid = ("ɛː", "open_e")
            elif whole_word in CLOSE_O_STEMS:
                forced_mid = ("oː", "close_o")
            elif whole_word in OPEN_O_STEMS:
                forced_mid = ("ɔː", "open_o")

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

        # Special check: 'ou'/'ow' before 'gh' or final/open 'ow(e)' diphthongs ('trowe', 'lowe', 'knowe', 'bowe', 'fowel') vs [uː]
        for dg in ("ou", "ow"):
            if dg in s:
                idx = s.index(dg)
                onset = s[:idx]
                coda = s[idx + 2 :]
                if coda.startswith("gh") or (
                    dg == "ow"
                    and whole_word.endswith(("owe", "ow"))
                    and whole_word not in {"how", "now", "thow", "yow", "cow", "brow", "vow", "avow", "prow", "alow"}
                ):
                    nuc = "ɔu"
                else:
                    nuc = "uː"
                return (
                    self._transcribe_consonants(onset, next_front=False)
                    + nuc
                    + self._transcribe_coda(coda, front_vowel=False),
                    None,
                )

        for dg, ipa_v, qual in digraph_map:
            if dg in s:
                idx = s.index(dg)
                onset = s[:idx]
                coda = s[idx + len(dg) :]
                if forced_mid and dg in {"ee", "oo"}:
                    ipa_v, qual = forced_mid
                front = dg in {"ee", "ei", "ey", "ai", "ay"}
                return (
                    self._transcribe_consonants(onset, next_front=front)
                    + ipa_v
                    + self._transcribe_coda(coda, front_vowel=front),
                    qual,
                )

        # Single-letter vowel nucleus (guard 'y' onset and 'qu' labialized velar onset)
        masked = s
        if masked.startswith("y") and len(masked) > 1 and masked[1] in VOWEL_CHARS:
            masked = "J" + masked[1:]
        masked = re.sub(r"(?<=q)u(?=[aeiouy])", "W", masked)
        m = re.search(r"[aeiouy]", masked)
        if not m:
            return self._transcribe_consonants(s), None
        idx = m.start()
        v_ch = s[idx]
        onset = s[:idx]
        coda = s[idx + 1 :]

        # Open-syllable lengthening, '-age(s)' penultimate 'a', Romance '-as'/'-at', or word-final stressed open syllable
        lengthen = is_stressed and (is_open or (is_final and coda == ""))
        if v_ch == "a" and coda == "" and whole_word.endswith(("age", "ages")):
            lengthen = True
        if (
            v_ch == "a"
            and is_final
            and is_stressed
            and (
                whole_word in {"cas", "pas", "las", "solas", "allas", "purchas", "trespas", "compas"}
                or (not is_monosyllable and coda in {"s", "t"} and whole_word.endswith(("as", "at")) and whole_word not in {"what", "that", "flat", "was", "nas"})
            )
        ):
            lengthen = True
        qual = None
        if forced_mid and v_ch in {"e", "o"} and (is_primary_stress or is_monosyllable):
            ipa_v, qual = forced_mid
        elif v_ch == "a":
            ipa_v = "aː" if lengthen else "a"
        elif v_ch == "e":
            if not is_stressed and coda == "" and not is_monosyllable:
                ipa_v = "ə"
            elif lengthen:
                ipa_v = "ɛː"
                qual = "open_e"
            else:
                ipa_v = "ɛ"
        elif v_ch in {"i", "y"}:
            ipa_v = "iː" if (lengthen or (is_final and coda == "" and v_ch == "y" and whole_word.endswith("ye"))) else "i"
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
            self._transcribe_consonants(onset, next_front=front_v)
            + ipa_v
            + self._transcribe_coda(coda, front_vowel=front_v),
            qual,
        )

    @staticmethod
    def _transcribe_consonants(cluster: str, next_front: bool = False) -> str:
        """Transcribe Middle English onset consonants (preserving kn-, gn-, wr-, wh-, soft c/g, and j)."""
        if not cluster:
            return ""
        c = cluster
        c = c.replace("sch", "ʃ").replace("sh", "ʃ").replace("ch", "tʃ")
        c = c.replace("th", "θ").replace("wh", "ʍ").replace("qu", "kw").replace("ph", "f")
        c = c.replace("j", "dʒ")
        if c.startswith("y"):
            c = "j" + c[1:]
        if next_front and c.endswith("c"):
            c = c[:-1] + "s"
        c = c.replace("c", "k")
        return c

    @staticmethod
    def _transcribe_coda(cluster: str, front_vowel: bool) -> str:
        """Transcribe Middle English coda consonants (distinguishing [ç] vs [x] for 'gh' and soft 'ce')."""
        if not cluster:
            return ""
        c = cluster
        c = c.replace("gh", "ç" if front_vowel else "x")
        c = c.replace("sch", "ʃ").replace("sh", "ʃ").replace("ch", "tʃ")
        c = c.replace("th", "θ").replace("ng", "ŋg").replace("nk", "ŋk")
        c = c.replace("ck", "k").replace("j", "dʒ")
        c = c.replace("c", "k")
        return c
