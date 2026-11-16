# chaucer-canterbury

Computational linguistics, Middle English phonological modeling, blind-scansion holdout evaluation, and protocol-bound generative reconstruction for Geoffrey Chaucer's **Canterbury Tales**.

## Scope and Related Repositories

This repository (`chaucer-canterbury`) is the Middle English phonological, prosodic, author-operator, and generative pilgrimage workbench. Within the broader `4444J99` repository suite, each repository serves a distinct scope:

| Repository | Scope |
|---|---|
| [`4444J99/chaucer-canterbury`](https://github.com/4444J99/chaucer-canterbury) | Middle English phonology, WFST scansion & rhyme validation, blind-scansion holdout suite, parameterized `AUTHOR_DEFINITION`, 30-pilgrim `WORLD_STATE`, and constrained generative reconstruction (`Python` + `FastAPI` + `React/Vite` workbench) |
| [`4444J99/chaucer`](https://github.com/4444J99/chaucer) | Dedicated Chaucer literary/textual study repository separate from the generative pilgrimage engine |
| [`4444J99/hand-script`](https://github.com/4444J99/hand-script) | Paleographic and handwriting-centered script-learning study and annotated archive |
| [`4444J99/journal-handwritten-web`](https://github.com/4444J99/journal-handwritten-web) | Web presentation and reader surface for handwritten journal materials |
| [`4444J99/versforms`](https://github.com/4444J99/versforms) | General poetic and stanzaic verse-form modeling across traditions (distinct from late-14th-century London Middle English phonology) |

## Architectural Taxonomy

Rather than treating **The Canterbury Tales** as training text to memorize or imitate, this system formalizes Chaucer as a parameterized author-operator (`AUTHOR_DEFINITION`) acting inside the Southwark-to-Canterbury pilgrimage environment (`WORLD_STATE`). Extant **Canterbury Tales** witnesses (`S1`) remain strictly isolated from runtime calibration and generation (`EVALUATION_ONLY`, enforced statically and at runtime in `tests/test_blind_scansion.py`) so emergent road links and tales are synthesized from pre-1400 **compilatio** sources (`S5`), pilgrim sociolect profiles (`PILGRIM_DEFINITION`), Middle English clause syntax (`S3`), and pre-Great-Vowel-Shift lexical and prosodic laws (`S4`, `L1`–`L7`).

Specifications and reports:
- `specs/01-author-operator-and-pipeline.md` — Author-operator, world-state, generative core, and conservation laws `L1`–`L7`
- `specs/02-validation-plan-blind-scansion.md` — Blind scansion and rhyme holdout validation plan (`H1`–`H4`, `N1`, `REF70`)
- `docs/PROVENANCE.md` — Edition provenance, SHA-256 manifest inventory, and stratum isolation boundaries
- `reports/validation-02-report.md` — Full comparison of untouched `v0.1-baseline` vs. `v0.2` prosody and untouched `H4` generalization

## Implemented System Modules

- `PHONOLOGY_WORKBENCH` (`lexicon.py`, `phonology.py`, `elision.py`, `scansion.py`) — Stratum `S4` [Middle English Dictionary (MED)](https://quod.lib.umich.edu/m/middle-english-dictionary/about) lookup (`267` core lemmas + general pre-1400 Law `L1` chronological gate), late-14th-century London pre-GVS IPA transducer preserving etymological open versus close mid vowels (`/ɛː/` vs. `/eː/`, `/ɔː/` vs. `/oː/`) and sounded consonant clusters (`[kn]`, `[gn]`, `[wr]`, `[ç]`, `[x]`) ([Harvard Geoffrey Chaucer Website](https://chaucer.fas.harvard.edu/pages/great-vowel-shift)), prevocalic/weak-`h` final `-e` sandhi and proclitic synaloepha ([Harvard Lesson 3](https://chaucer.fas.harvard.edu/lesson-3)), and dynamic-programming scansion and stanza rhyme validator across `AABB` Riding Rhyme, `ABABBCC` Rhyme Royal, and `AABCCB` Tail Rhyme (`4-4-3-4-4-3` beats).
- `AUTHOR_DEFINITION` (`author_operator.py`, `data/s2_calibration/`, `data/s3_syntax/`) — Empirical calibration of Chaucer operator factors `F1`–`F6` strictly from non-Canterbury Chaucerian works (**Troilus and Criseyde** from [CMEPV](https://quod.lib.umich.edu/c/cme/Troilus/1:1.1?rgn=div2;view=fulltext), **The Legend of Good Women** from [Wikisource Skeat Edition](https://en.wikisource.org/wiki/The_Complete_Works_of_Geoffrey_Chaucer/Volume_3/The_Legend_of_Good_Women), and **Boece**) alongside [Penn-Helsinki Parsed Corpus of Middle English (PPCME2)](https://varieng.helsinki.fi/CoRD/corpora/PPCME2/) V2 inversion and negative-concord clause grammar.
- `WORLD_STATE` & `PILGRIM_DEFINITION` (`world_state.py`, `data/pilgrims/general_prologue_30.json`) — Stateful Kentish road itinerary (`Southwark` Mile `0` through `Canterbury` Mile `56`), `30` sociolect-parameterized General Prologue pilgrims (including all `7` historically silent or uncompleted manuscript pilgrims: Yeoman, Plowman, Haberdasher, Carpenter, Weaver, Dyer, Tapestry-Maker), Harry Bailly scheduling distribution, **quiting** grievance ledger, and **sentence**/**solaas** homeostasis.
- `CORPUS_SUBSTRATE` & `GENERATIVE_CORE` (`generator.py`, `witness.py`, `data/s5_sources/pre_1400_source_graphs.json`) — Five-stage holdout-blind synthesis engine across `16` pre-1400 **compilatio** narrative beat graphs, four formal vehicles (`riding_rhyme_couplet`, `rhyme_royal_ababbcc`, `tail_rhyme_aabccb`, `cadenced_prose_cursus`), and diplomatic witness projection modeling Hengwrt (`Hg`) and Ellesmere (`El`) orthography plus TEI-XML export ([Canterbury Tales Witnesses](https://www.dhi.ac.uk/manuscriptsonline/resources/ct/)).
- `VALIDATION_SUITE` (`validators.py`, `blind_scansion.py`, `data/s1_witnesses/`) — Dual validation harness combining (1) **Validation Plan 02 Blind Scansion & Rhyme** on SHA-256-frozen Skeat (1900) holdouts (`99.0%` `H1`–`H3` line recall, `99.5%` rhyme recall, `91.8%` `N1` corruption rejection across 340 items, `97.1%` final `-e` agreement on 70 annotated lines, `+2.0 pt` `S2`–`H1` generalization gap, and `90.5%` untouched `H4` GP 201–400 line recall) and (2) **Law L6 Counterfactual Suite** (`6/6` leave-one-tale-out and silent-pilgrim convergence with `0.0` 5-gram overlap).
- Fullstack Web Application (`server.py`, `webapp/`) — Portable FastAPI + SQLite REST backend serving a five-view React + Vite + Tailwind + shadcn/ui workbench (`GENERATIVE_CORE`, `PHONOLOGY_WORKBENCH`, `AUTHOR_DEFINITION`, `CORPUS_SUBSTRATE`, `VALIDATION_SUITE`).

## Quickstart: Installation, Tests, CLI, and Workbench Server

Install in editable mode with development tools:

```bash
pip install -e ".[dev]"
```

Run linting and all unit, isolation, holdout, and API integration tests:

```bash
ruff check src tests scripts
pytest -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run the Middle English prosody, blind-scansion holdout, and generative pipeline CLI:

```bash
chaucer-canterbury transcribe "The double sorwe of Troilus to tellen,"
chaucer-canterbury audit-corpus data/s2_calibration/troilus_book1_proem.json
chaucer-canterbury validate-holdout --set H1
chaucer-canterbury validate-holdout --set ALL --output reports/validation-02-v0.2.json
chaucer-canterbury calibrate-operator
chaucer-canterbury generate-turn --speaker plowman
chaucer-canterbury run-counterfactuals
```

Build the web frontend and launch the FastAPI workbench server (uses repo-relative `.local/studio.db` and `webapp/dist/public` by default, overrideable via `CHAUCER_DB_PATH` and `CHAUCER_STATIC_DIR`):

```bash
npm --prefix webapp install
npm --prefix webapp run check
npm --prefix webapp run build
chaucer-canterbury-server
```

## Open Owner Decisions

- **Repository License (`LICENSE`):** No open-source license has been assumed or added; `pyproject.toml` marks licensing as `Proprietary - owner decision pending` until the repository owner selects a license.
- **GitHub Visibility:** Created as a `--private` repository under `4444J99/chaucer-canterbury` pending owner review for public release.
