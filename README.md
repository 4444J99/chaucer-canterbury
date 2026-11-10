# chaucer-canterbury

Computational linguistics, Middle English phonological modeling, and protocol-bound generative reconstruction for Geoffrey Chaucer's **Canterbury Tales**.

## Architectural Taxonomy

Rather than treating **The Canterbury Tales** as training text to memorize or imitate, this system formalizes Chaucer as a parameterized author-operator (`AUTHOR_DEFINITION`) acting inside the Southwark-to-Canterbury pilgrimage environment (`WORLD_STATE`). Extant **Canterbury Tales** witnesses (`S1`) remain strictly isolated from runtime generation so emergent road links and tales are synthesized from pre-1400 **compilatio** sources (`S5`), pilgrim sociolect profiles (`PILGRIM_DEFINITION`), Middle English clause syntax (`S3`), and pre-Great-Vowel-Shift lexical and prosodic laws (`S4`, `L1`–`L7`).

Full design specification: `specs/01-author-operator-and-pipeline.md`.

## Implemented System Modules (Phases 1–5)

- `PHONOLOGY_WORKBENCH` (`lexicon.py`, `phonology.py`, `elision.py`, `scansion.py`) — Stratum `S4` [Middle English Dictionary (MED)](https://quod.lib.umich.edu/m/middle-english-dictionary/about) lookup (`267` pre-1400 lemmas + Law `L1` chronological gate), late-14th-century London pre-GVS IPA transducer preserving open versus close mid vowels (`/ɛː/` vs. `/eː/`, `/ɔː/` vs. `/oː/`) and sounded consonant clusters (`[kn]`, `[gn]`, `[wr]`, `[ç]`, `[x]`) ([Harvard Geoffrey Chaucer Website](https://chaucer.fas.harvard.edu/pages/great-vowel-shift)), prevocalic and weak-`h` final `-e` sandhi resolver ([Harvard Lesson 3](https://chaucer.fas.harvard.edu/lesson-3)), and WFST dynamic-programming pentameter and stanza rhyme validator (`AABB` Riding Rhyme and `ABABBCC` Rhyme Royal).
- `AUTHOR_DEFINITION` (`author_operator.py`, `data/s2_calibration/`, `data/s3_syntax/`) — Empirical calibration of Chaucer operator factors `F1`–`F6` strictly from non-Canterbury Chaucerian works (**Troilus and Criseyde** from [CMEPV](https://quod.lib.umich.edu/c/cme/Troilus/1:1.1?rgn=div2;view=fulltext), **The Legend of Good Women** from [Wikisource Skeat Edition](https://en.wikisource.org/wiki/The_Complete_Works_of_Geoffrey_Chaucer/Volume_3/The_Legend_of_Good_Women), and **Boece**) alongside [Penn-Helsinki Parsed Corpus of Middle English (PPCME2)](https://varieng.helsinki.fi/CoRD/corpora/PPCME2/) V2 inversion and negative-concord clause grammar.
- `WORLD_STATE` & `PILGRIM_DEFINITION` (`world_state.py`, `data/pilgrims/general_prologue_30.json`) — Stateful Kentish road itinerary (`Southwark` Mile `0` through `Canterbury` Mile `56`), `30` sociolect-parameterized General Prologue pilgrims (including all `7` historically silent or uncompleted manuscript pilgrims: Yeoman, Plowman, Haberdasher, Carpenter, Weaver, Dyer, Tapestry-Maker), Harry Bailly scheduling distribution, **quiting** grievance ledger, and **sentence**/**solaas** homeostasis.
- `CORPUS_SUBSTRATE` & `GENERATIVE_CORE` (`generator.py`, `witness.py`, `data/s5_sources/pre_1400_source_graphs.json`) — Five-stage holdout-blind synthesis engine across `16` pre-1400 **compilatio** narrative beat graphs ([Medieval Theory of Authorship](https://www.blackwellpublishing.com/content/bpl_images/content_store/sample_chapter/0631232893/Dalrymple_sample%20chapter_middle%20english%20literature.pdf)), four formal vehicles (`riding_rhyme_couplet`, `rhyme_royal_ababbcc`, `tail_rhyme_aabccb`, `cadenced_prose_cursus`), and dual diplomatic witness projection modeling Hengwrt (`Hg`, National Library of Wales MS Peniarth 392D) and Ellesmere (`El`, Huntington Library MS EL 26 C 9) orthography plus TEI-XML export ([Canterbury Tales Witnesses](https://www.dhi.ac.uk/manuscriptsonline/resources/ct/)).
- `VALIDATION_SUITE` (`validators.py`, `data/s1_witnesses/holdout_reference_index.json`) — Conservation Laws `L1`–`L7` runtime and holdout audit suite enforcing `<= 1400 CE` chronology, estate-register ceilings, Northern dialect conditioning (`gaan`/`staan`, `ik`, `sal`), `100%` WFST scansion compliance, `0` 5-gram overlap against `S1`/`S2` corpora (`L6`), and `6/6` leave-one-tale-out and silent-pilgrim counterfactual convergence.
- Fullstack Web Application (`server.py`, `webapp/`) — FastAPI + SQLite REST backend serving a five-view React + Vite + Tailwind + shadcn/ui workbench (`GENERATIVE_CORE`, `PHONOLOGY_WORKBENCH`, `AUTHOR_DEFINITION`, `CORPUS_SUBSTRATE`, `VALIDATION_SUITE`).

## Running the Test Suite, CLI, and Web Application

Run all `23` unit and integration tests across Phases 1–5:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run the Middle English prosody and generative pipeline CLI:

```bash
PYTHONPATH=src python3 -m chaucer_canterbury.cli transcribe "The double sorwe of Troilus to tellen,"
PYTHONPATH=src python3 -m chaucer_canterbury.cli audit-corpus data/s2_calibration/troilus_book1_proem.json
PYTHONPATH=src python3 -m chaucer_canterbury.cli calibrate-operator
PYTHONPATH=src python3 -m chaucer_canterbury.cli generate-turn --speaker plowman
PYTHONPATH=src python3 -m chaucer_canterbury.cli run-counterfactuals
```

Build the web frontend and launch the FastAPI workbench server:

```bash
cd webapp && npm install && npx vite build && cd ..
PYTHONPATH=src CHAUCER_WEBAPP_DIST=webapp/dist/public python3 -m uvicorn chaucer_canterbury.server:app --host 0.0.0.0 --port 5000
```
