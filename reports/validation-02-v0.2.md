# Validation Plan 02 Report (v0.2)

- **Plan ID:** `validation-plan-02-blind-scansion`
- **Engine Version:** `v0.2`
- **SHA-256 Manifest Verified:** `True`
- **Overall Threshold Verdict:** `PASS`

## Threshold Summary

| Metric | Result | Target | Status |
|---|---|---|---|
| Line Recall (H1-H3 non-contested) | 99.0% | >= 90.0% | PASS |
| Rhyme Recall (H1-H3 non-contested) | 99.5% | >= 95.0% | PASS |
| Corruption Rejection (N1 overall & min type) | 91.8% (min type 80.0%) | >= 85.0% overall, >= 70.0% per type | PASS |
| Final -e Agreement (70 Reference Lines) | 97.1% (101/104) | >= 85.0% | PASS |
| Generalization Gap (S2 Calibration - H1) | +2.0 pts | <= 10.0 pts | PASS |
| S4 Lexicon Token Coverage | 25.2% | Report only | REPORT |
| Untouched Holdout H4 (GP 201-400) Step 5 Rescore | 90.5% line / 78.0% couplet (H1-H4 gap +7.5 pts) | Report only (Step 5 overfitting check) | REPORT |

## Held-Out Positive Sets

| Set | Form | Non-Contested Lines | Line Recall | Contested (Accepted/Total) | Rhyme Recall | S4 Token Coverage |
|---|---|---:|---:|---:|---:|---:|
| H1 | `riding_rhyme_couplet` | 192/196 | 98.0% | 3/4 | 99.0% (95/96) | 23.7% |
| H2 | `rhyme_royal_ababbcc` | 138/138 | 100.0% | 1/2 | 100.0% (58/58) | 27.6% |
| H3 | `tail_rhyme_aabccb` | 59/59 | 100.0% | 1/1 | 100.0% (29/29) | 24.8% |
| H4 | `riding_rhyme_couplet` | 181/200 | 90.5% | 0/0 | 78.0% (78/100) | 22.2% |

## N1 Corruption Rejection Breakdown

| Corruption Type | Rejected / Total | Rejection Rate | Target-Gate Rate | >= 70% Floor |
|---|---:|---:|---:|---|
| `hypermetric_or_hypometric` | 84/91 | 92.3% | 92.3% | PASS |
| `mid_vowel_rhyme_violation` | 65/68 | 95.6% | 94.1% | PASS |
| `post_1400_anachronism` | 91/91 | 100.0% | 100.0% | PASS |
| `stress_inversion_collision` | 72/90 | 80.0% | 80.0% | PASS |

## Failure Taxonomy (H1-H3 Non-Contested)

| Failure Bucket | Count |
|---|---:|
| `lexicon_gap` | 2 |
| `final_e_rule` | 0 |
| `stress_or_lattice` | 2 |
| `rhyme_phonology` | 0 |
