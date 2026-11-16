export interface AuthorDefinition {
  dialect_base: string;
  etymological_rom_gmc_ratio: number;
  etymology_distribution: Record<string, number>;
  v2_topicalization_rate: number;
  negative_concord_rate: number;
  initial_inversion_rate: number;
  headless_line_rate: number;
  feminine_ending_rate: number;
  elision_per_line_rate: number;
  compilatio_digression_density: number;
  ironic_disclaimer_threshold: number;
  sentence_solaas_homeostasis: number;
  calibrated_works: string[];
  total_calibrated_tokens: number;
  total_calibrated_lines: number;
}

export interface QuitingEdge {
  source_pilgrim: string;
  target_pilgrim: string;
  weight: number;
  reason: string;
  turn_updated: number;
}

export interface WorldState {
  turn_index: number;
  route_stage_index: number;
  route_stage_name: string;
  mile_marker: number;
  time_of_day: string;
  epistemic_horizon_year: number;
  host_patience: number;
  rolling_sentence_level: number;
  rolling_solaas_level: number;
  last_speaker_id: string | null;
  last_genre: string | null;
  tales_told_by_pilgrim: Record<string, number>;
  used_source_ids: string[];
  used_genres: string[];
  quiting_edges: QuitingEdge[];
}

export interface RouteSegment {
  stage_index: number;
  name: string;
  mile: number;
  time_of_day: string;
}

export interface SpeakerCandidateScore {
  pilgrim_id: string;
  pilgrim_name: string;
  probability: number;
  host_call_score: number;
  grievance_drive: number;
  fatigue_penalty: number;
  would_interrupt: boolean;
}

export interface PilgrimDefinition {
  id: string;
  name: string;
  role_title: string;
  manuscript_status: string;
  estate_vector: Record<string, number>;
  dialect_profile: {
    base_region: string;
    northernism_rate: number;
    french_prestige_ceiling: number;
    latin_tag_rate: number;
  };
  pragmatic_posture: Record<string, number>;
  thematic_sensitivities: Record<string, number>;
  prosodic_competence: {
    preferred_forms: string[];
    metrical_regularity_target: number;
    syntax_complexity_ceiling?: number;
  };
  social_couplings: {
    allies: string[];
    natural_antagonists: string[];
  };
  occupational_lexicon: string[];
  signature_oath: string;
}

export interface SourceBeat {
  beat_id: string;
  role: string;
  edge: string;
  proposition: string;
  focus_lex: string[];
}

export interface SourceGraph {
  source_id: string;
  title: string;
  auctor: string;
  year_composed: number;
  language: string;
  genre: string;
  recommended_form: string;
  sentence_weight: number;
  solaas_weight: number;
  estate_affinity: Record<string, number>;
  thematic_tags: string[];
  provokes_pilgrims: string[];
  beats: SourceBeat[];
}

export interface TransposedBeat {
  beat_id: string;
  role: string;
  causal_edge: string;
  rhetorical_operation: string;
  source_proposition: string;
  adapted_proposition: string;
  focus_lexicon: string[];
}

export interface GeneratedVerseLine {
  line_number: number;
  section: string;
  speaker_id: string;
  middle_english: string;
  modern_gloss: string;
  hengwrt_orthography: string;
  ellesmere_orthography: string;
  ipa_transcription: string;
  metrical_pattern: string;
  syllable_count: number;
  license_used: string;
  rhyme_key: string;
  elision_events: string[];
  etymons: string[];
  max_attestation_year: number;
}

export interface EstateReaction {
  estate_group: string;
  representative_pilgrim: string;
  polarity: string;
  reaction_summary: string;
  quiting_delta: number;
}

export interface ConservationLawCheck {
  law_id: string;
  name: string;
  passed: boolean;
  metric_label: string;
  metric_value: string;
  detail: string;
}

export interface AnalyticalDiagnostics {
  prosody_pass_rate: number;
  rhyme_purity_rate: number;
  romance_to_germanic_ratio: number;
  kl_divergence_vs_s2: number;
  v2_inversion_rate: number;
  causal_binding_ratio: number;
  alliteration_density: number;
  vox_idiolect_alignment: number;
  max_5gram_overlap_s1_s2: number;
  max_line_levenshtein_s1_s2: number;
}

export interface GeneratedTurnArtifact {
  turn_id: number;
  turn_index: number;
  route_stage_name: string;
  mile_marker: number;
  speaker_id: string;
  speaker_name: string;
  speaker_role: string;
  manuscript_status: string;
  selection_mode: string;
  quiting_target_id: string | null;
  source_id: string;
  source_title: string;
  source_auctor: string;
  source_year: number;
  genre: string;
  metrical_form: string;
  sentence_score: number;
  solaas_score: number;
  link_lines: GeneratedVerseLine[];
  beat_plan: TransposedBeat[];
  tale_lines: GeneratedVerseLine[];
  ellesmere_marginalia: string[];
  tei_xml_apparatus: string;
  estate_reactions: EstateReaction[];
  host_verdict: string;
  conservation_laws: ConservationLawCheck[];
  diagnostics: AnalyticalDiagnostics;
}

export interface CounterfactualScenarioResult {
  scenario_id: string;
  held_out_fragment: string;
  preceding_speaker: string;
  emergent_speaker_id: string;
  emergent_speaker_name: string;
  selection_mode: string;
  selected_genre: string;
  selected_source_id: string;
  structural_convergence: boolean;
  prosody_pass_rate: number;
  max_5gram_overlap: number;
  max_levenshtein_similarity: number;
  non_copying_l6_passed: boolean;
  sample_couplet: string[];
}

export interface CounterfactualSuiteReport {
  total_scenarios: number;
  convergent_scenarios: number;
  all_l6_non_copying_passed: boolean;
  mean_prosody_pass_rate: number;
  results: CounterfactualScenarioResult[];
  updated_at?: string;
}

export interface HoldoutSetSummary {
  set_id: string;
  title: string;
  metrical_form: string;
  total_lines: number;
  contested_lines: number;
  contested_accepted: number;
  non_contested_lines: number;
  accepted_lines: number;
  line_recall: number;
  rhyme_groups_total: number;
  rhyme_groups_non_contested: number;
  rhyme_groups_accepted: number;
  rhyme_recall: number;
  total_tokens: number;
  in_lexicon_tokens: number;
  lexicon_token_coverage: number;
  unique_types: number;
  in_lexicon_types: number;
  lexicon_type_coverage: number;
  failure_counts: Record<string, number>;
}

export interface CorruptionTypeSummary {
  corruption_type: string;
  total_items: number;
  rejected_items: number;
  rejection_rate: number;
  target_gate_rejected_items: number;
  target_gate_rejection_rate: number;
  passed_threshold_70pct: boolean;
}

export interface FinalEAgreementSummary {
  annotated_lines: number;
  exact_syllable_matches: number;
  syllable_match_rate: number;
  total_decisions: number;
  matched_decisions: number;
  agreement_rate: number;
  passed_threshold_85pct: boolean;
  mismatches: {
    ref: string;
    surface: string;
    expected: string;
    actual: string;
    line_text: string;
    scanned_pattern: string;
  }[];
}

export interface BlindScansionThresholdCheck {
  metric_id: string;
  label: string;
  value: number;
  display_value: string;
  threshold_display: string;
  passed: boolean | null;
}

export interface BlindScansionReport {
  plan_id: string;
  engine_version: string;
  manifest_verified: boolean;
  evaluated_sets: string[];
  h1_h3_non_contested_lines: number;
  h1_h3_accepted_lines: number;
  h1_h3_line_recall: number;
  h1_h3_rhyme_groups_non_contested: number;
  h1_h3_rhyme_groups_accepted: number;
  h1_h3_rhyme_recall: number;
  h1_h3_lexicon_coverage: number;
  s2_calibration_recall: number;
  generalization_gap_points: number;
  n1_total_items: number;
  n1_rejected_items: number;
  n1_overall_rejection_rate: number;
  n1_min_type_rejection_rate: number;
  n1_by_type: CorruptionTypeSummary[];
  final_e_summary: FinalEAgreementSummary | null;
  h4_untouched_summary: HoldoutSetSummary | null;
  set_summaries: HoldoutSetSummary[];
  failure_taxonomy_totals: Record<string, number>;
  threshold_checks: BlindScansionThresholdCheck[];
  all_thresholds_passed: boolean;
}

export interface BlindScansionRunSummary {
  run_key: string;
  engine_version: string;
  target_set: string;
  updated_at: string;
  all_thresholds_passed: boolean;
  h1_h3_line_recall: number;
  h1_h3_rhyme_recall: number;
  n1_overall_rejection_rate: number;
}

export interface BlindScansionBundle {
  baseline: BlindScansionReport | null;
  current: BlindScansionReport;
  runs: BlindScansionRunSummary[];
  latest_run?: BlindScansionReport;
}

export interface StudioOverview {
  author_definition: AuthorDefinition;
  world_state: WorldState;
  route_segments: RouteSegment[];
  speaker_probabilities: SpeakerCandidateScore[];
  pilgrims: PilgrimDefinition[];
  source_graphs: SourceGraph[];
  turns: GeneratedTurnArtifact[];
  counterfactual_report: CounterfactualSuiteReport;
  blind_scansion?: BlindScansionBundle;
  lexicon_stats: {
    med_entries: number;
    epistemic_horizon_year: number;
    s2_works: string[];
    s2_calibrated_lines: number;
    s2_calibrated_tokens: number;
  };
}

export interface ContextualRealization {
  surface: string;
  ipa_realized: string;
  syllables: { ipa: string; stress: number; is_final_schwa: boolean }[];
  sandhi_event: string;
  cost: number;
}

export interface LineScansionResult {
  line_number: number;
  original_text: string;
  is_valid: boolean;
  license_used: string | null;
  metrical_pattern: string;
  syllable_count: number;
  beat_count: number;
  ipa_transcription: string;
  rhyme_key: string;
  rhyme_vowel_quality: string | null;
  total_cost: number;
  tokens: ContextualRealization[];
  elision_events: string[];
  l1_violations: string[];
  l4_notes: string[];
}

export interface StanzaAuditResult {
  stanza_id: string;
  rhyme_scheme: string;
  is_valid: boolean;
  valid_line_rate: number;
  lines: LineScansionResult[];
  rhyme_audits: {
    label: string;
    line_numbers: number[];
    end_words: string[];
    rhyme_keys: string[];
    status: string;
    is_valid: boolean;
  }[];
  violations: string[];
}

export interface ScanWorkbenchResponse {
  lines: LineScansionResult[];
  word_profiles: {
    surface: string;
    normalized: string;
    lemma: string;
    med_id: string | null;
    etymon: string;
    earliest_year: number;
    word_class: string;
    final_e_class: string;
  }[][];
  stanza_audit: StanzaAuditResult | null;
}

export interface CorpusAuditReport {
  work_id: string;
  title: string;
  total_lines: number;
  valid_lines: number;
  scansion_pass_rate: number;
  rhyme_groups_total: number;
  rhyme_groups_valid: number;
  license_distribution: Record<string, number>;
  elision_count: number;
  l1_chronology_violations: string[];
  stanzas: StanzaAuditResult[];
}
