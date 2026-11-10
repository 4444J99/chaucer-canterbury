"""Pydantic data contracts for Phase 1 Middle English phonology and scansion."""

from __future__ import annotations

from enum import Enum
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
    """Stanza and couplet vehicles in Chaucerian verse."""

    RIDING_RHYME = "riding_rhyme_couplet"      # AABB... decasyllabic/hendecasyllabic
    RHYME_ROYAL = "rhyme_royal_ababbcc"        # 7-line stanza ABABBCC


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
    sandhi_event: str = "none"  # "none" | "elided_prevocalic" | "elided_weak_h" | "apocopated" | "preserved_final_e"
    cost: float = 0.0


class LineScansionResult(BaseModel):
    """Deterministic scansion and Law L1/L4 validation output for a single verse line."""

    line_number: int = 1
    original_text: str
    is_valid: bool
    license_used: MetricalLicense | None = None
    metrical_pattern: str = ""                 # e.g., "x/x/x/x/x/x"
    syllable_count: int = 0
    beat_count: int = 0
    ipa_transcription: str = ""
    rhyme_key: str = ""                        # Phonological rhyme nucleus+coda(+feminine tail) from 5th beat
    rhyme_vowel_quality: str | None = None     # Tracks open_e/close_e/open_o/close_o when known
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
    status: str  # "EXACT" | "MID_VOWEL_VARIANT" | "ENCLITIC_BROKEN" | "MISMATCH"
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
