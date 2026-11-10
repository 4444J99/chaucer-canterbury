# Chaucer Author-Operator, Middle English Corpus, and Generative Pipeline Specification

## 1. Architectural Premise: Production vs. Copying

A conventional language-model workflow treats Geoffrey Chaucer's **Canterbury Tales** as training target text, optimizing token-level likelihood to imitate surviving passages. That approach memorizes surface phrasing from the 24 extant tales rather than modeling the generative process that produced them.

This system inverts that formulation. It models Chaucer not as a static text archive, but as a parameterized **author-operator** \(\mathcal{C}\) coupled to a **discourse environment** \(\mathcal{W}_t\) (the pilgrimage road from Southwark to Canterbury circa 1387–1400). The **Canterbury Tales**—both the 24 surviving tales and the roughly 96 uncompleted tales implied by Harry Bailly's four-tales-per-pilgrim contract in the General Prologue ([Harvard Geoffrey Chaucer Website](https://chaucer.fas.harvard.edu/summary-framing-narrative))—emerge as trajectories generated when \(\mathcal{C}\) resolves pilgrim agency, pre-1400 textual sources, late-fourteenth-century London sociolinguistics, and Middle English prosodic constraints inside \(\mathcal{W}_t\).

### The Holdout Counterfactual Principle

To guarantee that the pipeline **produces rather than copies**, the architecture enforces a strict epistemic split across its corpus strata:

1. **Generator Blindness to Target Tales:** Runtime generation never retrieves, quotes, or conditions on lines from **The Canterbury Tales** itself. The generator sees only pre-Chaucerian or contemporary source materials (such as Boccaccio, Boethius, Ovid, French fabliaux, saints' lives, and penitential manuals), Middle English lexical-phonological grammar, and the live state of the pilgrimage frame.
2. **Calibration-Only Parameter Extraction:** Surviving Chaucerian texts (primarily earlier works like **Troilus and Criseyde**, **The House of Fame**, **Boece**, and **The Legend of Good Women**, alongside leave-one-out folds of **The Canterbury Tales**) are used solely to estimate numerical operator invariants—such as Anglo-Saxon to Romance lexical ratios, syntactic inversion rates, metrical license probabilities, and rhetorical transition densities.
3. **Leave-One-Tale-Out Verification:** When an extant tale \(T_k\) is held out and the runtime environment is initialized at the exact frame state preceding \(T_k\) (for example, immediately after the Miller humiliates a carpenter, triggering the Reeve's retaliatory turn), a valid run must match \(T_k\)'s structural, sociolinguistic, and prosodic distributions while remaining strictly bounded away from \(T_k\) in n-gram overlap, line-level edit similarity, and verbatim plot sequence.

---

## 2. The Author-Operator (`AUTHOR_DEFINITION`)

In late-medieval scholastic literary theory, analyzed by Alastair Minnis in **Medieval Theory of Authorship**, vernacular writers positioned themselves not as autonomous modern creators inventing plots ex nihilo, but as **compilatores** (compilers) who select, arrange, translate, and frame authoritative material (**auctoritates**) while delegating moral and rhetorical responsibility to their speakers ([Blackwell Middle English Literature Extract](https://www.blackwellpublishing.com/content/bpl_images/content_store/sample_chapter/0631232893/Dalrymple_sample%20chapter_middle%20english%20literature.pdf); [McGill Medieval Authorship Study](https://mcgill.scholaris.ca/server/api/core/bitstreams/54fa0b4c-a694-4dfb-b7aa-c8f900032d7b/content)).

Accordingly, `AUTHOR_DEFINITION` encodes zero plot templates or memorized verses. Instead, it formalizes six computational factor groups that govern how the Chaucer operator transforms raw source matter and social friction into Middle English verse and prose.

### Factor Matrix of the Chaucer Operator

| Factor ID | Functional Component | First-Principles Mechanism | Measurable Linguistic / Structural Signatures |
| :--- | :--- | :--- | :--- |
| `F1` | **Dialectal & Lexical Matrix** | Late-14th-century London / East Midland base grammar mixed with French courtly/legal prestige loans, Latin scholastic terms, and regional English variants ([Cambridge: Chaucer and London English](https://www.cambridge.org/core/books/abs/geoffrey-chaucer-in-context/chaucer-and-london-english/5AFBC206E993EB610CD696DFBA25D661)). | Etymological register ratio \(\rho_{\text{Rom/Gmc}}\); regional phoneme/morpheme switches (such as Northern `/a:/` vs. Southern `/ɔ:/`, `ik` vs. `I`, `-es` vs. `-eth` 3sg. verb endings) deployed for character indexing or rhyme ([Harvard Middle English Dialects](https://chaucer.fas.harvard.edu/pages/middle-english-dialects); [Oxford Notes and Queries](https://academic.oup.com/nq/article-abstract/63/2/191/1752081?redirectedFrom=fulltext)). |
| `F2` | **Syntactic & Prosodic Engine** | Decasyllabic five-stress alternating meter (riding rhyme couplets `AABB` or rhyme royal `ABABBCC`) governed by historical final `-e` phonology, elision, apocope, and controlled initial variation ([Harvard Geoffrey Chaucer Website: Lesson 3](https://chaucer.fas.harvard.edu/lesson-3); [Harvard Rime Royal](https://chaucer.fas.harvard.edu/pages/rime-royal)). | Pronominal/nominal subject-verb inversion in topicalized clauses ([Penn Historical Corpora Notes](https://www.ling.upenn.edu/~kroch/omev2-html/node18.html)); initial trochaic inversion `/ x x /` preferred over headless nine-syllable lines `/ x / x / x / x /` in pentameter; ~40–50% feminine hendecasyllabic endings ([Bristol Prosody Study](https://research-information.bris.ac.uk/ws/files/139035778/Lines_without_anacrusis.pdf)). |
| `F3` | **Compilatory & Adaptive Operator** | Vernacular **translatio** and **compilatio**: recombining Italian novelle/epics, French fabliaux/romances, Ovidian myth, and Boethian philosophy rather than inventing plots from scratch ([Nagoya University Frame Study](https://www.lang.nagoya-u.ac.jp/proj/sosho/4/ramsey.pdf)). | Compression or amplification ratios across structural beats; insertion of Boethian/philosophical digressions (`apostrophe`, `exemplum`, `sententia`) into secular plots; explicit citation—real or fictive—of **auctores**. |
| `F4` | **Narratorial Self-Deprecation & Irony** | Splitting authorial consciousness between the orchestrating poet and a naive, accommodating pilgrim-reporter who claims merely to "rehearse" each speaker's words verbatim ([Blackwell Middle English Literature Extract](https://www.blackwellpublishing.com/content/bpl_images/content_store/sample_chapter/0631232893/Dalrymple_sample%20chapter_middle%20english%20literature.pdf)). | Unreliable praise superlatives ("a worthy man", "ther nas nikir"); paratactic juxtaposition of incompatible moral details without explicit editorial condemnation; strategic disclaimers before bawdy or heterodox speech. |
| `F5` | **Estates Polyphony & Ventriloquism** | Conditioning lexical, syntactic, and genre selection on three medieval estates (military/aristocratic, clerical, lay/mercantile-agrarian) plus urban guild mobility ([Cambridge: Chaucer and London English](https://www.cambridge.org/core/books/abs/geoffrey-chaucer-in-context/chaucer-and-london-english/5AFBC206E993EB610CD696DFBA25D661)). | Distinct pilgrim sociolect embeddings: polite plural `ye/yow` vs. intimate/contemptuous `thou/thee` pragmatics, occupational jargon density (legal, medical, alchemical, ecclesiastical, artisanal), and oath/swearing inventories. |
| `F6` | **Moral-Play Equilibrium (`Sentence` / `Solaas`)** | Dynamic tension between earnest moral instruction (`sentence`) and comic/aesthetic pleasure (`solaas`), resisting premature didactic closure until final penitential framing ([Harvard Summary of the Framing Narrative](https://chaucer.fas.harvard.edu/summary-framing-narrative)). | Alternation gradient across adjacent tales: high noble order -> disorderly comic subversion -> pointed personal rebuttal -> rhetorical/theological counter-thesis. |

### Formal Operator Representation

Let the author-operator \(\mathcal{C}\) be a tuple of invariant parameter vectors and transformation kernels calibrated from pre-Canterbury Chaucerian works and contemporary London/East Midland texts:

\[
\mathcal{C} = \langle \Theta_{\text{lex}}, \Theta_{\text{syn}}, \Theta_{\text{pros}}, \mathcal{K}_{\text{comp}}, \mathcal{K}_{\text{irony}}, \Lambda_{\text{balance}} \rangle
\]

- \(\Theta_{\text{lex}}\): Etymological and dialectal prior over the Middle English lexicon (Anglo-Saxon core, Anglo-Norman/Central French prestige layer, Latin clerical layer, Old Norse/Northern regional layer).
- \(\Theta_{\text{syn}}\): Constituency and clause-ordering grammar calibrated on Penn-Helsinki Middle English treebanks, including Chaucer's characteristic verb-second (V2) topicalization with both nominal and pronominal subjects ([Penn Historical Corpora Notes](https://www.ling.upenn.edu/~kroch/omev2-html/node18.html)).
- \(\Theta_{\text{pros}}\): Finite-state weighted transducer parameters governing syllable weight, final `-e` realization, syncopation, initial trochaic substitution, headless anacrusis omission, and rhyme-scheme lookahead.
- \(\mathcal{K}_{\text{comp}}\): Structural adaptation kernel mapping source-text beat graphs into Middle English narrative discourse via rhetorical operations (`abbreviatio`, `amplificatio`, `digressio`, `occupatio`).
- \(\mathcal{K}_{\text{irony}}\): Pragmatic divergence operator governing the distance between surface assertion (what the teller or pilgrim-narrator claims) and implied estates critique (what the detail pattern exposes).
- \(\Lambda_{\text{balance}}\): Homeostatic weight balancing `sentence` (doctrinal, philosophical, or ethical weight) against `solaas` (narrative velocity, comic reversal, sensory vividness).

---

## 3. Environment & Agent Protocols (`WORLD_STATE` and `PILGRIM_DEFINITION`)

The Chaucer operator does not generate in a vacuum. The **Canterbury Tales** exists because \(\mathcal{C}\) instantiates an interactive multi-agent social environment on the pilgrimage road from Southwark to Canterbury.

### 3.1 Pilgrimage Environment (`WORLD_STATE`)

`WORLD_STATE` \(\mathcal{W}_t\) tracks the boundary conditions at turn \(t \in \{1, \dots, N\}\):

1. **Spatial-Temporal Stage (`route_segment`):** Progression along the Kentish road (Tabard Inn at Southwark -> Deptford -> Greenwich -> Rochester -> Sittingbourne -> Boughton-under-Blean -> Canterbury, plus the projected return leg toward Southwark). Time of day and town proximity constrain tale length and Host impatience.
2. **Historical Epistemic Horizon (`horizon_1387_1400`):** Hard chronological filter prohibiting post-1400 lexical senses, post-Great-Vowel-Shift phonology, anachronistic historical events, or uncirculated texts.
3. **Host Arbitration State (`host_state`):** Harry Bailly acts as the in-world scheduler and aesthetic thermostat ([Nagoya University Frame Study](https://www.lang.nagoya-u.ac.jp/proj/sosho/4/ramsey.pdf)). He selects the next speaker by social rank, lot, or compensatory balance (for example, calling a monk after a knight, or demanding mirth after heavy pathos), interrupts tedious tales (as with Sir Thopas or the Monk), and scores `sentence` vs. `solaas`.
4. **Social Friction & `Quiting` Ledger (`quiting_matrix`):** Directed weighted graph \(G_t = (V, E_t)\) over all 30 pilgrims. Every completed tale updates edge weights representing professional insult, class rivalry, doctrinal disagreement, or thematic debt (such as the Miller "quiting" the Knight's courtly romance with a carpenter farce, and the Reeve—himself a carpenter—immediately "quiting" the Miller, or the Marriage Debate sequence across the Wife of Bath, Clerk, Merchant, and Franklin) ([Harvard Summary of the Framing Narrative](https://chaucer.fas.harvard.edu/summary-framing-narrative)).
5. **Genre & Motif Saturation (`discourse_memory`):** Tracks used genres, rhyme forms, authorities cited, and plot motifs across \(1 \dots t-1\) so subsequent speakers react to, invert, or escalate prior tales rather than repeating them.

### 3.2 Pilgrim Agent Definition (`PILGRIM_DEFINITION`)

Each pilgrim \(p_i \in P\) (including silent or uncompleted pilgrims in the surviving manuscripts: the Yeoman, Plowman, Haberdasher, Carpenter, Weaver, Dyer, Tapestry-Maker, Knight's Squire/Cook completions, and second/return tales for all speakers) is defined strictly by **generative properties, not pre-assigned plots**:

```yaml
pilgrim_definition:
  id: "plowman"
  estate_vector:
    bellatores: 0.00      # martial / aristocratic
    oratores: 0.25        # lay piety / brother to the Parson
    laboratores: 0.95     # agrarian manual labor
    urban_guild: 0.00     # mercantile / craft guild
  dialect_profile:
    base_region: "east_midland_rural"
    northernism_rate: 0.02
    french_prestige_ceiling: 0.12
    latin_liturgical_tag_rate: 0.08
  pragmatic_posture:
    pronoun_formality_bias: 0.65   # preference for 'ye' toward superiors, plain 'thou' among peers
    irony_capacity: 0.15           # earnest rather than duplicitous
    self_justification_drive: 0.10 # contrasts sharply with Pardoner (0.95) or Wife of Bath (0.90)
  thematic_sensitivities:
    tithe_and_charity: +0.90
    clerical_hypocrisy: +0.75
    courtly_luxury: -0.60
  prosodic_competence:
    preferred_forms: ["riding_rhyme_couplet", "stanzaic_complaint", "prose_homily"]
    metrical_regularity_target: 0.88
    syntax_complexity_ceiling: 0.45
  social_couplings:
    allies: ["parson", "knight"]
    natural_antagonists: ["miller", "reeve", "summoner", "pardoner"]
```

---

## 4. Five-Stratum Middle English & Source Corpus Architecture (`CORPUS_SUBSTRATE`)

To support phonological scansion, syntactic parsing, sociolect profiling, source-driven **compilatio**, and strict anti-copying verification, the corpus is organized into five distinct, cross-indexed strata.

### Corpus Strata Overview

| Stratum | Scope & Role | Primary Archival Sources | Encoding & Schema | Pipeline Partition |
| :--- | :--- | :--- | :--- | :--- |
| **S1: Manuscript & Witness Layer** | Diplomatic witnesses, scribal orthography, paratexts (incipits/explicits/glosses), and stemmatic variance. | [Norman Blake Canterbury Tales Editions](https://www.dhi.ac.uk/manuscriptsonline/resources/ct/) (Hengwrt, Ellesmere, Corpus Christi 198, Harley 7334, Lansdowne 851, Dd.4.24, Add. 35286) and Furnivall 6-Text XML in [Corpus of Middle English Prose and Verse (CMEPV)](https://quod.lib.umich.edu/c/cme/browse.html). | TEI-XML parallel witness alignment (`<app>`, `<rdg wit="#Hg #El">`), line IDs, rubric tags. | **Holdout / Evaluation & Optional Scribal Noising** (never exposed to story generator). |
| **S2: Chaucer Non-Canterbury & Contemporary London Layer** | Calibrating \(\mathcal{C}\)'s lexical, syntactic, and prosodic parameters without leaking **Canterbury Tales** plots or lines. | Chaucer's **Troilus and Criseyde**, **Boece**, **House of Fame**, **Parliament of Fowls**, **Legend of Good Women** via [CMEPV](https://quod.lib.umich.edu/c/cme/); Gower's **Confessio Amantis**, Langland's **Piers Plowman**, London guild/civic petitions. | Tokenized, normalized Middle English + speaker/narrator tags + stanza/meter annotations. | **Operator Parameter Calibration (`AUTHOR_DEFINITION` fitting)**. |
| **S3: Syntactic & Morphosyntactic Treebank Layer** | Historical grammar rules: V2 inversion, negative concord (`ne ... nat`), modal auxiliaries (`shal/sholde`, `moot/moste`), subordinating conjunctions. | [Penn-Helsinki Parsed Corpus of Middle English, 2nd ed. (PPCME2)](https://varieng.helsinki.fi/CoRD/corpora/PPCME2/) (~1.2M–1.5M words across 1150–1500 dialects/genres) and [Penn Parsed Corpora of Historical English](https://www.ling.upenn.edu/hist-corpora/). | Penn `.pos` and labelled bracketing `.psd` trees converted to Universal Dependencies + Constituency JSONL. | **Grammar Constraint Training & Syntactic Validator**. |
| **S4: Lexical, Etymological & Phonological Dictionary Layer** | Lemma normalization, 1100–1500 sense dating, etymological origin (OE, OF, AN, ON, Lat.), IPA phonetic transcription, and final `-e` grammar. | [Middle English Compendium / Middle English Dictionary (MED)](https://quod.lib.umich.edu/m/middle-english-dictionary/about) (54,081 entries; 891,531 dated quotations) + [CLTK Middle English](https://v0.cltk.org/en/latest/middle_english.html) phonological rules. | Relational lexicon (`med_id`, headword, variant spellings, etymon, earliest attestation date, syllable/stress template, inflectional `-e` class). | **Runtime Lexical Gating, Constrained Metrical Decoding, Anachronism Filter**. |
| **S5: Pre-1400 **Compilatio** Source Library** | The actual "desk of Chaucer": narrative, philosophical, scientific, and homiletic texts available to a multilingual London civil servant/poet circa 1390. | Boccaccio (**Decameron**, **Teseida**, **De Casibus**, **De Mulieribus Claris**), Ovid (**Metamorphoses**, **Heroides**), Boethius (**Consolatio**), **Roman de la Rose**, French fabliaux (**Recueil général**), **Legenda Aurea**, John Gower, Guillaume de Machaut, **Livre de Chasse**, medieval estates/penitential treatises. | Abstracted **Narrative Beat Graphs** + aligned source passages tagged by motif, genre, moral thesis, and social target. | **Runtime Source Input to Stage 2 (`source_selector` & `compilatio_planner`)**. |

### Ingestion & Normalization Pipeline for the Corpus

Middle English lacks fixed orthography (`shoures` / `schoures`, `swich` / `such` / `slyk`, `nyght` / `niȝt`). Treating raw surface forms as atomic tokens fractures statistical modeling while erasing purposeful dialectal signals. Every ingested token therefore carries a **four-tier representation**:

```json
{
  "line_id": "TC.1.1",
  "surface_diplomatic": "The double sorwe of Troilus to tellen",
  "tokens": [
    {
      "surface": "sorwe",
      "normalized_london_1390": "sorwe",
      "med_lemma_id": "MED41792",
      "lemma": "sorwe",
      "pos": "N-SG-DAT/ACC",
      "etymon_class": "OE",
      "earliest_date": 1150,
      "phonological_forms": [
        {"ipa": "ˈsɔr.wə", "syllables": 2, "stress": "10", "condition": "pre_consonantal_or_line_final"},
        {"ipa": "ˈsɔr.w",  "syllables": 1, "stress": "1",  "condition": "elided_pre_vocalic_or_h"}
      ]
    }
  ]
}
```

---

## 5. The Generative Model: Conservation Laws & Equations of Motion (`GENERATIVE_CORE`)

Following a protocol-bound architecture, the generator never optimizes toward "sounding vaguely medieval" or reproducing an extant plot summary. Instead, every generated link and tale is a trajectory through state space governed by **seven hard conservation laws (`L1–L7`)** and a **five-stage state-transition pipeline**.

### 5.1 Seven Conservation Laws (`L1–L7`)

Any candidate transition or decoded line violating `L1–L7` is rejected at generation time:

- **`L1` Chronological & Lexical Closure:** Every lemma and sense must be attested in Stratum S4 (`MED`) on or before `1400 CE`. Post-1400 vocabulary, Early Modern Shakespeareanisms, and pseudo-archaic "ye olde" coinages have probability zero.
- **`L2` Etymological-Estate Coherence:** A speaker's rolling ratio of Romance/Latinate (`OF`, `AN`, `Lat.`) to Germanic/Norse (`OE`, `ON`) content words must remain within the confidence interval defined by their `PILGRIM_DEFINITION` and current rhetorical posture—unless shifted deliberately for marked parody (as when a churl mimics courtly diction or a clerk mimics Northern speech in **The Reeve's Tale** ([Harvard Reeve's Tale Guide](https://chaucer.fas.harvard.edu/pages/reeves-tale))).
- **`L3` Compilatory Grounding (**Non-Ex-Nihilo** Plot Law):** Narrative plots are derived by transforming one or more pre-1400 source graphs from Stratum S5 via explicit adaptation operations (compression, frame-recontextualization, class transposition, genre inversion, or Boethian/Ovidian interpolation), matching medieval **compilatio** practice ([McGill Medieval Authorship Study](https://mcgill.scholaris.ca/server/api/core/bitstreams/54fa0b4c-a694-4dfb-b7aa-c8f900032d7b/content)).
- **`L4` Prosodic & Final-`-e` Phonological Well-Formedness:** Verse lines must admit at least one valid phonological scansion under late-14th-century Middle English rules:
  - Standard line: 5 metrical beats `(x) / x / x / x / x / (x)`.
  - Final `-e` (`[ə]`) is obligatorily **elided** before a following vowel or weak `h-` (`he`, `his`, `him`, `hire`, `han`, French loan `honour`), optionally apocopated in unstressed function words, and sounded before consonants or at line-end (producing a feminine 11-syllable ending) when etymologically or grammatically licensed (weak adjectives after determiners/vocatives, infinitives, preterite weak verbs, etymological OE/OF `-e`) ([Harvard Geoffrey Chaucer Website: Lesson 3](https://chaucer.fas.harvard.edu/lesson-3); [PMLA: Chaucer's Final -E](https://www.cambridge.org/core/journals/pmla/article/abs/chaucers-final-e/17B086DE28ED933B676AF7CC5D569B65)).
  - Metrical licenses are bounded to Chaucerian pentameter rates: initial trochaic inversion (`/ x x / ...`) is licensed at ~8–15% of lines; headless nine-syllable lines (`/ x / x / x / x /`) are rarer (~1–4%); adjacent non-elidable double offbeats outside resolution environments are forbidden ([Cambridge Birth of English Iambic Meter](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/4FB492EBAD6034D3AF04CA4EFB8B8A47/9781316562925c10_p259-271_CBO.pdf); [Bristol Prosody Study](https://research-information.bris.ac.uk/ws/files/139035778/Lines_without_anacrusis.pdf)).
- **`L5` Frame Causality & `Quiting` Conservation:** No tale begins without a resolved frame transition (`prologue` / `link`). Speaker selection and genre choice must be a lawful resolution of Host arbitration, social hierarchy, or accumulated `quiting` tension from prior turns.
- **`L6` Non-Copying / Holdout Divergence Bound:** Against all extant Chaucerian texts in S1 and S2, every generated passage must satisfy maximum contiguous n-gram overlap \(n < 5\) (excluding fixed Middle English closed-class function phrases and cited Latin scripture/proverbs), normalized line Levenshtein similarity \(< 0.62\), and distinct character/setting instantiation from extant **Canterbury Tales** witnesses.
- **`L7` Reception Non-Assertion:** Consistent with frame polyphony, neither a pilgrim narrator nor the Chaucer-pilgrim reporter may declare objective critical triumph; reception inside the frame collapses as a **divergent reaction distribution** across estates (for instance, "the gentils" praising what "the cherles" mock, or the Host misreading an allegory as domestic complaint) ([Harvard Summary of the Framing Narrative](https://chaucer.fas.harvard.edu/summary-framing-narrative)).

### 5.2 Runtime State-Transition Equations

At turn \(t\), given world state \(\mathcal{W}_{t-1}\), pilgrim population \(P\), and Chaucer operator \(\mathcal{C}\):

1. **Speaker & Interruption Resolution:**
   \[
   P(p_t \mid \mathcal{W}_{t-1}) \propto \exp\!\Big( \alpha \cdot \text{HostCall}(p_t, \mathcal{W}_{t-1}) + \beta \cdot \max_{q \prec t} \text{Grievance}(p_t, p_q) \cdot \text{Disinhibition}(p_t) - \gamma \cdot \text{Fatigue}(p_t) \Big)
   \]
   If \(\text{Grievance}(p_t, p_{t-1}) \cdot \text{Disinhibition}(p_t)\) exceeds threshold \(\tau_{\text{interrupt}}\) (for example, a drunken Miller or aggrieved Reeve/Summoner), \(p_t\) overrides Harry Bailly's scheduled call, generating a contentious link prologue.

2. **Genre, Stanza Form, and Source Selection:**
   \[
   (g_t, m_t, S_t) = \arg\max_{(g, m, S) \in \mathcal{G} \times \mathcal{M} \times \text{S5}} \Big[ \text{Affinity}(p_t, g, m) + \text{QuitingContrast}(g, g_{t-1}) + \Lambda_{\text{balance}}(\mathcal{W}_{t-1}, g) - \text{Saturation}(S, \mathcal{W}_{t-1}) + \epsilon_t \Big]
   \]
   where \(g_t\) is genre (chivalric romance, fabliau, Breton lay, saint's vita, exemplum, beast fable, estates confession, prose treatise), \(m_t\) is metrical vehicle (`riding_rhyme_couplet`, `rhyme_royal_ababbcc`, `tail_rhyme_parody`, or `cadenced_prose`), \(S_t \subset \text{S5}\) is an unused pre-1400 source graph, and \(\epsilon_t\) is bounded stochastic drift.

### 5.3 Five-Stage Generation Pipeline

```
[Stage 1: Frame & Link Engine]
  Input:  W_{t-1}, Quiting Matrix G_{t-1}, Pilgrim Definitions P
  Output: Next speaker p_t, Dramatic Link Prologue plan, Updated Host/Pilgrim tensions
          |
          v
[Stage 2: Compilatio & Narrative Beat Planner]
  Input:  p_t, Genre g_t, Source Graph S_t (from Stratum S5), Operator Kernel K_comp
  Output: Transposed Beat Graph B_t (causal chain: 'therefore'/'but' edges, rhetorical digressions, sententiae)
          |
          v
[Stage 3: Sociolect & Clause Realizer]
  Input:  Beat Graph B_t, Pilgrim Sociolect p_t, Syntax Grammar Theta_syn (PPCME2), Lexicon S4 (MED)
  Output: Semantic-Syntactic Clause Specifications + Candidate Rhyme Pairs (pre-planned per couplet/stanza)
          |
          v
[Stage 4: Constrained Prosodic & Phonological Decoder]
  Input:  Clause Specs, Rhyme Targets, Phonological Transducer Theta_pros
  Check:  Enforces L1 (<=1400 MED), L2 (etymon ratio), L4 (final -e elision/scansion), L6 (anti-copy filter)
  Output: Scanned Middle English Verse/Prose Lines + Explicit Phonological Scansion & Gloss Layer
          |
          v
[Stage 5: Frame Reception & Optional Scribal Witness Emitter]
  Input:  Completed Tale T_t, Pilgrim Population P, Witness Orthography Models (Hg / El from S1)
  Output: Estate-split pilgrim reactions -> W_t update; normalized edition + optional diplomatic witness JSON/TEI
```

#### Critical Technical Detail in Stage 4: Rhyme-First & Phonology-Constrained Decoding

Autoregressive left-to-right token generation routinely breaks strict meter and forces unnatural end-rhymes. Stage 4 resolves this through **two-pass prosodic realization**:

1. **Rhyme-Anchor Lookahead:** Before generating a couplet (`AA`) or rhyme-royal stanza (`ABABBCC`), the planner selects phonologically valid Middle English rhyme sets from Stratum S4 whose stressed vowel quality (distinguishing open `/ɛː/` vs. close `/eː/` and open `/ɔː/` vs. close `/oː/`, which Chaucer carefully separates in rhyme) and final `-e` inflection status match, while satisfying the semantic proposition of each beat.
2. **Weighted Finite-State Scansion Masking (WFST):** During token/word selection, a phonological tracker maintains partial metrical state across the ten (or eleven) positions of the pentameter line. Lookahead over the next word's initial phoneme dynamically resolves whether the current word's final `-e` elides (`0` syllables) or sounds (`1` unstressed syllable), pruning invalid stress collisions before surface emission.

---

## 6. Multi-Level Validation, Anti-Copying, and Ecosystem Integration

Generated tales are evaluated through deterministic diagnostics rather than subjective LLM self-grading, integrating directly with your existing repositories:

### 6.1 Integration with Existing Analytical Engines

| External Repository | Role in `chaucer-canterbury` Pipeline | Concrete Integration Surface |
| :--- | :--- | :--- |
| **[linguistic-atomization-framework](https://github.com/4444J99/linguistic-atomization-framework)** | Multilevel structural atomization (`tale -> stanza/verse-paragraph -> sentence/couplet -> word -> phoneme/grapheme`). | Adapts LingFrame's heuristic-honesty principle: measures marker densities (etymological strata, hypotaxis vs. parataxis, rhetorical figure density, phonetic alliteration/assonance) against S2 Chaucerian reference distributions without conflating marker density with aesthetic triumph. |
| **[narratological-algorithmic-lenses](https://github.com/4444J99/narratological-algorithmic-lenses)** | Auditing Stage 2 Beat Graphs (`B_t`) prior to verse realization. | Runs causal-binding diagnostics (`therefore`/`but` vs. episodic `and then`), scene necessity, reorderability, and dramatic irony/information-economy checks tailored to genre (`fabliau` requires tight mechanical farce causality; `saint's vita` permits episodic miracle escalation). |
| **[vox](https://github.com/4444J99/vox)** (Voice Governance) | Scoring pilgrim idiolect separation and Chaucerian narratorial invariants. | Computes pairwise stylistic distance across generated pilgrims (verifying the Plowman does not drift into the Pardoner's or Knight's register) and enforces anti-pattern rules against modern idioms or Victorian pseudo-medievalisms. |

### 6.2 Four Quantitative Validation Suites

1. **Prosodic Well-Formedness Audit (`prosody_audit`):**
   - Requires \(\ge 97\%\) of pentameter lines to parse cleanly under deterministic Middle English scansion rules (`regular`, `initial_inversion`, `headless`, `feminine_ending`, `epic_caesura`), with rhyme purity verified on reconstructed 1390 London vowel heights.
2. **Philological & Dialectal Calibration (`philology_audit`):**
   - Zero post-1400 `MED` sense violations (`L1`).
   - Kullback-Leibler divergence \(D_{\text{KL}}(P_{\text{gen}} \parallel P_{\text{S2}})\) on function-word distributions, V2 inversion rates, and etymological ratios within genre-specific bounds.
3. **Holdout Counterfactual Experiment (`holdout_counterfactual`):**
   - Hold out each of the 24 extant tales \(T_k\) one at a time. Run the pipeline from \(\mathcal{W}_{k-1}\). Measure:
     - **Structural Convergence:** Does the emergent turn select a compatible genre contrast, estate register, and `sentence`/`solaas` polarity?
     - **Non-Copying Guarantee:** Verify `L6` (5-gram overlap \(= 0\) on content sequences; plot graph edit distance \(> \delta_{\min}\)).
4. **Stemmatic & Apparatus Emission Check (`witness_audit`):**
   - Optional Stage 5 module applies scribal orthographic profiles modeled on Hengwrt (`Hg`, conservative East Midland spelling) vs. Ellesmere (`El`, more regularized spelling and fuller layout glosses) ([Norman Blake Canterbury Tales Editions](https://www.dhi.ac.uk/manuscriptsonline/resources/ct/)), emitting valid TEI-XML critical apparatus files compatible with stemmatic tools.

---

## 7. Reference Repository Layout & Core Data Contracts

When implemented as code inside this project or a linked repository, the system decomposes into six plain, role-based packages:

```
chaucer-canterbury/
├── specs/
│   └── 01-author-operator-and-pipeline.md
├── data/
│   ├── s1_witnesses/          # Holdout TEI-XML witnesses (Hg, El, 6-text CMEPV)
│   ├── s2_calibration/        # Troilus, Boece, Legend of Good Women, Gower, London civic texts
│   ├── s3_syntax/             # PPCME2 / Penn parsed clause patterns & V2 templates
│   ├── s4_lexicon/            # MED headwords, <=1400 sense dates, etymon tags, IPA + final -e classes
│   └── s5_sources/            # Pre-1400 compilatio beat graphs (Decameron, Ovid, fabliaux, vitae)
├── src/
│   ├── corpus/                # TEI ingesters, 4-tier tokenizer, MED normalizer, phoneme transcriber
│   ├── author_model/          # AUTHOR_DEFINITION parameter estimators & kernels (F1-F6)
│   ├── world_env/             # WORLD_STATE, PILGRIM_DEFINITION, Host scheduler, quiting graph G_t
│   ├── generator/             # Stage 1-5 pipeline, rhyme planner, WFST metrical constrained decoder
│   ├── validators/            # L1-L7 law checkers, scansion parser, anti-copying holdout suite
│   └── cli/                   # CLI entrypoints: corpus sync, calibrate, step-frame, generate-tale, audit
└── tests/                     # Unit tests for final -e elision, MED date gates, holdout non-copying
```

### Core Runtime Contracts (Python / Pydantic Sketch)

```python
from enum import Enum
from pydantic import BaseModel, Field


class MetricalForm(str, Enum):
    RIDING_RHYME = "riding_rhyme_couplet"      # AABB decasyllabic/hendecasyllabic
    RHYME_ROYAL = "rhyme_royal_ababbcc"        # 7-line stanza (high style / pathos / vita)
    TAIL_RHYME = "tail_rhyme_sixain"           # burlesque / romance parody
    CADENCED_PROSE = "cadenced_prose"          # homiletic / philosophical treatise (Melibee / Parson)


class AuthorDefinition(BaseModel):
    dialect_base: str = "london_east_midland_1390"
    v2_topicalization_rate: float = Field(..., ge=0.0, le=1.0)
    initial_inversion_rate: float = Field(0.11, ge=0.0, le=0.25)
    headless_line_rate: float = Field(0.02, ge=0.0, le=0.08)
    feminine_ending_rate: float = Field(0.45, ge=0.20, le=0.70)
    compilatio_digression_density: float = Field(0.18, ge=0.0, le=0.50)
    ironic_disclaimer_threshold: float = Field(0.60, ge=0.0, le=1.0)
    sentence_solaas_homeostasis: float = Field(0.50, ge=0.0, le=1.0)


class ScannedLine(BaseModel):
    line_number: int
    middle_english: str
    ipa_realization: str
    stress_pattern: str                        # e.g., "x/x/x/x/x/x" or "/xx/x/x/x/"
    license_used: str                          # "regular" | "initial_inversion" | "headless" | "elided_final_e"
    rhyme_phoneme_key: str                     # e.g., "oːtə" ("roote" / "soote")
    med_lemma_ids: list[str]
    max_attestation_year: int = Field(..., le=1400)
```

---

## 8. Immediate Implementation Sequence

1. **Phase 1 — Lexicon & Phonological Scansion Core (`S4` + `L1`/`L4`):** Build the deterministic Middle English phonological transcriber, final `-e` elision/apocope resolver, and pentameter/rhyme-royal scansion validator calibrated against **Troilus and Criseyde** (`S2`), holding **The Canterbury Tales** (`S1`) strictly out of generator memory.
2. **Phase 2 — Operator Calibration (`S2` + `S3` -> `AUTHOR_DEFINITION`):** Extract empirical distributions for `F1–F6` (etymological strata, V2 syntactic inversion, metrical variation rates, rhetorical apostrophe/sententia cadence) from Chaucer's non-Canterbury corpus and `PPCME2`.
3. **Phase 3 — Pilgrimage Environment & `Quiting` Graph (`WORLD_STATE` + 30 `PILGRIM_DEFINITION` files):** Encode all 30 General Prologue pilgrims—including the silent Yeoman, Plowman, and five Guildsmen—and Harry Bailly's turn-scheduling and interruption dynamics.
4. **Phase 4 — Source Graph Ingestion (`S5`) & Holdout Counterfactual Benchmark:** Encode an initial set of 15–20 pre-1400 source graphs (unadapted **Decameron** novelle, French fabliaux, Ovidian tales, **Livre de Chasse** excerpts, penitential complaint sources), run leave-one-tale-out counterfactual validation against extant fragments, and then execute forward runs into the ~96 uncompleted tales.
