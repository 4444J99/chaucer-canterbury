# Validation Plan 02: Blind Scansion and Rhyme on Held-Out Chaucer Verse

Status: draft, 2026-11-14. Nothing in this plan has been run yet.

## Why this target

Law L4 (scansion and rhyme) is the gate that every generated line has to pass, so the claims about the generator depend on it. The current evidence for it is weak:

- `tests/test_scansion.py` reports 100% compliance on 44 lines: 28 from the Troilus Book I proem and 16 from the Legend of Good Women prologue (`data/s2_calibration/`).
- Those are the same lines the lexicon, the final -e rules, and the scansion lattice were built and tuned against. A score on them shows the system fits its own data, not that it generalizes.
- The core lexicon has 267 lemmas. We don't know how the transcriber handles real lines full of words it has never seen.
- If L4 wrongly rejects real Chaucer, or passes unmetrical lines, then the "100% L4" results for generated tales mean nothing.

Two measurements answer the question: (a) how often does the validator accept genuine Chaucer it has never seen, and (b) how often does it reject lines that have been broken on purpose?

## Holdout set (evaluation only)

| Set | Content | Size | Role |
|---|---|---|---|
| H1 | General Prologue 1–200 (riding-rhyme couplets) | 200 lines | Main recall set |
| H2 | Clerk's Tale or Man of Law's Tale stanzas (rhyme royal) | 140 lines (20 stanzas) | Stanza and rhyme recall |
| H3 | Sir Thopas (tail rhyme) | 60 lines | Tests the tail-rhyme form |
| N1 | Corrupted copies of H1 and H2 | about 340 lines | Precision set |

- Text source: one cited edition, chosen once and recorded with its URL (for example, the Harvard Chaucer site interlinear texts, or the Hengwrt transcription from the Canterbury Tales Project). Normalize spelling exactly as `phonology.py` already does.
- Store the sets in `data/s1_witnesses/blind_scansion/` with an `EVALUATION_ONLY` flag. Add a test that fails if any generator or calibration module can read this path.
- Freeze the sets with a SHA-256 manifest before the first run. Don't change rules after seeing H1–H3 failures without logging it (see Procedure).

N1 corruptions, about 1 per line, each tagged by type:
1. Insert or delete one syllable-bearing word (hypermetric or hypometric line).
2. Swap a rhyme word for a near-rhyme that breaks the open vs. close mid-vowel contrast (/ɛː/ vs. /eː/, /ɔː/ vs. /oː/).
3. Insert a post-1400 word (L1 chronology).
4. Reorder words so the stress pattern breaks but the syllable count stays the same.

## Reference annotation

- Mark the expected syllable count and the final -e decisions (sounded, elided, or silent) for 50 H1 lines and 20 H2 lines, citing standard metrical commentary (Benson's Riverside notes or the Harvard lessons) where they settle a disputed line.
- Mark lines editors treat as metrically irregular or textually uncertain as "contested". Report them separately, not as failures.

## Metrics and pass thresholds

| Metric | Definition | Pass |
|---|---|---|
| Line recall | Share of non-contested H1–H3 lines accepted as metrical | 90% or more |
| Rhyme recall | Share of genuine rhyme pairs or stanza schemes accepted | 95% or more |
| Corruption rejection | Share of N1 lines rejected, reported per corruption type | 85% or more overall, no type below 70% |
| Final -e agreement | Match with annotated -e decisions on the 70 reference lines | 85% or more |
| Lexicon coverage | Share of word tokens found in S4, vs. handled by fallback | Report only |
| Generalization gap | Recall on the S2 calibration lines minus recall on H1 | 10 points or less |

These thresholds are starting proposals. Change them before the run, not after.

## Procedure

1. Build and freeze H1–H3 and N1, then commit the manifest.
2. Add `cli validate-holdout --set H1` and a non-default test module, `tests/test_blind_scansion.py`, that writes a JSON report (per-line verdicts, failure reasons, metrics).
3. Run it once with no rule changes. Save that run as the baseline report.
4. Sort the failures into four groups: lexicon gap, -e rule, stress or lattice, and rhyme phonology.
5. Any later rule change goes in a changelog entry, and is re-scored on a second, untouched holdout (General Prologue 201–400) so we don't overfit to H1.

## Deliverables

- `data/s1_witnesses/blind_scansion/` (sets plus manifest)
- `tests/test_blind_scansion.py` and the `validate-holdout` CLI command
- `reports/validation-02-baseline.json` and a short Markdown write-up
- A Validation Suite view in the workbench showing recall and rejection rates per set

## Out of scope (later targets)

- Scaling up the non-copying (L6) check. Right now it compares 5-grams against only 56 reference lines (12 holdout sample lines plus the 44 calibration lines). That should be the next target after this one.
- Expert or human evaluation of whether generated tales read as Chaucerian.
- Testing the counterfactual scenarios against real held-out fragments.
