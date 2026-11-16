"""Deterministic extractor and builder for Validation Plan 02 blind-scansion holdout sets.

Reads W. W. Skeat's *The Complete Works of Geoffrey Chaucer*, vol. 4 (*The Canterbury Tales: Text*,
2nd ed., Oxford: Clarendon Press, 1900; Project Gutenberg #22120 `22120-8.txt`), verifies its
SHA-256 digest, and writes the frozen `EVALUATION_ONLY` holdout corpus and SHA-256 manifest under
`data/s1_witnesses/blind_scansion/`:

- `h1_general_prologue_1_200.json`   (200 lines: General Prologue 1-200, riding-rhyme couplets)
- `h2_clerks_tale_stanzas_1_20.json` (140 lines: Clerk's Tale Prima Pars 57-196, 20 rhyme-royal stanzas)
- `h3_sir_thopas_1_60.json`          (60 lines: Sir Thopas 1902-1961, 10 tail-rhyme stanzas)
- `h4_general_prologue_201_400.json` (200 lines: General Prologue 201-400, untouched second holdout)
- `n1_corrupted_340.json`            (340 lines: 1 corruption per H1+H2 line, 85 per corruption type)
- `reference_annotations_70.json`    (70 lines: 50 H1 + 20 H2 expected syllable counts & final -e labels)
- `manifest.json`                    (SHA-256 hashes and provenance metadata)

Usage:
    python3 scripts/extract_skeat_holdouts.py /path/to/22120-8.txt
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

EXPECTED_UPSTREAM_SHA256 = "2506000b31a78ae72dd9d1dd755fb3f305c42516b293960c222ad78509fc00db"
UPSTREAM_REPO_URL = (
    "https://github.com/GITenberg/Chaucer-s-Works-Volume-4--of-7----The-Canterbury-Tales_22120"
)
UPSTREAM_COMMIT = "1e7f4c2ef672531d0676159202f2f9e2520e174c"
EDITION_CITATION = (
    "W. W. Skeat (ed.), The Complete Works of Geoffrey Chaucer, vol. 4, "
    "The Canterbury Tales: Text, 2nd ed., Oxford: Clarendon Press, 1900 (Project Gutenberg #22120)."
)

PAGE_MARK = re.compile(r"^\s*\[\d+: T\. \d+-\d+\.\]\s*$")
GAP = re.compile(r"\s{3,}")
MARGIN_NO = re.compile(r"^(?P<n>\d+)(?: (?P<sfx>[a-z]))?$|^\((?P<alt>\d+)\)$")

# Conservative scholarly contested flags (Benson, Riverside Chaucer pp. xlii-xlv & textual notes; Skeat vol. 5)
CONTESTED_LINES: dict[str, str] = {
    "GP.76": "Irregular initial/syncopated scansion ('Al bismotered with his habergeoun'); noted in Benson p. xliv.",
    "GP.131": "Manuscript variation and irregular initial foot ('That no drope ne fille'); Skeat vol. 5 note to A.131.",
    "GP.162": "Macaronic Latin motto ('And after, Amor vincit omnia') outside English phonology.",
    "GP.163": "Textually disputed four-stress/incomplete line ('Another NONNE with hir hadde she'); Riverside note to I.163-64.",
    "CL.57": "Hengwrt/Skeat lacks 'right' ('Ther is, at the west syde of Itaille') vs Ellesmere regularization; Skeat note to E.57.",
    "CL.142": "Broken-backed/nine-syllable line ('Made the markis herte han pitee'); Skeat vol. 5 note to E.142.",
    "TH.1929": "Project Gutenberg #22120 OCR misprint ('Ther-to be was a good archeer' for 'he').",
}

# Authentic Middle English open-vs-close mid-vowel minimal-coda swaps (/e:/ <-> /E:/, /o:/ <-> /O:/)
# Pre-/r/ rhymes are intentionally excluded because Chaucer admits pre-/r/ variation ('matere'/'here').
MID_VOWEL_SWAPS: dict[str, tuple[str, str]] = {
    # Close /o:/ <-> Open /O:/
    "sote": ("cote", "close_o /oːtə/ (OE swōte) -> open_o /ɔːtə/ (OE cote)"),
    "rote": ("throte", "close_o /oːtə/ (ON rót) -> open_o /ɔːtə/ (OE þrote)"),
    "good": ("brood", "close_o /oːd/ (OE gōd) -> open_o /ɔːd/ (OE brād 'broad')"),
    "wood": ("lood", "close_o /oːd/ (OE wōd) -> open_o /ɔːd/ (OE lād 'load')"),
    "sho": ("go", "close_o /oː/ (OE scōh) -> open_o /ɔː/ (OE gān)"),
    # Open /O:/ <-> Close /o:/
    "everichon": ("doon", "open_o /ɔːn/ (OE ān) -> close_o /oːn/ (OE dōn)"),
    "anon": ("doon", "open_o /ɔːn/ (OE on ān) -> close_o /oːn/ (OE dōn)"),
    "stoon": ("doon", "open_o /ɔːn/ (OE stān) -> close_o /oːn/ (OE dōn)"),
    "noon": ("doon", "open_o /ɔːn/ (OE nān) -> close_o /oːn/ (OE dōn)"),
    "echoon": ("shoon", "open_o /ɔːn/ (OE ān) -> close_o /oːn/ (OE scōn)"),
    "foo": ("do", "open_o /ɔː/ (OE fā) -> close_o /oː/ (OE dōn)"),
    "also": ("to", "open_o /ɔː/ (OE eall swā) -> close_o /oː/ (OE tō)"),
    "namo": ("do", "open_o /ɔː/ (OE nā mā) -> close_o /oː/ (OE dōn)"),
    "so": ("sho", "open_o /ɔː/ (OE swā) -> close_o /oː/ (OE scōh 'shoe')"),
    "bifore": ("flore", "open_o /ɔːrə/ (OE beforan) -> close_o /oːrə/ (OE flōr)"),
    "more": ("flore", "open_o /ɔːrə/ (OE māra) -> close_o /oːrə/ (OE flōr)"),
    "yore": ("flore", "open_o /ɔːrə/ (OE gēara) -> close_o /oːrə/ (OE flōr)"),
    "sore": ("flore", "open_o /ɔːrə/ (OE sāre) -> close_o /oːrə/ (OE flōr)"),
    "lore": ("flore", "open_o /ɔːrə/ (OE lār) -> close_o /oːrə/ (OE flōr)"),
    "y-bore": ("flore", "open_o /ɔːrə/ (OE geboren) -> close_o /oːrə/ (OE flōr)"),
    "therfore": ("flore", "open_o /ɔːrə/ -> close_o /oːrə/ (OE flōr)"),
    "colde": ("sholde", "open_o /ɔːldə/ (Anglian cāld) -> /oːldə/ modal mismatch"),
    "biholde": ("wolde", "open_o /ɔːldə/ (Anglian bihāldan) -> /oːldə/ modal mismatch"),
    "olde": ("sholde", "open_o /ɔːldə/ (Anglian āld) -> /oːldə/ modal mismatch"),
    # Close /e:/ <-> Open /E:/
    "seke": ("speke", "close_e /eːkə/ (OE sēcan) -> open_e /ɛːkə/ (OE sprecan)"),
    "grene": ("mene", "close_e /eːnə/ (OE grēne) -> open_e /ɛːnə/ (OE mǣnan)"),
    "kene": ("clene", "close_e /eːnə/ (OE cēne) -> open_e /ɛːnə/ (OE clǣne)"),
    "shene": ("lene", "close_e /eːnə/ (OE scīene) -> open_e /ɛːnə/ (OE hlǣne)"),
    "fiftene": ("mene", "close_e /eːnə/ (OE fīftēne) -> open_e /ɛːnə/ (OE mǣnan)"),
    "tramissene": ("clene", "close_e /eːnə/ -> open_e /ɛːnə/ (OE clǣne)"),
    "depe": ("hepe", "close_e /eːpə/ (OE dēop) -> open_e /ɛːpə/ (OE hēap)"),
    "kepe": ("lepe", "close_e /eːpə/ (OE cēpan) -> open_e /ɛːpə/ (OE hlēapan)"),
    "seme": ("dreme", "close_e /eːmə/ (ON sœma) -> open_e /ɛːmə/ (OE drēam)"),
    "deme": ("streme", "close_e /eːmə/ (OE dēman) -> open_e /ɛːmə/ (OE strēam)"),
    "been": ("meen", "close_e /eːn/ (OE bēon) -> open_e /ɛːn/ (OE mǣnan)"),
    "streen": ("cleen", "close_e /eːn/ (OE strēon) -> open_e /ɛːn/ (OE clǣne)"),
    "me": ("see", "close_e /eː/ (OE mē) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "degree": ("see", "close_e /eː/ (OF degré) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "be": ("see", "close_e /eː/ (OE bēon) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "she": ("see", "close_e /eː/ -> open_e /ɛː/ (OE sǣ 'sea')"),
    "three": ("see", "close_e /eː/ (OE þrēo) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "we": ("see", "close_e /eː/ (OE wē) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "ye": ("see", "close_e /eː/ (OE gē) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "humanitee": ("see", "close_e /eː/ (OF -ité) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "necessitee": ("see", "close_e /eː/ (OF -ité) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "felicitee": ("see", "close_e /eː/ (OF -ité) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "pitee": ("see", "close_e /eː/ (OF pité) -> open_e /ɛː/ (OE sǣ 'sea')"),
    "libertee": ("see", "close_e /eː/ (OF liberté) -> open_e /ɛː/ (OE sǣ 'sea')"),
    # Open /E:/ <-> Close /e:/
    "breeth": ("teeth", "open_e /ɛːθ/ (OE brǣþ) -> close_e /eːθ/ (OE tēþ)"),
    "heeth": ("teeth", "open_e /ɛːθ/ (OE hǣþ) -> close_e /eːθ/ (OE tēþ)"),
    "mede": ("spede", "open_e /ɛːdə/ (OE mǣd 'mead') -> close_e /eːdə/ (OE spēdan)"),
    "rede": ("hede", "open_e /ɛːdə/ (OE rēad 'red') -> close_e /eːdə/ (OE hēdan)"),
    "clene": ("grene", "open_e /ɛːnə/ (OE clǣne) -> close_e /eːnə/ (OE grēne)"),
    "sene": ("grene", "open_e /ɛːnə/ -> close_e /eːnə/ (OE grēne)"),
    "wastel-breed": ("speed", "open_e /ɛːd/ (OE brēad) -> close_e /eːd/ (OE spēd)"),
    "deed": ("speed", "open_e /ɛːd/ (OE dēad) -> close_e /eːd/ (OE spēd)"),
    "reed": ("speed", "open_e /ɛːd/ (OE rēad) -> close_e /eːd/ (OE spēd)"),
    "forheed": ("steed", "open_e /ɛːd/ (OE forhēafod) -> close_e /eːd/ (OE stēda)"),
    "cloisterlees": ("gees", "open_e /ɛːs/ (OE -lēas) -> close_e /eːs/ (OE gēs)"),
    "waterlees": ("gees", "open_e /ɛːs/ (OE -lēas) -> close_e /eːs/ (OE gēs)"),
    "drede": ("spede", "open_e /ɛːdə/ -> close_e /eːdə/ (OE spēdan)"),
    "forbede": ("dede", "close_e /eːdə/ (OE forbēodan) -> open_e /ɛːdə/ (OE dēad)"),
}

# Post-1400 English anachronisms spanning 16th-21st centuries (OED first attestation years)
POST_1400_ANACHRONISMS: list[tuple[str, int]] = [
    ("protestant", 1539),
    ("factory", 1560),
    ("printing-press", 1589),
    ("telescope", 1619),
    ("electricity", 1646),
    ("submarine", 1648),
    ("microscope", 1649),
    ("disillusion", 1651),
    ("psychology", 1654),
    ("newspaper", 1667),
    ("railroad", 1757),
    ("rifleman", 1775),
    ("telegraph", 1794),
    ("ideology", 1796),
    ("biology", 1802),
    ("steamship", 1819),
    ("scientist", 1834),
    ("photograph", 1839),
    ("sociology", 1842),
    ("capitalism", 1854),
    ("television", 1907),
    ("computer", 1946),
    ("automation", 1948),
    ("internet", 1974),
    ("smartphone", 2007),
]


def extract_section(
    lines: list[str],
    start_marker: str,
    end_marker: str,
    first_line_no: int,
    max_lines: int,
    prefix: str,
) -> list[tuple[int, str]]:
    start = next(i for i, ln in enumerate(lines) if ln.strip() == start_marker)
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == end_marker)
    block = lines[start + 1 : end]
    paras: list[list[str]] = [[]]
    for ln in block:
        if ln.strip():
            paras[-1].append(ln)
        else:
            paras.append([])
    verse: list[tuple[int, str]] = []
    n = first_line_no - 1
    for para in paras:
        para = [ln for ln in para if not PAGE_MARK.match(ln)]
        if not para:
            continue
        first = para[0].strip()
        if first.startswith(
            ("HERE BIGINNETH", "HERE ENDETH", "HEADING.", "*", "EXPLICIT", "HERE THE HOST")
        ):
            continue
        if re.match(r"^\d+[.,\s]", first):
            continue
        for ln in para:
            body, *rest = GAP.split(ln.strip(), maxsplit=1)
            m = MARGIN_NO.match(rest[0].strip()) if rest else None
            printed = suffix = None
            if m and m.group("n"):
                printed, suffix = int(m.group("n")), m.group("sfx")
            if suffix:
                # Bracketed spurious lines (e.g. GP 252b, 252c) sit outside numbered canon
                continue
            n += 1
            if printed is not None and printed != n:
                raise RuntimeError(f"{prefix}: expected line {n}, printed {printed}: {ln!r}")
            verse.append((n, body))
            if len(verse) >= max_lines:
                return verse
    return verse


def base_metadata(set_id: str, role: str, metrical_form: str) -> dict[str, Any]:
    return {
        "stratum": "S1",
        "holdout_flag": "EVALUATION_ONLY",
        "holdout_policy": "STRICT_EVALUATION_ONLY_NEVER_EXPOSED_TO_GENERATOR_OR_CALIBRATION",
        "set_id": set_id,
        "role": role,
        "metrical_form": metrical_form,
        "edition": EDITION_CITATION,
        "source_url": UPSTREAM_REPO_URL,
        "upstream_file": "22120-8.txt",
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_sha256": EXPECTED_UPSTREAM_SHA256,
    }


def make_line_obj(prefix: str, num: int, text: str) -> dict[str, Any]:
    ref = f"{prefix}.{num}"
    contested_note = CONTESTED_LINES.get(ref)
    obj: dict[str, Any] = {
        "ref": ref,
        "line_number": num,
        "text": text,
        "contested": contested_note is not None,
    }
    if contested_note:
        obj["contested_reason"] = contested_note
    return obj


def build_couplet_set(
    set_id: str,
    title: str,
    role: str,
    verse: list[tuple[int, str]],
    couplet_offset: int = 1,
) -> dict[str, Any]:
    stanzas = []
    for idx in range(0, len(verse), 2):
        pair = verse[idx : idx + 2]
        c_no = couplet_offset + (idx // 2)
        stanzas.append(
            {
                "stanza_id": f"GP.C{c_no:03d}",
                "rhyme_scheme": "AA",
                "lines": [make_line_obj("GP", n, t) for n, t in pair],
            }
        )
    return {
        "metadata": base_metadata(set_id, role, "riding_rhyme_couplet"),
        "work_id": f"BLIND_{set_id}",
        "title": title,
        "stanzas": stanzas,
    }


def build_h2_clerks_tale(verse: list[tuple[int, str]]) -> dict[str, Any]:
    stanzas = []
    for idx in range(0, len(verse), 7):
        chunk = verse[idx : idx + 7]
        s_no = (idx // 7) + 1
        stanzas.append(
            {
                "stanza_id": f"CL.S{s_no:02d}",
                "rhyme_scheme": "ABABBCC",
                "lines": [make_line_obj("CL", n, t) for n, t in chunk],
            }
        )
    return {
        "metadata": base_metadata(
            "H2",
            "Stanza and rhyme recall (Clerk's Tale Prima Pars, 20 rhyme-royal stanzas)",
            "rhyme_royal_ababbcc",
        ),
        "work_id": "BLIND_H2",
        "title": "The Clerk's Tale, Prima Pars, lines 57-196 (Skeat 1900)",
        "stanzas": stanzas,
    }


def build_h3_sir_thopas(verse: list[tuple[int, str]]) -> dict[str, Any]:
    stanzas = []
    for idx in range(0, len(verse), 6):
        chunk = verse[idx : idx + 6]
        s_no = (idx // 6) + 1
        stanzas.append(
            {
                "stanza_id": f"TH.S{s_no:02d}",
                "rhyme_scheme": "AABCCB",
                "beat_targets": [4, 4, 3, 4, 4, 3],
                "lines": [make_line_obj("TH", n, t) for n, t in chunk],
            }
        )
    return {
        "metadata": base_metadata(
            "H3",
            "Tests the tail-rhyme form (Sir Thopas, first 10 six-line stanzas)",
            "tail_rhyme_aabccb",
        ),
        "work_id": "BLIND_H3",
        "title": "The Tale of Sir Thopas, lines 1902-1961 (Skeat 1900)",
        "stanzas": stanzas,
    }


def _last_alpha_word(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-zëé-]+", " ", text.lower())
    parts = [p for p in cleaned.split() if p]
    return parts[-1] if parts else ""


def _replace_last_word(text: str, new_word: str) -> str:
    m = list(re.finditer(r"[A-Za-zëé-]+", text))
    if not m:
        return text + " " + new_word
    last = m[-1]
    return text[: last.start()] + new_word + text[last.end() :]


def _corrupt_hyper_or_hypometric(text: str, idx: int) -> tuple[str, str]:
    words = re.findall(r"[A-Za-zëé'-]+|[,.;:!?()_\"-]+|\s+", text)
    word_positions = [i for i, tok in enumerate(words) if re.match(r"^[A-Za-zëé]", tok)]
    if idx % 2 == 0:
        # Insert a disyllabic/trisyllabic Middle English adverb before a consonant-initial word (+2/+3 syllables -> >=12)
        ins_word = "verrayly" if (idx // 2) % 2 == 0 else "certeynly"
        insert_after = word_positions[min(2, len(word_positions) - 1)]
        corrupted = "".join(words[: insert_after + 1]) + f" {ins_word}" + "".join(words[insert_after + 1 :])
        return corrupted, f"Inserted Middle English adverb '{ins_word}' (+3 syllables, hypermetric)"
    else:
        # Delete two consecutive interior words or a multisyllable phrase so syllable count drops <= 7 (hypometric)
        alpha_words = [tok for tok in re.findall(r"[A-Za-zëé'-]+", text)]
        if len(alpha_words) >= 5:
            kept = alpha_words[:2] + alpha_words[5:]
        else:
            kept = alpha_words[:2]
        return " ".join(kept), "Deleted interior phrase (-3+ syllables, hypometric)"


def _corrupt_anachronism(text: str, idx: int) -> tuple[str, str, str, int]:
    anach_word, year = POST_1400_ANACHRONISMS[idx % len(POST_1400_ANACHRONISMS)]
    tokens = re.findall(r"[A-Za-zëé'-]+", text)
    if len(tokens) >= 4:
        # Substitute an interior token so line length remains plausible while violating Law L1 (>1400 CE)
        target_idx = len(tokens) // 2
        corrupted_tokens = tokens[:target_idx] + [anach_word] + tokens[target_idx + 1 :]
        corrupted = " ".join(corrupted_tokens)
    else:
        corrupted = f"{text} {anach_word}"
    return corrupted, anach_word, f"Inserted post-1400 word '{anach_word}' (attested {year} CE)", year


def _corrupt_stress_inversion(text: str) -> tuple[str, str]:
    """Reorder words to preserve exact token multiset & syllable count while inducing a stress collision."""
    cleaned = re.sub(r"[()_\"']", "", text)
    punct_stripped = re.sub(r"[,.;:!?—–]", "", cleaned)
    words = [w for w in punct_stripped.split() if w]
    vowels = re.compile(r"[aeiouyëé]+", re.I)

    # Look for a polysyllabic content word (>=2 vowel groups) that we can move so its primary stress lands in an offbeat
    poly_idx = None
    for i, w in enumerate(words):
        wl = w.lower()
        if len(vowels.findall(wl)) >= 2 and wl not in {
            "into", "in-to", "unto", "un-to", "upon", "up-on", "over", "after", "under",
            "other", "another", "never", "ever", "many", "every", "any", "only", "hadde",
            "were", "weren", "wolde", "sholde", "shulde", "coude", "have", "whiche",
        }:
            poly_idx = i
            break

    # Permute words into an anti-iambic clustering: group function monosyllables at the right edge (forcing an
    # unstressed function/article onto final beat or placing polysyllable primary stress into mid-line offbeat)
    func_set = {
        "the", "a", "an", "of", "in", "to", "for", "with", "and", "that", "as", "at",
        "by", "his", "hir", "our", "your", "my", "is", "was", "he", "it", "ne", "so",
    }
    funcs = [w for w in words if w.lower() in func_set]
    contents = [w for w in words if w.lower() not in func_set]

    if poly_idx is not None and funcs and contents:
        # Place two stressed words adjacent after three unstressed words, and end on unstressed article/preposition if present
        articles = [w for w in funcs if w.lower() in {"the", "a", "an", "ne"}]
        other_funcs = [w for w in funcs if w.lower() not in {"the", "a", "an", "ne"}]
        # Put polysyllable at index 2 (after two monosyllables -> slot 3 'x' offbeat!) and trailing article at end
        poly_word = words[poly_idx]
        rem_contents = [w for j, w in enumerate(words) if j != poly_idx and w.lower() not in func_set]
        reordered: list[str] = []
        pool_mono = other_funcs + rem_contents
        if len(pool_mono) >= 2:
            # Ensure first two tokens are monosyllabic if possible so polysyllable starts at syllable index 2 ('x' offbeat!)
            monos = [w for w in pool_mono if len(vowels.findall(w)) == 1]
            rest = [w for w in pool_mono if len(vowels.findall(w)) != 1]
            # Remove matching counts carefully to preserve exact multiset
            used_idx: set[int] = set()
            lead: list[str] = []
            for j, w in enumerate(pool_mono):
                if len(vowels.findall(w)) == 1 and len(lead) < 2:
                    lead.append(w)
                    used_idx.add(j)
            tail_pool = [w for j, w in enumerate(pool_mono) if j not in used_idx]
            reordered = lead + [poly_word] + tail_pool + articles
        else:
            reordered = [poly_word] + pool_mono + articles
        if reordered != words:
            return " ".join(reordered), (
                f"Reordered exact word multiset placing polysyllable '{poly_word}' into offbeat / trailing function clitic"
            )

    # Fallback: reverse interior/final order putting function words last and inverting beat alignment
    reordered_fb = contents + list(reversed(funcs))
    if reordered_fb == words:
        reordered_fb = list(reversed(words))
    return " ".join(reordered_fb), "Reordered exact word multiset to disrupt alternating iambic stress"


def build_n1_corrupted(
    h1_doc: dict[str, Any], h2_doc: dict[str, Any]
) -> dict[str, Any]:
    """Build 340 deterministically corrupted items (85 per type) across all 340 H1+H2 lines."""
    # Collect all 340 lines together with their rhyming partner line in their stanza
    all_entries: list[dict[str, Any]] = []
    for set_id, doc in [("H1", h1_doc), ("H2", h2_doc)]:
        for st in doc["stanzas"]:
            scheme = st["rhyme_scheme"]
            st_lines = st["lines"]
            for pos, ln in enumerate(st_lines):
                lbl = scheme[pos]
                partner_candidates = [
                    st_lines[j]["text"] for j in range(len(st_lines)) if j != pos and scheme[j] == lbl
                ]
                all_entries.append(
                    {
                        "source_set": set_id,
                        "stanza_id": st["stanza_id"],
                        "ref": ln["ref"],
                        "line_number": ln["line_number"],
                        "original_text": ln["text"],
                        "partner_line": partner_candidates[0],
                    }
                )

    assert len(all_entries) == 340, f"Expected 340 H1+H2 lines, got {len(all_entries)}"

    # Select all genuine non-contested open/close mid-vowel lines in H1+H2 (up to 85)
    mid_vowel_indices: list[int] = []
    for idx, item in enumerate(all_entries):
        ew = _last_alpha_word(item["original_text"])
        partner_ew = _last_alpha_word(item["partner_line"])
        if ew in MID_VOWEL_SWAPS and partner_ew != MID_VOWEL_SWAPS[ew][0] and item["ref"] not in CONTESTED_LINES:
            mid_vowel_indices.append(idx)
            if len(mid_vowel_indices) == 85:
                break

    if len(mid_vowel_indices) < 50:
        raise RuntimeError(f"Found only {len(mid_vowel_indices)} mid-vowel swap candidates, expected >= 50")

    mid_set = set(mid_vowel_indices)
    remaining_indices = [i for i in range(340) if i not in mid_set]

    # Partition remaining lines deterministically and evenly across the other 3 corruption types
    hyper_hypo_set = {remaining_indices[i] for i in range(0, len(remaining_indices), 3)}
    anach_set = {remaining_indices[i] for i in range(1, len(remaining_indices), 3)}
    stress_set = {remaining_indices[i] for i in range(2, len(remaining_indices), 3)}

    corrupted_items: list[dict[str, Any]] = []
    c_hyper = c_anach = 0
    for idx, item in enumerate(all_entries):
        cid = f"N1.{idx + 1:03d}"
        if idx in mid_set:
            ew = _last_alpha_word(item["original_text"])
            replacement, note = MID_VOWEL_SWAPS[ew]
            corrupted_text = _replace_last_word(item["original_text"], replacement)
            corrupted_items.append(
                {
                    "corruption_id": cid,
                    "source_set": item["source_set"],
                    "source_ref": item["ref"],
                    "corruption_type": "mid_vowel_rhyme_violation",
                    "original_text": item["original_text"],
                    "partner_line": item["partner_line"],
                    "corrupted_text": corrupted_text,
                    "note": note,
                }
            )
        elif idx in hyper_hypo_set:
            corrupted_text, note = _corrupt_hyper_or_hypometric(item["original_text"], c_hyper)
            c_hyper += 1
            corrupted_items.append(
                {
                    "corruption_id": cid,
                    "source_set": item["source_set"],
                    "source_ref": item["ref"],
                    "corruption_type": "hypermetric_or_hypometric",
                    "original_text": item["original_text"],
                    "corrupted_text": corrupted_text,
                    "note": note,
                }
            )
        elif idx in anach_set:
            corrupted_text, word, note, year = _corrupt_anachronism(item["original_text"], c_anach)
            c_anach += 1
            corrupted_items.append(
                {
                    "corruption_id": cid,
                    "source_set": item["source_set"],
                    "source_ref": item["ref"],
                    "corruption_type": "post_1400_anachronism",
                    "original_text": item["original_text"],
                    "corrupted_text": corrupted_text,
                    "anachronism_word": word,
                    "attestation_year": year,
                    "note": note,
                }
            )
        else:
            corrupted_text, note = _corrupt_stress_inversion(item["original_text"])
            corrupted_items.append(
                {
                    "corruption_id": cid,
                    "source_set": item["source_set"],
                    "source_ref": item["ref"],
                    "corruption_type": "stress_inversion_collision",
                    "original_text": item["original_text"],
                    "corrupted_text": corrupted_text,
                    "note": note,
                }
            )

    return {
        "metadata": base_metadata(
            "N1",
            "Precision set: 340 deterministically corrupted lines from H1 and H2 (85 per corruption type)",
            "mixed_pentameter_corruptions",
        ),
        "total_items": len(corrupted_items),
        "counts_by_type": {
            "hypermetric_or_hypometric": len(hyper_hypo_set),
            "mid_vowel_rhyme_violation": len(mid_set),
            "post_1400_anachronism": len(anach_set),
            "stress_inversion_collision": len(stress_set),
        },
        "items": corrupted_items,
    }


# Scholarly reference annotations for 50 H1 lines (GP.1-50) + 20 H2 lines (CL.58-77).
# Conventions follow Benson, Riverside Chaucer (pp. xlii-xlv), Harvard Chaucer Website Lesson 2,
# and Skeat (1900, vol. 5 notes):
#   - Line-final etymological/inflectional -e is ALWAYS sounded (feminine ending -> 11 syllables, or 10 if headless).
#   - Prevocalic -e (before a, e, i, o, u) and weak-h -e (before he/hem/hir/his/hit/han/hath/hadde/honour/hostelrye) -> 'elided'.
#   - Pre-consonantal weak/inflectional -e -> 'sounded' unless petrified silent ('whiche', 'hire', 'oure', 'youre', 'thise')
#     or apocopated in standard high-frequency polysyllables/auxiliaries ('were', 'hadde', 'have', 'sonne', 'felawshipe', 'aventure').
REFERENCE_ANNOTATIONS_SPEC: list[tuple[str, str, int, list[tuple[str, str, str]]]] = [
    # H1: GP.1 - GP.50 (50 lines)
    ("H1", "GP.1", 11, [("Aprille", "sounded", "Skeat spells Aprille with sounded -e before consonant (or headless if apocopated)"), ("sote", "sounded", "line-final adverbial/plural -e")]),
    ("H1", "GP.2", 11, [("droghte", "elided", "prevocalic before 'of'"), ("Marche", "elided", "elided before weak-h auxiliary 'hath'"), ("rote", "sounded", "line-final etymological -e")]),
    ("H1", "GP.3", 10, [("veyne", "elided", "prevocalic before 'in'")]),
    ("H1", "GP.4", 10, []),
    ("H1", "GP.5", 10, [("swete", "sounded", "weak singular adjective 'his swete breeth'")]),
    ("H1", "GP.6", 10, []),
    ("H1", "GP.7", 11, [("tendre", "sounded", "weak plural adjective 'the tendre croppes'"), ("yonge", "sounded", "weak singular adjective 'the yonge sonne'"), ("sonne", "sounded", "line-final OE sunne")]),
    ("H1", "GP.8", 11, [("halfe", "sounded", "weak singular adjective 'his halfe cours'"), ("y-ronne", "sounded", "line-final past participle -e")]),
    ("H1", "GP.9", 11, [("smale", "sounded", "plural adjective 'smale fowles'"), ("melodye", "sounded", "line-final Romance -ye")]),
    ("H1", "GP.10", 11, [("yë", "sounded", "line-final disyllabic y-ë")]),
    ("H1", "GP.11", 11, [("nature", "elided", "prevocalic before 'in'")]),
    ("H1", "GP.12", 11, []),
    ("H1", "GP.13", 11, [("straunge", "sounded", "plural adjective 'straunge strondes'")]),
    ("H1", "GP.14", 11, [("ferne", "sounded", "plural adjective 'ferne halwes'"), ("couthe", "elided", "prevocalic before 'in'")]),
    ("H1", "GP.15", 11, [("ende", "sounded", "line-final dative/etymological -e")]),
    ("H1", "GP.16", 11, [("wende", "sounded", "line-final plural verb")]),
    ("H1", "GP.17", 11, [("seke", "sounded", "line-final infinitive")]),
    ("H1", "GP.18", 11, [("were", "silent", "apocopated auxiliary before 'seke'"), ("seke", "sounded", "line-final plural predicate adjective")]),
    ("H1", "GP.19", 10, []),
    ("H1", "GP.20", 10, []),
    ("H1", "GP.21", 11, [("pilgrimage", "sounded", "line-final Romance -age")]),
    ("H1", "GP.22", 11, [("corage", "sounded", "line-final Romance -age")]),
    ("H1", "GP.23", 11, [("come", "elided", "prevocalic before 'in-to'"), ("hostelrye", "sounded", "line-final Romance -ye")]),
    ("H1", "GP.24", 11, [("nyne", "elided", "prevocalic before 'and'"), ("companye", "sounded", "line-final Romance -ye")]),
    ("H1", "GP.25", 11, [("aventure", "elided", "prevocalic before vocalic prefix 'y-falle'"), ("y-falle", "sounded", "line-final past participle")]),
    ("H1", "GP.26", 11, [("felawshipe", "elided", "prevocalic before 'and'"), ("were", "silent", "apocopated auxiliary before 'they'"), ("alle", "sounded", "line-final plural 'alle'")]),
    ("H1", "GP.27", 11, [("ryde", "sounded", "line-final infinitive")]),
    ("H1", "GP.28", 11, [("wyde", "sounded", "line-final plural adjective")]),
    ("H1", "GP.29", 11, [("atte", "sounded", "assimilated 'at the' -> at-të before 'beste'"), ("beste", "sounded", "line-final weak superlative")]),
    ("H1", "GP.30", 11, [("sonne", "silent", "apocopated medial 'sonne' before 'was'"), ("reste", "sounded", "line-final dative noun")]),
    ("H1", "GP.31", 10, [("hadde", "elided", "prevocalic before 'I'")]),
    ("H1", "GP.32", 10, [("felawshipe", "elided", "prevocalic before 'anon'")]),
    ("H1", "GP.33", 11, [("made", "sounded", "preterite -de sounded before 'forward'"), ("ryse", "sounded", "line-final infinitive")]),
    ("H1", "GP.34", 11, [("take", "elided", "prevocalic before 'our'"), ("devyse", "sounded", "line-final 1sg present")]),
    ("H1", "GP.35", 11, [("have", "silent", "apocopated 1sg 'have' before consonant"), ("tyme", "elided", "prevocalic before 'and'"), ("space", "sounded", "line-final Romance -e")]),
    ("H1", "GP.36", 11, [("tale", "sounded", "etymological OE talu sounded before 'pace'"), ("pace", "sounded", "line-final subjunctive")]),
    ("H1", "GP.37", 10, []),
    ("H1", "GP.38", 10, [("telle", "silent", "apocopated infinitive before 'yow' (or disyllabic condicioun)")]),
    ("H1", "GP.39", 10, []),
    ("H1", "GP.40", 10, [("whiche", "silent", "petrified/apocopated 'whiche' before 'they'")]),
    ("H1", "GP.41", 11, [("were", "elided", "prevocalic before 'inne'"), ("inne", "sounded", "line-final adverbial -e")]),
    ("H1", "GP.42", 11, [("biginne", "sounded", "line-final infinitive")]),
    ("H1", "GP.43", 10, []),
    ("H1", "GP.44", 10, [("tyme", "sounded", "dative/etymological 'tyme' sounded before 'that'")]),
    ("H1", "GP.45", 11, [("chivalrye", "sounded", "line-final Romance -ye")]),
    ("H1", "GP.46", 11, [("Trouthe", "elided", "prevocalic before 'and'"), ("curteisye", "sounded", "line-final Romance -ye")]),
    ("H1", "GP.47", 11, [("werre", "sounded", "line-final noun -e")]),
    ("H1", "GP.48", 11, [("hadde", "elided", "elided before weak-h pronoun 'he'"), ("ferre", "sounded", "line-final comparative -e")]),
    ("H1", "GP.49", 11, [("hethenesse", "sounded", "line-final -esse")]),
    ("H1", "GP.50", 11, [("worthinesse", "sounded", "line-final -esse")]),
    # H2: CL.58 - CL.77 (20 non-contested rhyme-royal lines from Clerk's Tale Prima Pars)
    ("H2", "CL.58", 11, [("rote", "elided", "prevocalic before 'of'"), ("colde", "sounded", "line-final weak adjective")]),
    ("H2", "CL.59", 11, [("playne", "elided", "elided before Romance h-muet 'habundant'"), ("vitaille", "sounded", "line-final Romance -aille")]),
    ("H2", "CL.60", 11, [("biholde", "sounded", "line-final infinitive")]),
    ("H2", "CL.61", 11, [("were", "elided", "prevocalic before 'in'"), ("tyme", "elided", "prevocalic before 'of'"), ("olde", "sounded", "line-final plural adjective")]),
    ("H2", "CL.62", 11, [("delitable", "sounded", "syllabic -ble/-e before 'sighte'"), ("sighte", "sounded", "line-final noun -e")]),
    ("H2", "CL.63", 11, [("noble", "sounded", "syllabic -ble/-e before 'contree'"), ("highte", "sounded", "line-final preterite")]),
    ("H2", "CL.64", 11, [("londe", "sounded", "line-final dative -e")]),
    ("H2", "CL.65", 11, [("were", "elided", "elided before weak-h 'his'"), ("bifore", "sounded", "line-final adverbial -e")]),
    ("H2", "CL.66", 11, [("honde", "sounded", "line-final dative -e")]),
    ("H2", "CL.67", 11, [("Were", "elided", "prevocalic before 'alle'"), ("alle", "elided", "elided before weak-h 'his'"), ("bothe", "sounded", "sounded before 'lasse'"), ("lasse", "elided", "prevocalic before 'and'"), ("more", "sounded", "line-final comparative -e")]),
    ("H2", "CL.68", 11, [("yore", "sounded", "line-final adverbial -e")]),
    ("H2", "CL.69", 11, [("fortune", "sounded", "line-final Romance -e")]),
    ("H2", "CL.70", 11, [("Bothe", "elided", "prevocalic before 'of'"), ("commune", "sounded", "line-final Romance -e")]),
    ("H2", "CL.71", 11, [("speke", "elided", "prevocalic before 'as'"), ("linage", "sounded", "line-final Romance -age")]),
    ("H2", "CL.72", 11, [("gentilleste", "elided", "prevocalic before vocalic prefix 'y-born'"), ("Lumbardye", "sounded", "line-final Romance -ye")]),
    ("H2", "CL.73", 11, [("persone", "elided", "prevocalic before 'and'"), ("age", "sounded", "line-final Romance -age")]),
    ("H2", "CL.74", 11, [("curteisye", "sounded", "line-final Romance -ye")]),
    ("H2", "CL.75", 11, [("gye", "sounded", "line-final infinitive")]),
    ("H2", "CL.76", 11, [("Save", "elided", "prevocalic before 'in'"), ("somme", "silent", "apocopated before plural 'thinges'"), ("blame", "sounded", "line-final infinitive/noun")]),
    ("H2", "CL.77", 11, [("yonge", "sounded", "weak singular adjective 'this yonge lordes'"), ("name", "sounded", "line-final OE nama")]),
]


def build_reference_annotations(
    h1_doc: dict[str, Any], h2_doc: dict[str, Any]
) -> dict[str, Any]:
    line_lookup: dict[str, str] = {}
    for doc in (h1_doc, h2_doc):
        for st in doc["stanzas"]:
            for ln in st["lines"]:
                line_lookup[ln["ref"]] = ln["text"]

    records = []
    for set_id, ref, exp_sylls, decisions in REFERENCE_ANNOTATIONS_SPEC:
        text = line_lookup[ref]
        records.append(
            {
                "set_id": set_id,
                "ref": ref,
                "text": text,
                "expected_syllable_count": exp_sylls,
                "final_e_decisions": [
                    {"surface": surf, "expected": label, "reason": reason}
                    for surf, label, reason in decisions
                ],
                "commentary_source": (
                    "L. D. Benson (ed.), The Riverside Chaucer, 3rd ed., pp. xlii-xlv; "
                    "Harvard Geoffrey Chaucer Website, Lesson 2; W. W. Skeat (1900), vol. 5 notes."
                ),
            }
        )
    assert len(records) == 70, f"Expected 70 reference annotations, got {len(records)}"
    return {
        "metadata": base_metadata(
            "REF70",
            "70 reference-annotated lines (50 H1 + 20 H2) for final -e and syllable-count agreement",
            "pentameter_reference_annotations",
        ),
        "total_annotated_lines": len(records),
        "total_final_e_decisions": sum(len(r["final_e_decisions"]) for r in records),
        "lines": records,
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/extract_skeat_holdouts.py /path/to/22120-8.txt", file=sys.stderr)
        return 2

    src_path = Path(sys.argv[1])
    raw_bytes = src_path.read_bytes()
    actual_sha = sha256_bytes(raw_bytes)
    if actual_sha != EXPECTED_UPSTREAM_SHA256:
        raise SystemExit(
            f"Upstream SHA-256 mismatch: expected {EXPECTED_UPSTREAM_SHA256}, got {actual_sha}"
        )

    text = raw_bytes.decode("iso-8859-1").replace("\r\n", "\n")
    lines = text.split("\n")

    gp_400 = extract_section(
        lines, "GROUP A. THE PROLOGUE.", "THE KNIGHTES TALE.", first_line_no=1, max_lines=400, prefix="GP"
    )
    cl_140 = extract_section(
        lines,
        "THE CLERKES TALE.",
        "EXPLICIT PRIMA PARS.  INCIPIT SECUNDA PARS.",
        first_line_no=57,
        max_lines=140,
        prefix="CL",
    )
    th_60 = extract_section(
        lines,
        "SIR THOPAS.",
        "HERE THE HOST STINTETH CHAUCER OF HIS TALE OF THOPAS.",
        first_line_no=1902,
        max_lines=60,
        prefix="TH",
    )

    assert len(gp_400) == 400 and len(cl_140) == 140 and len(th_60) == 60

    out_dir = (
        Path(__file__).resolve().parents[1] / "data" / "s1_witnesses" / "blind_scansion"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    h1_doc = build_couplet_set(
        "H1",
        "General Prologue, lines 1-200 (Skeat 1900)",
        "Main recall set (riding-rhyme couplets)",
        gp_400[:200],
        couplet_offset=1,
    )
    h2_doc = build_h2_clerks_tale(cl_140)
    h3_doc = build_h3_sir_thopas(th_60)
    h4_doc = build_couplet_set(
        "H4",
        "General Prologue, lines 201-400 (Skeat 1900)",
        "Untouched second holdout reserved strictly for rescoring post-baseline rule changes",
        gp_400[200:400],
        couplet_offset=101,
    )
    n1_doc = build_n1_corrupted(h1_doc, h2_doc)
    ref70_doc = build_reference_annotations(h1_doc, h2_doc)

    files_to_write = {
        "h1_general_prologue_1_200.json": h1_doc,
        "h2_clerks_tale_stanzas_1_20.json": h2_doc,
        "h3_sir_thopas_1_60.json": h3_doc,
        "h4_general_prologue_201_400.json": h4_doc,
        "n1_corrupted_340.json": n1_doc,
        "reference_annotations_70.json": ref70_doc,
    }

    manifest_files: dict[str, dict[str, Any]] = {}
    for fname, payload in files_to_write.items():
        fpath = out_dir / fname
        serialized = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        fpath.write_bytes(serialized)
        manifest_files[fname] = {
            "sha256": sha256_bytes(serialized),
            "bytes": len(serialized),
            "set_id": payload["metadata"]["set_id"],
            "holdout_flag": payload["metadata"]["holdout_flag"],
        }

    manifest = {
        "plan_id": "validation-plan-02-blind-scansion",
        "holdout_flag": "EVALUATION_ONLY",
        "frozen_date": "2026-11-15",
        "edition": EDITION_CITATION,
        "upstream_repo": UPSTREAM_REPO_URL,
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_file": "22120-8.txt",
        "upstream_sha256": EXPECTED_UPSTREAM_SHA256,
        "extraction_script": "scripts/extract_skeat_holdouts.py",
        "files": manifest_files,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote frozen blind-scansion holdouts to {out_dir}:")
    for fname, info in manifest_files.items():
        print(f"  {fname:<36} sha256={info['sha256'][:16]}... ({info['bytes']} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
