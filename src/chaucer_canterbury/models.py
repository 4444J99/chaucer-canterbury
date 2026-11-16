"""Pydantic data contracts for chaucer-canterbury Phases 1-5."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class FinalEClass(str, Enum):
    """Historical behavior of word-final -e in Chaucer's London Middle English."""

    NONE = "none"                          # Does not end in orthographic -e
    ETYMOLOGICAL = "etymological"          # OE/OF root vowel reduced to -e (e.g., 'tale', 'sorwe', 'peyne')
    INFLECTIONAL = "inflectional"          # Weak adj, infinitive, subjunctive, dat. sg. (e.g., 'write', 'parte')
    OPTIONAL_APOCOPE = "optional_apocope"  # High-frequency variable -e (e.g., 'have', 'were', 'sone', 'louynge')
    PETRIFIED_SILENT = "petrified_silent"  # Orthographic -e silent in speech/verse (e.g., 'thise', 'hire', 'oure')
    MONOSYLLABIC_ROOT = "monosyllabic_root"  # Long vowel -e/-ee root, never elided as schwa (e.g., 'he', 'me', 'contree')


class WordClass(str, Enum):
    """Prosodic word category governing metrical beat promotion/demotion."""

    CONTENT = "content"    # Nouns, main verbs, adjectives, lexical adverbs
    FUNCTION = "function"  # Determiners, prepositions, pronouns, conjunctions, auxiliaries


class MetricalLicense(str, Enum):
    """Chaucerian pentameter templates licensed under Law L4."""

    REGULAR_DECASYLLABIC = "regular_decasyllabic"            # x / x / x / x / x /   (10 sylls)
    REGULAR_FEMININE = "regular_feminine"                    # x / x / x / x / x / x (11 sylls)
    INITIAL_INVERSION = "initial_inversion"                  # / x x / x / x / x / (x)
    CAESURAL_INVERSION = "caesural_inversion"                # x / x / | / x x / x / (x)
    HEADLESS = "headless"                                    # / x / x / x / x / (x) (9 or 10 sylls)
    EPIC_CAESURA = "epic_caesura"                            # extra unstressed -e before midline pause


class MetricalForm(str, Enum):
    """Stanza, couplet, and prose vehicles in Chaucerian discourse."""

    RIDING_RHYME = "riding_rhyme_couplet"      # AABB... decasyllabic/hendecasyllabic
    RHYME_ROYAL = "rhyme_royal_ababbcc"        # 7-line stanza ABABBCC
    TAIL_RHYME = "tail_rhyme_sixain"           # 6-line burlesque tail-rhyme AABCCB
    CADENCED_PROSE = "cadenced_prose"          # Homiletic / philosophical prose treatise


class Syllable(BaseModel):
    """Single phonological syllable with IPA nucleus/margins and lexical stress."""

    ipa: str
    stress: int = Field(..., ge=0, le=2, description="0=unstressed, 1=primary, 2=secondary")
    is_final_schwa: bool = False


class PhonologicalVariant(BaseModel):
    """One historically licensed phonological realization of a Middle English word."""

    ipa: str
    syllables: list[Syllable]
    stress_pattern: str
    cost: float = Field(0.0, ge=0.0)
    note: str = "canonical"


class WordProfile(BaseModel):
    """Four-tier lexical and phonological profile for a tokenized word."""

    surface: str
    normalized: str
    lemma: str
    med_id: str | None = None
    etymon: str = "ME_RULE"
    earliest_year: int = 1390
    word_class: WordClass = WordClass.CONTENT
    final_e_class: FinalEClass = FinalEClass.NONE
    weak_h: bool = False
    starts_with_vowel: bool = False
    vowel_quality: str | None = None
    trailing_punct: str = ""
    variants: list[PhonologicalVariant]


class ContextualRealization(BaseModel):
    """Resolved realization of a word in line context after sandhi / final -e elision."""

    surface: str
    ipa_realized: str
    syllables: list[Syllable]
    sandhi_event: str = "none"
    cost: float = 0.0


class LineScansionResult(BaseModel):
    """Deterministic scansion and Law L1/L4 validation output for a single verse line."""

    line_number: int = 1
    original_text: str
    is_valid: bool
    license_used: MetricalLicense | None = None
    metrical_pattern: str = ""
    syllable_count: int = 0
    beat_count: int = 0
    ipa_transcription: str = ""
    rhyme_key: str = ""
    rhyme_vowel_quality: str | None = None
    total_cost: float = 0.0
    tokens: list[ContextualRealization] = Field(default_factory=list)
    elision_events: list[str] = Field(default_factory=list)
    l1_violations: list[str] = Field(default_factory=list)
    l4_notes: list[str] = Field(default_factory=list)


class RhymePairAudit(BaseModel):
    """Phonological audit of rhyming lines within a couplet or stanza."""

    label: str
    line_numbers: list[int]
    end_words: list[str]
    rhyme_keys: list[str]
    status: str
    is_valid: bool


class StanzaAuditResult(BaseModel):
    """Validation summary for a multi-line stanza or couplet block."""

    stanza_id: str
    rhyme_scheme: str
    is_valid: bool
    valid_line_rate: float
    lines: list[LineScansionResult]
    rhyme_audits: list[RhymePairAudit]
    violations: list[str] = Field(default_factory=list)


class CorpusAuditReport(BaseModel):
    """Aggregate Phase 1 calibration/validation report across a work."""

    work_id: str
    title: str
    total_lines: int
    valid_lines: int
    scansion_pass_rate: float
    rhyme_groups_total: int
    rhyme_groups_valid: int
    license_distribution: dict[str, int]
    elision_count: int
    l1_chronology_violations: list[str]
    stanzas: list[StanzaAuditResult]


# ============================================================================
# Phase 2: AUTHOR_DEFINITION Models
# ============================================================================


class AuthorDefinition(BaseModel):
    """Parameterized Chaucer operator C = <Theta_lex, Theta_syn, Theta_pros, K_comp, K_irony, Lambda_balance>."""

    dialect_base: str = "london_east_midland_1390"
    etymological_rom_gmc_ratio: float = Field(0.38, ge=0.0, le=1.0)
    etymology_distribution: dict[str, float] = Field(default_factory=dict)
    v2_topicalization_rate: float = Field(0.52, ge=0.0, le=1.0)
    negative_concord_rate: float = Field(0.84, ge=0.0, le=1.0)
    initial_inversion_rate: float = Field(0.11, ge=0.0, le=0.35)
    headless_line_rate: float = Field(0.02, ge=0.0, le=0.15)
    feminine_ending_rate: float = Field(0.48, ge=0.10, le=0.85)
    elision_per_line_rate: float = Field(0.42, ge=0.0, le=2.0)
    compilatio_digression_density: float = Field(0.20, ge=0.0, le=0.60)
    ironic_disclaimer_threshold: float = Field(0.60, ge=0.0, le=1.0)
    sentence_solaas_homeostasis: float = Field(0.50, ge=0.0, le=1.0)
    calibrated_works: list[str] = Field(default_factory=list)
    total_calibrated_tokens: int = 0
    total_calibrated_lines: int = 0


# ============================================================================
# Phase 3: WORLD_STATE & PILGRIM_DEFINITION Models
# ============================================================================


class PilgrimDefinition(BaseModel):
    """Generative agent profile for one General Prologue pilgrim (zero pre-assigned plots)."""

    id: str
    name: str
    role_title: str
    manuscript_status: str
    estate_vector: dict[str, float]
    dialect_profile: dict[str, Any]
    pragmatic_posture: dict[str, float]
    thematic_sensitivities: dict[str, float]
    prosodic_competence: dict[str, Any]
    social_couplings: dict[str, list[str]]
    occupational_lexicon: list[str]
    signature_oath: str


class QuitingEdge(BaseModel):
    """Directed social grievance / quiting tension edge u -> v in G_t."""

    source_pilgrim: str
    target_pilgrim: str
    weight: float = Field(..., ge=0.0, le=1.0)
    reason: str
    turn_updated: int = 0


class SpeakerCandidateScore(BaseModel):
    """Turn-selection probability breakdown for a pilgrim under W_{t-1}."""

    pilgrim_id: str
    pilgrim_name: str
    probability: float
    host_call_score: float
    grievance_drive: float
    fatigue_penalty: float
    would_interrupt: bool


class WorldState(BaseModel):
    """Boundary conditions W_t on the road from Southwark to Canterbury."""

    turn_index: int = 0
    route_stage_index: int = 0
    route_stage_name: str = "Southwark — Tabard Inn"
    mile_marker: int = 0
    time_of_day: str = "Day 1 Dawn"
    epistemic_horizon_year: int = 1400
    host_patience: float = 0.88
    rolling_sentence_level: float = 0.50
    rolling_solaas_level: float = 0.50
    last_speaker_id: str | None = None
    last_genre: str | None = None
    tales_told_by_pilgrim: dict[str, int] = Field(default_factory=dict)
    used_source_ids: list[str] = Field(default_factory=list)
    used_genres: list[str] = Field(default_factory=list)
    quiting_edges: list[QuitingEdge] = Field(default_factory=list)


# ============================================================================
# Phase 4 & 5: GENERATIVE_CORE & VALIDATION_SUITE Models
# ============================================================================


class TransposedBeat(BaseModel):
    """Single narrative beat after Stage 2 compilatio adaptation."""

    beat_id: str
    role: str
    causal_edge: str  # "initial" | "therefore" | "but"
    rhetorical_operation: str  # "translatio" | "amplificatio" | "abbreviatio" | "digressio" | "class_transposition"
    source_proposition: str
    adapted_proposition: str
    focus_lexicon: list[str]


class GeneratedVerseLine(BaseModel):
    """Single emitted Middle English line with phonological, lexical, and witness layers."""

    line_number: int
    section: str  # "link_prologue" | "tale_body"
    speaker_id: str
    middle_english: str
    modern_gloss: str
    hengwrt_orthography: str
    ellesmere_orthography: str
    ipa_transcription: str
    metrical_pattern: str
    syllable_count: int
    license_used: str
    rhyme_key: str
    elision_events: list[str] = Field(default_factory=list)
    etymons: list[str] = Field(default_factory=list)
    max_attestation_year: int = 1390


class EstateReaction(BaseModel):
    """Divergent pilgrim estate reception enforcing Conservation Law L7."""

    estate_group: str
    representative_pilgrim: str
    polarity: str  # "approving" | "mocking" | "contested" | "aggrieved"
    reaction_summary: str
    quiting_delta: float


class ConservationLawCheck(BaseModel):
    """Audit result for one of the seven hard conservation laws (L1-L7)."""

    law_id: str
    name: str
    passed: bool
    metric_label: str
    metric_value: str
    detail: str


class AnalyticalDiagnostics(BaseModel):
    """Ecosystem integration diagnostics (LingFrame, Narratological Lenses, Vox Governance)."""

    prosody_pass_rate: float
    rhyme_purity_rate: float
    romance_to_germanic_ratio: float
    kl_divergence_vs_s2: float
    v2_inversion_rate: float
    causal_binding_ratio: float
    alliteration_density: float
    vox_idiolect_alignment: float
    max_5gram_overlap_s1_s2: int
    max_line_levenshtein_s1_s2: float


class GeneratedTurnArtifact(BaseModel):
    """Complete Stage 1-5 generated pilgrimage link + tale artifact."""

    turn_id: int
    turn_index: int
    route_stage_name: str
    mile_marker: int
    speaker_id: str
    speaker_name: str
    speaker_role: str
    manuscript_status: str
    selection_mode: str  # "host_call" | "quiting_interruption" | "researcher_override"
    quiting_target_id: str | None = None
    source_id: str
    source_title: str
    source_auctor: str
    source_year: int
    genre: str
    metrical_form: MetricalForm
    sentence_score: float
    solaas_score: float
    link_lines: list[GeneratedVerseLine]
    beat_plan: list[TransposedBeat]
    tale_lines: list[GeneratedVerseLine]
    ellesmere_marginalia: list[str]
    tei_xml_apparatus: str
    estate_reactions: list[EstateReaction]
    host_verdict: str
    conservation_laws: list[ConservationLawCheck]
    diagnostics: AnalyticalDiagnostics


class CounterfactualScenarioResult(BaseModel):
    """Single leave-one-tale-out or silent-pilgrim counterfactual evaluation."""

    scenario_id: str
    held_out_fragment: str
    preceding_speaker: str
    emergent_speaker_id: str
    emergent_speaker_name: str
    selection_mode: str
    selected_genre: str
    selected_source_id: str
    structural_convergence: bool
    prosody_pass_rate: float
    max_5gram_overlap: int
    max_levenshtein_similarity: float
    non_copying_l6_passed: bool
    sample_couplet: list[str]


class CounterfactualSuiteReport(BaseModel):
    """Aggregate report for Phase 4 Holdout Counterfactual Suite."""

    total_scenarios: int
    convergent_scenarios: int
    all_l6_non_copying_passed: bool
    mean_prosody_pass_rate: float
    results: list[CounterfactualScenarioResult]


# ============================================================================
# Validation Plan 02: Blind Scansion & Rhyme Holdout Models
# ============================================================================


class HoldoutLineVerdict(BaseModel):
    """Per-line verdict on held-out Chaucerian verse (H1-H4)."""

    set_id: str
    stanza_id: str
    ref: str
    line_number: int
    text: str
    expected_beats: int = 5
    contested: bool = False
    contested_reason: str | None = None
    is_valid: bool
    metrical_pattern: str = ""
    syllable_count: int = 0
    beat_count: int = 0
    license_used: str | None = None
    total_cost: float = 0.0
    rhyme_key: str = ""
    elision_events: list[str] = Field(default_factory=list)
    oov_tokens: list[str] = Field(default_factory=list)
    failure_category: str | None = None
    failure_detail: str | None = None


class HoldoutRhymeVerdict(BaseModel):
    """Per-rhyme-group verdict on held-out Chaucerian verse."""

    set_id: str
    stanza_id: str
    label: str
    line_numbers: list[int]
    end_words: list[str]
    rhyme_keys: list[str]
    status: str
    has_contested_line: bool = False
    is_valid: bool


class HoldoutSetSummary(BaseModel):
    """Summary metrics for one positive held-out verse set (H1, H2, H3, or H4)."""

    set_id: str
    title: str
    metrical_form: str
    total_lines: int
    contested_lines: int
    contested_accepted: int
    non_contested_lines: int
    accepted_lines: int
    line_recall: float
    rhyme_groups_total: int
    rhyme_groups_non_contested: int
    rhyme_groups_accepted: int
    rhyme_recall: float
    total_tokens: int
    in_lexicon_tokens: int
    lexicon_token_coverage: float
    unique_types: int
    in_lexicon_types: int
    lexicon_type_coverage: float
    failure_counts: dict[str, int] = Field(default_factory=dict)


class CorruptionItemVerdict(BaseModel):
    """Per-item verdict on corrupted precision set N1."""

    corruption_id: str
    source_set: str
    source_ref: str
    corruption_type: str
    original_text: str
    corrupted_text: str
    rejected: bool
    rejected_by_target_gate: bool
    detail: str


class CorruptionTypeSummary(BaseModel):
    """Aggregate rejection metrics for one N1 corruption type."""

    corruption_type: str
    total_items: int
    rejected_items: int
    rejection_rate: float
    target_gate_rejected_items: int
    target_gate_rejection_rate: float
    passed_threshold_70pct: bool


class FinalEAgreementSummary(BaseModel):
    """Final -e decision and syllable-count agreement on the 70 annotated reference lines."""

    annotated_lines: int
    exact_syllable_matches: int
    syllable_match_rate: float
    total_decisions: int
    matched_decisions: int
    agreement_rate: float
    passed_threshold_85pct: bool
    mismatches: list[dict[str, Any]] = Field(default_factory=list)


class BlindScansionThresholdCheck(BaseModel):
    """Pass/fail check for one Validation Plan 02 metric."""

    metric_id: str
    label: str
    value: float
    display_value: str
    threshold_display: str
    passed: bool | None = None  # None for report-only metrics


class BlindScansionReport(BaseModel):
    """Complete Validation Plan 02 evaluation report."""

    plan_id: str = "validation-plan-02-blind-scansion"
    engine_version: str = "v0.1-baseline"
    manifest_verified: bool = True
    evaluated_sets: list[str]
    h1_h3_non_contested_lines: int = 0
    h1_h3_accepted_lines: int = 0
    h1_h3_line_recall: float = 0.0
    h1_h3_rhyme_groups_non_contested: int = 0
    h1_h3_rhyme_groups_accepted: int = 0
    h1_h3_rhyme_recall: float = 0.0
    h1_h3_lexicon_coverage: float = 0.0
    s2_calibration_recall: float = 0.0
    generalization_gap_points: float = 0.0
    n1_total_items: int = 0
    n1_rejected_items: int = 0
    n1_overall_rejection_rate: float = 0.0
    n1_min_type_rejection_rate: float = 0.0
    n1_by_type: list[CorruptionTypeSummary] = Field(default_factory=list)
    final_e_summary: FinalEAgreementSummary | None = None
    h4_untouched_summary: HoldoutSetSummary | None = None
    set_summaries: list[HoldoutSetSummary] = Field(default_factory=list)
    failure_taxonomy_totals: dict[str, int] = Field(default_factory=dict)
    threshold_checks: list[BlindScansionThresholdCheck] = Field(default_factory=list)
    all_thresholds_passed: bool = False
    line_verdicts: list[HoldoutLineVerdict] = Field(default_factory=list)
    rhyme_verdicts: list[HoldoutRhymeVerdict] = Field(default_factory=list)
    corruption_verdicts: list[CorruptionItemVerdict] = Field(default_factory=list)

