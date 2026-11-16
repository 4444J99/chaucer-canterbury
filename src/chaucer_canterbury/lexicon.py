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
        "a", "al", "alle", "als", "also", "almost", "am", "an", "and", "anon",
        "another", "any", "art", "as", "at", "atte", "ay",
        "be", "been", "ben", "beth", "bothe", "but", "but-if", "by", "can", "coude", "dar",
        "did", "dide", "do", "don", "doth", "dooth", "ech", "eche", "eek", "either", "eyther",
        "elles", "er", "ere", "ever", "evere", "everichon", "every", "for", "fro", "ffro", "from", "ful", "gan",
        "had", "hadde", "han", "hath", "haue", "have", "he", "heer-up-on", "hem", "her",
        "hir", "hire", "his", "hit", "how", "hym", "him", "him-self", "hym-self",
        "i", "if", "in", "in-to", "into", "is", "ys", "it", "kan", "koude", "lat", "mai", "may", "me",
        "men", "mi", "min", "mo", "moot", "moste", "my", "myn", "na", "namo", "namore", "na-more", "nas",
        "nat", "natheles", "nathelees", "ne", "ner", "never", "nevere", "nil", "nyl", "nis", "nys", "no", "noght", "non",
        "noon", "nor", "not", "now", "o", "of", "on", "oon", "or", "other",
        "ough", "oghte", "our", "oure", "out", "quod", "right", "sal", "save", "shal", "she",
        "sholde", "shul", "shulde", "sin", "sithen", "so", "som", "somme", "swich", "swiche",
        "than", "thanne", "that", "the", "thee", "then", "ther", "there",
        "ther-as", "therfore", "ther-fore", "ther-on", "ther-to", "ther-up-on", "these", "they", "thi", "thin",
        "this", "thise", "tho", "thogh", "though", "thow", "thou", "thurgh",
        "thus", "thy", "thyn", "til", "to", "un-to", "unto", "up", "up-on",
        "upon", "us", "was", "we", "wel", "were", "weren", "what", "whan", "wher",
        "where", "wherfor", "wherfore", "wher-fore", "which", "whiche", "whil", "who", "whom", "whos", "why",
        "wil", "with", "with-alle", "wol", "wole", "wolde", "wolden", "wot", "woot", "ye", "yet", "yit",
        "you", "your", "youre", "yow",
    }
)

# Native weak-h pronouns/auxiliaries + French h-muet stems triggering prevocalic -e elision
WEAK_H_STEMS: frozenset[str] = frozenset(
    {
        "he", "hem", "her", "hir", "hire", "his", "hit", "how", "hym", "him",
        "him-self", "hym-self", "han", "hath", "haue", "have", "had", "hadde",
        "honour", "honouren", "honurable", "honest", "honestee", "homage",
        "humble", "humblesse", "humilitee", "habit", "habundant", "heritage",
        "hour", "houre", "eir", "heir", "herbe", "host", "hoste", "hostelrie", "hostelrye",
    }
)

# Words whose written final -e was petrified / silent in Chaucer's London usage
PETRIFIED_SILENT_E: frozenset[str] = frozenset(
    {"thise", "these", "hire", "oure", "youre", "ther-fore", "wher-fore", "here-before"}
)

# Words with frequent optional apocope of final -e even before consonants
OPTIONAL_APOCOPE_WORDS: frozenset[str] = frozenset(
    {
        "have", "haue", "were", "sone", "more", "moore", "namore", "na-more", "sore", "soore",
        "shulde", "sholde", "wolde", "hadde", "koude", "coude", "dorste", "moste",
        "oghte", "dide", "come", "tyme", "somtyme", "tale", "make", "take", "yeve",
        "loue", "love", "helle", "forbede", "acorde", "founde",
        "whiche", "swiche", "eche", "bothe", "somme", "atte", "alle", "owene",
        "therfore", "wherfore", "wole", "alone", "allone", "madame", "sire", "dame",
        "here", "there", "where", "everywhere", "telle", "swere", "slepe", "wake", "rome", "truste",
        "muche", "lite", "swifte", "ofte", "softe", "reule", "maure", "spousaille", "bataille", "write",
    }
)

# Historical Middle English open vs. close long mid-vowel stem classes
# Close /eː/ < OE ē, ēo, Anglian ē, OF -é / -ie
CLOSE_E_STEMS: frozenset[str] = frozenset(
    {
        "be", "been", "ben", "he", "me", "she", "we", "ye", "thee",
        "free", "three", "tree", "knee", "flee", "se", "seen", "sene", "stre", "gree", "degree",
        "grene", "kene", "shene", "quene", "wene", "thirtene", "fourtene", "fiftene", "sixtene",
        "seventene", "eightetene", "nynetene", "tramissene",
        "seke", "biseke", "eke", "meke", "cheke",
        "depe", "kepe", "wepe", "slepe", "crepe",
        "seme", "deme", "queme", "breme",
        "spede", "hede", "stede", "glede", "forbede", "blede", "fede", "nede",
        "speed", "steed", "teeth", "gees", "feet", "sweet", "swete", "strete",
        "streen", "preest", "preestes", "cheef", "theef", "leef", "breef", "privee",
    }
)

# Open /ɛː/ < OE ǣ, ēa, and ME open-syllable lengthening of short e
OPEN_E_STEMS: frozenset[str] = frozenset(
    {
        "see", "speke", "breke", "wreke",
        "mene", "clene", "lene", "meen", "cleen",
        "hepe", "lepe", "chepe", "stepe",
        "dreme", "streme", "beme", "reme",
        "breeth", "heeth", "deeth", "sheeth",
        "rede", "dede", "drede", "brede", "lede", "sprede", "threde", "mede",
        "deed", "reed", "breed", "wastel-breed", "heed", "forheed", "leed", "shreed",
        "lees", "cloisterlees", "waterlees", "endlees", "recchelees", "giltlees", "pees", "ees",
        "prees", "encrees", "deel", "meel", "weel", "ese", "plese", "disese", "apese",
        "este", "heste", "leste", "meste", "feste", "requeste", "beeste",
    }
)

# Close /oː/ < OE ō, ON ó
CLOSE_O_STEMS: frozenset[str] = frozenset(
    {
        "sote", "swote", "rote", "roote", "bote", "boote", "fote", "foote", "mote",
        "good", "goode", "wood", "woode", "food", "foode", "mood", "flood", "blood", "stood", "hood",
        "book", "took", "shook", "look", "forsok", "forsook", "cook", "hook", "awook", "quook",
        "do", "to", "unto", "un-to", "sho", "shoo",
        "doon", "don", "shoon", "spoon", "soon", "sone", "mone_moon",
        "flore", "floor", "swore", "tothe", "tooth", "sooth", "sothe",
    }
)

# Open /ɔː/ < OE ā and ME open-syllable lengthening of short o
OPEN_O_STEMS: frozenset[str] = frozenset(
    {
        "cote", "throte", "note", "grote", "frote",
        "brood", "lood", "rood", "abood",
        "stoon", "goon", "noon", "oon", "echoon", "echon", "everichon", "anon", "anoon", "boon", "loon", "mone", "alone", "allone",
        "go", "so", "also", "mo", "namo", "wo", "fro", "tho", "two", "foo", "fo", "lo", "no",
        "more", "moore", "namore", "na-more", "sore", "soore", "lore", "loore", "yore", "yoore",
        "bifore", "before", "therfore", "wherfore", "bore", "y-bore", "core", "gore", "hore", "ore",
        "colde", "olde", "holde", "biholde", "bolde", "folde", "golde", "solde", "tolde",
        "bothe", "clothe", "lothe", "wrothe", "oothe",
        "hoot", "woot", "goot", "coot", "smoot", "wroot",
    }
)

# Post-1400 Neo-Latin/Greek and Early-Modern/Industrial anachronism horizon (Law L1)
POST_1400_LEXICAL_HORIZON: dict[str, int] = {
    "protestant": 1539,
    "puritan": 1572,
    "telescope": 1619,
    "microscope": 1656,
    "barometer": 1665,
    "thermometer": 1633,
    "coffee": 1598,
    "tobacco": 1577,
    "potato": 1565,
    "chocolate": 1604,
    "newspaper": 1667,
    "factory": 1582,
    "parliamentarian": 1642,
    "capitalism": 1854,
    "socialism": 1837,
    "communism": 1840,
    "electricity": 1646,
    "disillusion": 1651,
    "psychology": 1654,
    "sociology": 1842,
    "biology": 1802,
    "ideology": 1796,
    "railroad": 1757,
    "railway": 1756,
    "locomotive": 1612,
    "steamboat": 1787,
    "steamship": 1819,
    "submarine": 1648,
    "printing-press": 1589,
    "scientist": 1834,
    "rifleman": 1775,
    "telegraph": 1794,
    "telephone": 1844,
    "photograph": 1839,
    "camera": 1708,
    "automobile": 1895,
    "airplane": 1907,
    "television": 1907,
    "radio": 1907,
    "radar": 1941,
    "laser": 1960,
    "computer": 1946,
    "automation": 1948,
    "software": 1958,
    "hardware": 1515,
    "database": 1962,
    "algorithm_modern": 1957,
    "internet": 1974,
    "website": 1993,
    "smartphone": 2007,
    "podcast": 2004,
    "blockchain": 2008,
    "rifle": 1751,
    "pistol": 1570,
    "musket": 1587,
    "bayonet": 1611,
    "grenade": 1591,
    "artillery_modern": 1560,
    "propaganda": 1718,
    "bureaucracy": 1818,
    "nationalism": 1798,
    "colonialism": 1853,
    "industrial": 1587,
    "laboratory": 1605,
    "vaccine": 1799,
    "antibiotic": 1899,
    "chromosome": 1889,
    "electron": 1891,
    "quantum": 1567,
}

POST_1400_AFFIX_PATTERNS: tuple[tuple[str, int], ...] = (
    (r"^(tele|photo|micro|electro|cyber|thermo|neuro|socio|psycho|steam|rifle|submarin)[a-z-]{2,}$", 1650),
    (r"^[a-z]{3,}(graph|scope|ware|base)$", 1750),
    (r"^(tele|micro|smart|ear|head|mega|gramo)phone$", 1850),
    (r"^[a-z]{3,}ology$", 1650),
    (r"^[a-z]{4,}ism$", 1550),
)

PRE_1400_AFFIX_EXCEPTIONS: frozenset[str] = frozenset(
    {"theology", "astrology", "mythology", "baptism", "sophism", "schism", "thesiphone", "persephone", "antigone"}
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

    def __len__(self) -> int:
        return len(self.entries)

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
        norm = normalize_orthography(surface)
        if norm in POST_1400_LEXICAL_HORIZON:
            yr = POST_1400_LEXICAL_HORIZON[norm]
            return f"L1 violation: '{surface}' attested {yr} > {self.max_year} CE"
        if norm not in PRE_1400_AFFIX_EXCEPTIONS:
            for pattern, approx_year in POST_1400_AFFIX_PATTERNS:
                if re.match(pattern, norm):
                    return f"L1 violation: '{surface}' post-1400 neoclassical/modern formation (~{approx_year} > {self.max_year} CE)"
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
