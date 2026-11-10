"""Stratum S4 Middle English Dictionary (MED) lexicon loader and L1 chronological gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from chaucer_canterbury.models import FinalEClass, WordClass

DEFAULT_LEXICON_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "s4_lexicon" / "core_med_lexicon.json"
)

# Closed-class Middle English function words (monosyllables & light disyllables)
FUNCTION_WORDS: frozenset[str] = frozenset(
    {
        "a", "al", "als", "also", "am", "an", "and", "any", "art", "as", "at",
        "be", "been", "ben", "beth", "but", "but-if", "by", "can", "dar",
        "did", "dide", "do", "don", "doth", "dooth", "ech", "either", "eyther",
        "elles", "er", "ere", "every", "for", "fro", "ffro", "from", "gan",
        "had", "hadde", "han", "hath", "haue", "have", "he", "hem", "her",
        "hir", "hire", "his", "hit", "how", "hym", "him", "him-self", "hym-self",
        "i", "if", "in", "into", "is", "ys", "it", "kan", "mai", "may", "me",
        "men", "mi", "min", "mo", "moot", "moste", "my", "myn", "na", "nas",
        "nat", "natheles", "ne", "ner", "never", "nis", "nys", "no", "non",
        "noon", "nor", "not", "now", "o", "of", "on", "oon", "or", "other",
        "ough", "oghte", "our", "oure", "out", "right", "sal", "shal", "she",
        "sholde", "shul", "shulde", "sin", "sithen", "so", "som", "swich",
        "than", "thanne", "that", "the", "thee", "then", "ther", "there",
        "ther-as", "ther-fore", "ther-to", "these", "they", "thi", "thin",
        "this", "thise", "tho", "thogh", "though", "thow", "thou", "thurgh",
        "thus", "thy", "thyn", "til", "to", "un-to", "unto", "up", "up-on",
        "upon", "us", "was", "we", "wel", "were", "what", "whan", "wher",
        "where", "which", "whiche", "whil", "who", "whom", "whos", "why",
        "wil", "with", "wol", "wolde", "wot", "woot", "ye", "yet", "yit",
        "you", "your", "youre", "yow",
    }
)

# Native weak-h pronouns/auxiliaries + French h-muet stems triggering prevocalic -e elision
WEAK_H_STEMS: frozenset[str] = frozenset(
    {
        "he", "hem", "her", "hir", "hire", "his", "hit", "how", "hym", "him",
        "him-self", "hym-self", "han", "hath", "haue", "have", "had", "hadde",
        "honour", "honouren", "honurable", "humble", "humblesse", "humilitee",
        "habit", "hour", "houre", "eir", "heir", "herbe", "host", "hostelrie",
    }
)

# Words whose written final -e was petrified / silent in Chaucer's London usage
PETRIFIED_SILENT_E: frozenset[str] = frozenset(
    {"thise", "these", "hire", "oure", "youre", "ther-fore", "wher-fore", "here-before"}
)

# Words with frequent optional apocope of final -e even before consonants
OPTIONAL_APOCOPE_WORDS: frozenset[str] = frozenset(
    {
        "have", "haue", "were", "sone", "more", "moore", "sore", "soore",
        "shulde", "sholde", "wolde", "hadde", "koude", "dorste", "moste",
        "oghte", "dide", "come", "tyme", "tale", "make", "take", "yeve",
        "loue", "love", "helle", "forbede", "acorde", "founde",
    }
)


def normalize_orthography(surface: str) -> str:
    """Normalize diplomatic Middle English spelling without erasing phonemic contrasts."""
    w = surface.strip().lower()
    # Strip editorial daggers or punctuation attached to edges
    w = re.sub(r"^[^a-zA-Zȝþðëé'-]+|[^a-zA-Zȝþðëé'-]+$", "", w)
    # Initial scribal capital 'ff' -> 'f' (e.g., 'ffro' -> 'fro', 'ffor' -> 'for')
    if w.startswith("ff"):
        w = "f" + w[2:]
    # Thorn / eth -> 'th'
    w = w.replace("þ", "th").replace("ð", "th")
    # Yogh 'ȝ': initial before vowel -> 'y' (e.g., 'ȝow' -> 'yow', 'ȝit' -> 'yit'), else 'gh'
    if w.startswith("ȝ"):
        w = "y" + w[1:]
    w = w.replace("ȝ", "gh")
    return w


class MEDLexicon:
    """Lookup interface for Stratum S4 Middle English Dictionary (MED) entries and Law L1."""

    def __init__(self, lexicon_path: Path | None = None, max_year: int = 1400) -> None:
        self.path = lexicon_path or DEFAULT_LEXICON_PATH
        self.max_year = max_year
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.metadata: dict[str, Any] = raw.get("metadata", {})
        self.entries: dict[str, dict[str, Any]] = raw.get("entries", {})

    def lookup(self, surface: str) -> dict[str, Any] | None:
        """Look up a surface or orthographically normalized Middle English token."""
        raw_lower = re.sub(r"^[^a-zA-Zȝþðëé'-]+|[^a-zA-Zȝþðëé'-]+$", "", surface.strip().lower())
        if raw_lower in self.entries:
            return self.entries[raw_lower]
        norm = normalize_orthography(surface)
        if norm in self.entries:
            return self.entries[norm]
        # Vocalic/consonantal u/v and i/j scribal variants (e.g., 'louynge' <-> 'lovynge', 'ioie' <-> 'joye')
        uv_variant = re.sub(r"([aeiouy])u([aeiouy])", r"\1v\2", norm)
        if uv_variant in self.entries:
            return self.entries[uv_variant]
        if norm.startswith("i") and len(norm) > 1 and norm[1] in "aeiou":
            j_variant = "j" + norm[1:]
            if j_variant in self.entries:
                return self.entries[j_variant]
        return None

    def check_l1_chronology(self, surface: str, entry: dict[str, Any] | None) -> str | None:
        """Enforce Conservation Law L1: reject words attested strictly after 1400 CE."""
        if entry is not None:
            year = int(entry.get("earliest_year", 1390))
            if year > self.max_year:
                return (
                    f"L1 violation: '{surface}' (lemma '{entry.get('lemma')}', {entry.get('med_id')}) "
                    f"attested {year} > {self.max_year} CE"
                )
        return None

    @staticmethod
    def classify_word_class(norm: str, entry: dict[str, Any] | None) -> WordClass:
        if entry and "word_class" in entry:
            return WordClass(entry["word_class"])
        return WordClass.FUNCTION if norm in FUNCTION_WORDS else WordClass.CONTENT

    @staticmethod
    def is_weak_h(norm: str, entry: dict[str, Any] | None) -> bool:
        if entry and "weak_h" in entry:
            return bool(entry["weak_h"])
        return norm in WEAK_H_STEMS

    @staticmethod
    def classify_final_e(norm: str, entry: dict[str, Any] | None) -> FinalEClass:
        if entry and "final_e" in entry:
            return FinalEClass(entry["final_e"])
        if norm.endswith("ë"):
            return FinalEClass.ETYMOLOGICAL
        if not norm.endswith("e") or norm.endswith("ee"):
            return FinalEClass.MONOSYLLABIC_ROOT if norm.endswith("ee") else FinalEClass.NONE
        if norm in PETRIFIED_SILENT_E:
            return FinalEClass.PETRIFIED_SILENT
        if norm in {"he", "she", "me", "we", "ye", "be", "the", "ne"}:
            return FinalEClass.MONOSYLLABIC_ROOT
        if norm in OPTIONAL_APOCOPE_WORDS or norm.endswith(("ynge", "inge")):
            return FinalEClass.OPTIONAL_APOCOPE
        return FinalEClass.INFLECTIONAL
