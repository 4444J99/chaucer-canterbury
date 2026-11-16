# Corpus Stratification, Edition Provenance, and Holdout Isolation

This document records the exact textual provenance, SHA-256 checksums, and isolation boundaries across Strata `S1`–`S5` of `chaucer-canterbury`.

---

## 1. Stratum Isolation Architecture

| Stratum | Directory | Runtime Access | Purpose |
|---|---|---|---|
| **S1** (`WITNESS_HOLDOUT`) | `data/s1_witnesses/` | **Evaluation only** (`EVALUATION_ONLY` enforced by static & runtime tests in `tests/test_blind_scansion.py`) | Held-out *Canterbury Tales* verse (`H1`–`H4`), adversarial corruptions (`N1`), reference `-e` annotations (`REF70`), and Law L6 non-copying reference index |
| **S2** (`CALIBRATION_CORPUS`) | `data/s2_calibration/` | Read by `author_operator.py` and `/api/corpus-audit` | Non-*Canterbury* Chaucer works (*Troilus and Criseyde* Book I proem, *Legend of Good Women* prologue, *Boece*) used to calibrate `AUTHOR_DEFINITION` (`F1`–`F6`) |
| **S3** (`CLAUSE_SYNTAX`) | `data/s3_syntax/` | Read by `author_operator.py` and `generator.py` | Late-14th-century Middle English V2 inversion and negative-concord clause templates modeled on PPCME2 |
| **S4** (`MED_LEXICON`) | `data/s4_lexicon/` | Read by `lexicon.py` and `phonology.py` | `267`-lemma core *Middle English Dictionary* (`MED`) phonological lexicon plus pre-1400 Law L1 chronological gate |
| **S5** (`COMPILATIO_SOURCES`) | `data/s5_sources/` | Read by `generator.py` | `16` pre-1400 Latin, Old French, Anglo-Norman, and Trecento Italian narrative beat graphs used by the generative core |

---

## 2. Validation Plan 02 (`data/s1_witnesses/blind_scansion/`)

All positive held-out *Canterbury Tales* passages (`H1`–`H4`) were extracted once and frozen with SHA-256 verification (`data/s1_witnesses/blind_scansion/manifest.json`) via `scripts/extract_skeat_holdouts.py` before running the untouched baseline (`reports/validation-02-baseline.json`).

- **Primary Edition:** Walter W. Skeat (ed.), *The Complete Works of Geoffrey Chaucer, Volume 4: The Canterbury Tales* (2nd ed., Oxford: Clarendon Press, 1900; public domain).
- **Upstream Digital Source:** [GITenberg `Chaucer-s-Works-Volume-4--of-7----The-Canterbury-Tales_22120`](https://github.com/GITenberg/Chaucer-s-Works-Volume-4--of-7----The-Canterbury-Tales_22120), commit `1e7f4c2ef672531d0676159202f2f9e2520e174c`, file `22120-8.txt`.
- **Source File SHA-256:** `2506000b31a78ae72dd9d1dd755fb3f305c42516b293960c222ad78509fc00db`.
- **Prosodic & Editorial Reference Authorities:**
  - Larry D. Benson (ed.), *The Riverside Chaucer* (3rd ed., Boston: Houghton Mifflin, 1987), "Language and Versification", pp. xxvi–xlv.
  - Bernhard ten Brink, *The Language and Metre of Chaucer*, rev. Friedrich Kluge, trans. M. Bentinck Smith (London: Macmillan, 1901).
  - Donka Minkova, *The History of Final Vowels in English* (Berlin: Mouton de Gruyter, 1991).
  - Harvard Geoffrey Chaucer Website ([chaucer.fas.harvard.edu](https://chaucer.fas.harvard.edu/)).

### Frozen Holdout Files (`manifest.json`)

| File | Set ID | Span in Skeat (1900) | Size | Role |
|---|---|---|---:|---|
| `h1_general_prologue_1_200.json` | `H1` | Fragment I (Group A), General Prologue lines `1–200` | 200 lines (`4` contested, `196` non-contested) | Primary couplet recall set |
| `h2_clerks_tale_stanzas_1_20.json` | `H2` | Fragment IV (Group E), Clerk's Tale Part I lines `57–196` | 140 lines / 20 rhyme-royal stanzas (`2` contested, `138` non-contested) | Stanza & rhyme recall set |
| `h3_sir_thopas_1_60.json` | `H3` | Fragment VII (Group B2), Tale of Sir Thopas lines `1902–1961` | 60 lines / 10 tail-rhyme stanzas (`1` contested, `59` non-contested) | Tail-rhyme (`AABCCB`) recall set |
| `h4_general_prologue_201_400.json` | `H4` | Fragment I (Group A), General Prologue lines `201–400` | 200 lines / 100 couplets | Untouched Step 5 overfitting holdout |
| `n1_corrupted_340.json` | `N1` | Deterministic single-corruption transforms of `H1` and `H2` | 340 items across 4 corruption categories | Adversarial precision set |
| `reference_annotations_70.json` | `REF70` | 50 `H1` lines + 20 `H2` lines (`104` contextual `-e` decisions) | 70 lines / 104 `-e` decisions | Contextual final `-e` benchmark |

---

## 3. Stratum S2–S5 Upstream Sources

- **Stratum S2 (*Troilus and Criseyde*, *Legend of Good Women*, *Boece*):**
  - [Corpus of Middle English Prose and Verse (CMEPV) — *Troilus and Criseyde*](https://quod.lib.umich.edu/c/cme/Troilus/1:1.1?rgn=div2;view=fulltext)
  - [Wikisource — Skeat Edition, Vol. 3: *The Legend of Good Women*](https://en.wikisource.org/wiki/The_Complete_Works_of_Geoffrey_Chaucer/Volume_3/The_Legend_of_Good_Women)
- **Stratum S3 (Clause Syntax):**
  - [Penn-Helsinki Parsed Corpus of Middle English, 2nd ed. (PPCME2)](https://varieng.helsinki.fi/CoRD/corpora/PPCME2/)
- **Stratum S4 (Lexicon & Chronological Gate):**
  - [University of Michigan *Middle English Dictionary* (MED)](https://quod.lib.umich.edu/m/middle-english-dictionary/about)
- **Diplomatic Witness Orthography Projection (`Hg` / `El`):**
  - Hengwrt MS (`Hg`): National Library of Wales MS Peniarth 392D ([Manuscripts Online — Canterbury Tales Witnesses](https://www.dhi.ac.uk/manuscriptsonline/resources/ct/))
  - Ellesmere MS (`El`): Huntington Library MS EL 26 C 9
