# Chaucer-Canterbury Webapp Flows (`FLOWS.md`)

 Inventory recorded before editing `webapp/client/` (per incremental editing checklist).

## Existing Flows to Preserve

1. **Navigation & Shell (`AppShell.tsx`)**
   - Desktop persistent sidebar (`lg:flex`) and mobile drawer (`[data-testid="mobile-menu-btn"]`) navigate across all 5 hash routes (`#/`, `#/phonology`, `#/author`, `#/substrate`, `#/validation`).
   - Header status pills display current `world_state.route_stage_name`, mile marker, turn count, and rolling `sentence`/`solaas` percentages.
   - Theme toggle (`[data-testid="theme-toggle-btn"]`) toggles `.dark` on `document.documentElement` in memory without `localStorage`.

2. **Generative Core (`#/` — `GenerativeCorePage.tsx`)**
   - Loads initial `/api/overview` turn synthesis, route stage strip, speaker candidate probabilities, conservation law checks (`L1`–`L6`), and multi-witness text layers (`normalized`, `hengwrt`, `ellesmere`, `phonology`, `tei`).
   - Controls generate a new turn (`POST /api/generate-turn`) and reset pilgrimage state (`POST /api/world/reset`).

3. **Phonology Workbench (`#/phonology` — `PhonologyWorkbenchPage.tsx`)**
   -Preset buttons (`[data-testid="preset-troilus_proem"]`, `preset-lgw_couplets`, `preset-sandhi_elision`, `preset-adversarial_vowel`, `preset-adversarial_l1`) populate `[data-testid="phonology-textarea"]` and `[data-testid="scheme-select"]` and run `POST /api/scan`.
   - Displays stanza rhyme-band audit, per-line IPA/metrical pattern/syllable badges, per-token sandhi realizations, and S2 calibration audit (`GET /api/corpus-audit/troilus` and `lgw`).

4. **Author Definition (`#/author` — `AuthorDefinitionPage.tsx`)**
   - Displays empirically calibrated Factors `F1`–`F6` (`total_calibrated_lines`, etymology shares, V2 inversion, feminine ending rate, homeostasis) and persists operator slider adjustments or empirical reset via `POST /api/calibrate`.

5. **Corpus Substrate (`#/substrate` — `CorpusSubstratePage.tsx`)**
   - Switches between `30 Pilgrim Agents` (`[data-testid="subtab-pilgrims"]`) with search + estate filters and `16 Pre-1400 S5 Sources` (`[data-testid="subtab-sources"]`), and dispatches a chosen pilgrim to `#/` for turn synthesis.

6. **Validation Suite — Law L6 Counterfactuals (`#/validation` — `ValidationSuitePage.tsx`)**
   - Displays the 6 leave-one-tale-out and silent-pilgrim counterfactual scenarios and re-runs `POST /api/counterfactuals/run` via `[data-testid="rerun-counterfactuals-btn"]`.

## New / Modified Flows to Verify (`v0.2` Update)

1. **Validation Plan 02 Blind-Scansion Dashboard (`#/validation` — `ValidationSuitePage.tsx`)**
   - Sub-tab switcher toggles cleanly between `[data-testid="val-tab-plan02"]` (Validation Plan 02 Blind Scansion, default) and `[data-testid="val-tab-l6"]` (Law L6 Counterfactuals, preserving `[data-testid="rerun-counterfactuals-btn"]`).
   - Displays `v0.1-baseline` vs `v0.2` comparison across the 4 primary KPIs (`H1`–`H3` line recall `99.0%`, rhyme recall `99.5%`, `N1` corruption rejection `91.8%`, `REF70` final `-e` agreement `97.1%`), all 5 pass/fail threshold gates, `H1`–`H4` per-stratum table (marking `H4` as untouched overfitting check `90.5%`), 4 `N1` perturbation types, and 4-bucket failure taxonomy shift (`149 -> 4`).
   - Interactive set selector (`[data-testid="blind-target-select"]`) and run button (`[data-testid="run-blind-scansion-btn"]`) execute `POST /api/validation/blind-scansion/run` via `apiRequest` and render live run feedback + SQLite run history.

2. **Tail-Rhyme Sixain Scansion (`#/phonology` — `PhonologyWorkbenchPage.tsx`)**
   - `[data-testid="scheme-select"]` includes `AABCCB` (`Tail-Rhyme Sixain (6 lines AABCCB)`) and `[data-testid="preset-thopas_tail_rhyme"]` validates a 6-line `4/3`-beat tail-rhyme stanza via `POST /api/scan`.
