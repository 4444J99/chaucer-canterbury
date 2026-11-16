# Validation Plan 02 Report (v0.1-baseline)

- **Plan ID:** `validation-plan-02-blind-scansion`
- **Engine Version:** `v0.1-baseline`
- **SHA-256 Manifest Verified:** `True`
- **Overall Threshold Verdict:** `FAIL`

## Threshold Summary

| Metric | Result | Target | Status |
|---|---|---|---|
| Line Recall (H1-H3 non-contested) | 62.1% | >= 90.0% | FAIL |
| Rhyme Recall (H1-H3 non-contested) | 36.6% | >= 95.0% | FAIL |
| Corruption Rejection (N1 overall & min type) | 77.1% (min type 51.1%) | >= 85.0% overall, >= 70.0% per type | FAIL |
| Final -e Agreement (70 Reference Lines) | 74.0% (77/104) | >= 85.0% | FAIL |
| Generalization Gap (S2 Calibration - H1) | +25.5 pts | <= 10.0 pts | FAIL |
| S4 Lexicon Token Coverage | 25.2% | Report only | REPORT |
| Untouched Holdout H4 (GP 201-400) Line / Rhyme Recall | 73.0% / 50.0% | >= 90.0% / >= 95.0% | FAIL |

## Held-Out Positive Sets

| Set | Form | Non-Contested Lines | Line Recall | Contested (Accepted/Total) | Rhyme Recall | S4 Token Coverage |
|---|---|---:|---:|---:|---:|---:|
| H1 | `riding_rhyme_couplet` | 146/196 | 74.5% | 2/4 | 49.0% (47/96) | 23.7% |
| H2 | `rhyme_royal_ababbcc` | 95/138 | 68.8% | 2/2 | 34.5% (20/58) | 27.3% |
| H3 | `tail_rhyme_aabccb` | 3/59 | 5.1% | 0/1 | 0.0% (0/29) | 24.8% |
| H4 | `riding_rhyme_couplet` | 146/200 | 73.0% | 0/0 | 50.0% (50/100) | 22.2% |

## N1 Corruption Rejection Breakdown

| Corruption Type | Rejected / Total | Rejection Rate | Target-Gate Rate | >= 70% Floor |
|---|---:|---:|---:|---|
| `hypermetric_or_hypometric` | 91/91 | 100.0% | 100.0% | PASS |
| `mid_vowel_rhyme_violation` | 40/68 | 58.8% | 35.3% | FAIL |
| `post_1400_anachronism` | 85/91 | 93.4% | 37.4% | PASS |
| `stress_inversion_collision` | 46/90 | 51.1% | 51.1% | FAIL |

## Failure Taxonomy (H1-H3 Non-Contested)

| Failure Bucket | Count |
|---|---:|
| `lexicon_gap` | 54 |
| `final_e_rule` | 30 |
| `stress_or_lattice` | 65 |
| `rhyme_phonology` | 22 |
