# chaucer-canterbury

Computational linguistics, Middle English phonological modeling, and protocol-bound generative reconstruction for Geoffrey Chaucer's **Canterbury Tales**.

## Architectural Posture

Rather than treating **The Canterbury Tales** as training text to memorize or imitate, this repository formalizes Chaucer as a parameterized **author-operator** (`AUTHOR_DEFINITION`) acting inside the Southwark-to-Canterbury pilgrimage environment (`WORLD_STATE`). Extant **Canterbury Tales** witnesses (`S1`) are held out from runtime generation so emergent links and tales are produced from pre-1400 **compilatio** sources (`S5`), pilgrim sociolect profiles (`PILGRIM_DEFINITION`), Middle English syntax (`S3`), and pre-Great-Vowel-Shift lexical and prosodic laws (`S4`, `L1–L7`).

Full design specification: `specs/01-author-operator-and-pipeline.md`.

## Phase 1 Modules Implemented

- `src/chaucer_canterbury/models.py` — Pydantic v2 contracts for four-tier Middle English word profiles, contextual sandhi realizations, pentameter scansions, rhyme-group audits, and corpus reports.
- `src/chaucer_canterbury/lexicon.py` — Stratum `S4` [Middle English Dictionary (MED)](https://quod.lib.umich.edu/m/middle-english-dictionary/about) lookup, scribal orthography normalization (`ff`, `ȝ`, `þ`, `u/v`, `i/j`, `ë`), function-word classification, and Conservation Law `L1` (`<= 1400 CE` attestation gate).
- `src/chaucer_canterbury/phonology.py` — Late-14th-century London Middle English grapheme-to-phoneme (IPA) transcriber preserving pre-Great-Vowel-Shift vowel heights (`/eː/` vs. `/ɛː/`, `/oː/` vs. `/ɔː/`), sounded clusters (`[kn]`, `[gn]`, `[wr]`, `[ç]`, `[x]`), Germanic prefix rules, and Romance stress doublets ([Harvard Geoffrey Chaucer Website](https://chaucer.fas.harvard.edu/pages/great-vowel-shift)).
- `src/chaucer_canterbury/elision.py` — Inter-word final `-e` sandhi resolver implementing prevocalic schwa elision, weak-`h` elision (pronouns, auxiliaries, French `h-muet` loans), petrified silent `-e` (`thise`, `hire`, `oure`), optional pre-consonantal apocope, and mandatory line-final feminine `-e` retention ([Harvard Lesson 3](https://chaucer.fas.harvard.edu/lesson-3)).
- `src/chaucer_canterbury/scansion.py` — Dynamic-programming lattice scansion validator and stanza-level joint rhyme resolver enforcing Conservation Law `L4` across `regular_decasyllabic`, `regular_feminine`, `initial_inversion`, `caesural_inversion`, `headless`, and `epic_caesura` templates for both Riding Rhyme (`AABB`) and Rhyme Royal (`ABABBCC`).
- `data/s2_calibration/` — Holdout-safe non-Canterbury Chaucer calibration datasets from **Troilus and Criseyde** ([CMEPV](https://quod.lib.umich.edu/c/cme/Troilus/1:1.1?rgn=div2;view=fulltext)) and **The Legend of Good Women** ([Wikisource Skeat Edition](https://en.wikisource.org/wiki/The_Complete_Works_of_Geoffrey_Chaucer/Volume_3/The_Legend_of_Good_Women)).

## Usage

Run the test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Profile Middle English phonology and final `-e` classes:

```bash
PYTHONPATH=src python3 -m chaucer_canterbury.cli transcribe "The double sorwe of Troilus to tellen,"
```

Scan a single pentameter line:

```bash
PYTHONPATH=src python3 -m chaucer_canterbury.cli scan-line "Help me that am the sorwful instrument"
```

Audit a Stratum `S2` calibration work:

```bash
PYTHONPATH=src python3 -m chaucer_canterbury.cli audit-corpus data/s2_calibration/troilus_book1_proem.json
PYTHONPATH=src python3 -m chaucer_canterbury.cli audit-corpus data/s2_calibration/legend_good_women_prol.json
```
