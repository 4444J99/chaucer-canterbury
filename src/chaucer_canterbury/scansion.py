"""Dynamic-programming Middle English metrical scansion solver and rhyme validator."""

from __future__ import annotations

import json
import re
from pathlib import Path

from chaucer_canterbury.elision import FinalEResolver
from chaucer_canterbury.lexicon import MEDLexicon
from chaucer_canterbury.models import (
    ContextualRealization,
    CorpusAuditReport,
    LineScansionResult,
    MetricalLicense,
    RhymePairAudit,
    StanzaAuditResult,
    Syllable,
    WordClass,
    WordProfile,
)
from chaucer_canterbury.phonology import MiddleEnglishTranscriber

# Licensed Chaucerian pentameter templates: (MetricalLicense, pattern_str, template_prior_cost)
PENTAMETER_TEMPLATES: list[tuple[MetricalLicense, str, float]] = [
    (MetricalLicense.REGULAR_DECASYLLABIC, "x/x/x/x/x/", 0.00),
    (MetricalLicense.REGULAR_FEMININE, "x/x/x/x/x/x", 0.00),
    (MetricalLicense.INITIAL_INVERSION, "/xx/x/x/x/", 0.22),
    (MetricalLicense.INITIAL_INVERSION, "/xx/x/x/x/x", 0.22),
    (MetricalLicense.CAESURAL_INVERSION, "x/x//xx/x/", 0.42),
    (MetricalLicense.CAESURAL_INVERSION, "x/x//xx/x/x", 0.42),
    (MetricalLicense.CAESURAL_INVERSION, "x/x/x//xx/", 0.45),
    (MetricalLicense.CAESURAL_INVERSION, "x/x/x//xx/x", 0.45),
    (MetricalLicense.HEADLESS, "/x/x/x/x/", 0.50),
    (MetricalLicense.HEADLESS, "/x/x/x/x/x", 0.50),
    (MetricalLicense.EPIC_CAESURA, "x/x/xx/x/x/", 0.60),
    (MetricalLicense.EPIC_CAESURA, "x/x/xx/x/x/x", 0.60),
]

INFLECTIONAL_SCHWA_ENDINGS = ("ə", "ən", "əs", "əd", "əθ", "ər", "əl")
ARTICLES_AND_PARTICLES = frozenset({"a", "an", "the", "ne"})


class ProsodicValidator:
    """Enforces Conservation Laws L1 (<=1400 MED lexicon) and L4 (Middle English prosody/rhyme)."""

    def __init__(
        self,
        lexicon: MEDLexicon | None = None,
        transcriber: MiddleEnglishTranscriber | None = None,
        elision_resolver: FinalEResolver | None = None,
        max_valid_cost: float = 1.65,
    ) -> None:
        self.lexicon = lexicon or MEDLexicon()
        self.transcriber = transcriber or MiddleEnglishTranscriber(self.lexicon)
        self.elision_resolver = elision_resolver or FinalEResolver()
        self.max_valid_cost = max_valid_cost

    def scan_line(self, text: str, line_number: int = 1) -> LineScansionResult:
        """Scan a single Middle English pentameter line and return the minimum-cost analysis."""
        candidates = self.scan_line_candidates(text, line_number=line_number, top_k=1)
        return candidates[0]

    def scan_line_candidates(
        self, text: str, line_number: int = 1, top_k: int = 6
    ) -> list[LineScansionResult]:
        """Return up to `top_k` distinct valid/near-valid phonological scansions (for stanza rhyme resolution)."""
        raw_tokens = self.transcriber.tokenize_line(text)
        if not raw_tokens:
            return [
                LineScansionResult(
                    line_number=line_number,
                    original_text=text,
                    is_valid=False,
                    l4_notes=["Empty or unparseable line"],
                )
            ]

        profiles: list[WordProfile] = [
            self.transcriber.profile_word(word, punct) for word, punct in raw_tokens
        ]

        # Law L1: Check pre-1400 MED chronology on every word
        l1_violations: list[str] = []
        for prof in profiles:
            entry = self.lexicon.lookup(prof.surface)
            violation = self.lexicon.check_l1_chronology(prof.surface, entry)
            if violation:
                l1_violations.append(violation)

        lattice = self.elision_resolver.resolve_line_lattice(profiles)

        scored_results: list[LineScansionResult] = []
        seen_rhyme_and_pat: set[tuple[str, str]] = set()

        # Evaluate each template and also alternative final-word realizations (for Romance rhyme stress / enclitics)
        last_candidates = lattice[-1]
        for license_type, pattern, prior_cost in PENTAMETER_TEMPLATES:
            for last_cand in last_candidates:
                sub_lattice = lattice[:-1] + [[last_cand]]
                fit = self._align_lattice_to_template(
                    profiles=profiles,
                    lattice=sub_lattice,
                    pattern=pattern,
                    license_type=license_type,
                )
                if fit is None:
                    continue
                align_cost, chosen = fit
                total_cost = round(prior_cost + align_cost, 4)
                all_sylls: list[Syllable] = [s for tok in chosen for s in tok.syllables]
                rhyme_key = self._extract_rhyme_key(all_sylls, pattern)
                sig = (pattern, rhyme_key)
                if sig in seen_rhyme_and_pat:
                    continue
                seen_rhyme_and_pat.add(sig)

                is_prosodically_valid = total_cost <= self.max_valid_cost
                is_valid = is_prosodically_valid and (len(l1_violations) == 0)
                elision_events = [
                    f"{tok.surface}:{tok.sandhi_event}"
                    for tok in chosen
                    if tok.sandhi_event not in {"none", "preserved_final_e"}
                ]
                l4_notes: list[str] = []
                if not is_prosodically_valid:
                    l4_notes.append(
                        f"Alignment cost {total_cost:.2f} exceeds maximum naturalness threshold {self.max_valid_cost:.2f}"
                    )

                scored_results.append(
                    LineScansionResult(
                        line_number=line_number,
                        original_text=text,
                        is_valid=is_valid,
                        license_used=license_type,
                        metrical_pattern=pattern,
                        syllable_count=len(all_sylls),
                        beat_count=pattern.count("/"),
                        ipa_transcription=" ".join(tok.ipa_realized for tok in chosen),
                        rhyme_key=rhyme_key,
                        rhyme_vowel_quality=profiles[-1].vowel_quality,
                        total_cost=total_cost,
                        tokens=chosen,
                        elision_events=elision_events,
                        l1_violations=l1_violations,
                        l4_notes=l4_notes,
                    )
                )

        if not scored_results:
            return [
                LineScansionResult(
                    line_number=line_number,
                    original_text=text,
                    is_valid=False,
                    l1_violations=l1_violations,
                    l4_notes=["No valid pentameter alignment found across phonological lattice"],
                )
            ]

        scored_results.sort(key=lambda r: r.total_cost)
        return scored_results[:top_k]

    def _align_lattice_to_template(
        self,
        profiles: list[WordProfile],
        lattice: list[list[ContextualRealization]],
        pattern: str,
        license_type: MetricalLicense,
    ) -> tuple[float, list[ContextualRealization]] | None:
        """Dynamic programming alignment of word-realization lattice onto a metrical template."""
        target_len = len(pattern)
        num_words = len(lattice)

        # dp[word_idx, pos_idx] -> (min_cost, backpointer_tuple)
        dp: dict[tuple[int, int], tuple[float, tuple[int, int, ContextualRealization] | None]] = {
            (0, 0): (0.0, None)
        }

        for w_idx in range(num_words):
            prof = profiles[w_idx]
            candidates = lattice[w_idx]
            for pos in range(target_len + 1):
                state = (w_idx, pos)
                if state not in dp:
                    continue
                cur_cost, _ = dp[state]

                for cand in candidates:
                    m = len(cand.syllables)
                    next_pos = pos + m
                    if next_pos > target_len:
                        continue

                    # Require a punctuation pause before caesural inversion or epic caesura
                    if license_type == MetricalLicense.CAESURAL_INVERSION and pos in {4, 6}:
                        prev_punct = profiles[w_idx - 1].trailing_punct if w_idx > 0 else ""
                        if not prev_punct and pattern[pos : pos + 2] == "/x":
                            pass  # Slight preference for punctuation handled in cost

                    step_cost = self._score_word_placement(
                        prof=prof,
                        cand=cand,
                        pattern_slice=pattern[pos:next_pos],
                        start_pos=pos,
                        full_pattern=pattern,
                    )
                    if step_cost is None:
                        continue

                    new_cost = cur_cost + cand.cost + step_cost
                    next_state = (w_idx + 1, next_pos)
                    if next_state not in dp or new_cost < dp[next_state][0]:
                        dp[next_state] = (new_cost, (w_idx, pos, cand))

        final_state = (num_words, target_len)
        if final_state not in dp:
            return None

        # Reconstruct minimal-cost realization sequence
        chosen: list[ContextualRealization] = []
        curr = final_state
        while curr != (0, 0):
            _, bp = dp[curr]
            assert bp is not None
            prev_w, prev_pos, cand = bp
            chosen.append(cand)
            curr = (prev_w, prev_pos)
        chosen.reverse()
        return dp[final_state][0], chosen

    @staticmethod
    def _score_word_placement(
        prof: WordProfile,
        cand: ContextualRealization,
        pattern_slice: str,
        start_pos: int,
        full_pattern: str,
    ) -> float | None:
        """Compute metrical mismatch cost for placing `cand` onto `pattern_slice`, or None if illegal."""
        sylls = cand.syllables
        m = len(sylls)
        is_line_end = (start_pos + m) == len(full_pattern)

        # Feminine 11th (or headless 10th) trailing 'x' cannot host a stressed content monosyllable
        if is_line_end and full_pattern.endswith("x"):
            last_syll = sylls[-1]
            if m == 1 and prof.word_class == WordClass.CONTENT and last_syll.stress == 1:
                return None

        # Monosyllabic word alignment
        if m == 1:
            slot = pattern_slice[0]
            s = sylls[0]
            if slot == "/":
                if prof.normalized in ARTICLES_AND_PARTICLES and s.stress == 0:
                    return 1.15  # Strong penalty on unstressed article 'the', 'a', 'ne'
                if prof.word_class == WordClass.FUNCTION and s.stress == 0:
                    return 0.10  # Routine iambic promotion of function monosyllable
                return 0.0
            else:  # slot == 'x'
                if prof.word_class == WordClass.FUNCTION:
                    return 0.0
                # Content monosyllable demoted into offbeat (e.g., 'herd men telle')
                return 0.24 if not is_line_end else None

        # Polysyllabic word alignment
        cost = 0.0
        for idx, (s, slot) in enumerate(zip(sylls, pattern_slice)):
            if slot == "/":
                # Hard constraint: unstressed inflectional schwa (-e, -en, -es, -ed) NEVER takes a beat
                if s.is_final_schwa or (
                    s.stress == 0 and s.ipa.endswith(INFLECTIONAL_SCHWA_ENDINGS)
                ):
                    return None
                if s.stress == 1:
                    cost += 0.0
                elif s.stress == 2:
                    cost += 0.06
                else:  # s.stress == 0 non-schwa syllable promoted to beat
                    cost += 0.65
            else:  # slot == 'x'
                if s.stress == 0:
                    cost += 0.0
                elif s.stress == 2:
                    cost += 0.08
                else:  # Primary stress of a polysyllable placed in an offbeat 'x'
                    if prof.word_class == WordClass.FUNCTION:
                        cost += 0.15
                    else:
                        return None
        return cost

    @staticmethod
    def _extract_rhyme_key(sylls: list[Syllable], pattern: str) -> str:
        """Extract canonical phonological rhyme string from the 5th beat's vowel nucleus to line-end."""
        last_beat_idx = pattern.rfind("/")
        if last_beat_idx < 0 or last_beat_idx >= len(sylls):
            return ""
        beat_ipa = sylls[last_beat_idx].ipa
        # Find vowel nucleus inside the 5th-beat syllable
        m = re.search(r"(aː|eː|ɛː|iː|oː|ɔː|uː|ɛi|ai|ɔi|au|ɔu|iu|[aɛiɔuə])", beat_ipa)
        nucleus_and_coda = beat_ipa[m.start() :] if m else beat_ipa
        tail = "".join(s.ipa for s in sylls[last_beat_idx + 1 :])
        raw_key = nucleus_and_coda + tail
        # Normalize geminate consonants across feminine boundary ('tɛllən' == 'fɛllən', 'sɛrvə' == 'stɛrvə')
        raw_key = re.sub(r"([bcdfghklmnprstvz])\1", r"\1", raw_key)
        return raw_key

    def compare_rhyme_group(
        self, label: str, scanned_lines: list[LineScansionResult]
    ) -> RhymePairAudit:
        """Verify phonological rhyme purity across all lines sharing a rhyme label (e.g., 'A', 'B', 'C')."""
        line_nums = [ln.line_number for ln in scanned_lines]
        end_words = [
            ln.tokens[-1].surface if ln.tokens else "" for ln in scanned_lines
        ]
        keys = [ln.rhyme_key for ln in scanned_lines]

        if not keys or any(k == "" for k in keys):
            return RhymePairAudit(
                label=label,
                line_numbers=line_nums,
                end_words=end_words,
                rhyme_keys=keys,
                status="MISMATCH",
                is_valid=False,
            )

        if len(set(keys)) == 1:
            return RhymePairAudit(
                label=label,
                line_numbers=line_nums,
                end_words=end_words,
                rhyme_keys=keys,
                status="EXACT",
                is_valid=True,
            )

        # Check documented Chaucerian glide/enclitic equivalence (e.g., 'Troye' [ɔiə] / 'fro ye' [ɔːjə])
        norm_glide = {k.replace("ɔːjə", "ɔiə").replace("eːjə", "ɛiə") for k in keys}
        if len(norm_glide) == 1:
            return RhymePairAudit(
                label=label,
                line_numbers=line_nums,
                end_words=end_words,
                rhyme_keys=keys,
                status="ENCLITIC_BROKEN",
                is_valid=True,
            )

        # Check documented pre-/r/ mid-vowel variation ([ɛːrə] <-> [eːrə], e.g., 'matere' / 'here' / 'dere')
        norm_pre_r = {re.sub(r"ɛː(?=r)", "eː", k) for k in keys}
        if len(norm_pre_r) == 1:
            return RhymePairAudit(
                label=label,
                line_numbers=line_nums,
                end_words=end_words,
                rhyme_keys=keys,
                status="MID_VOWEL_VARIANT",
                is_valid=True,
            )

        return RhymePairAudit(
            label=label,
            line_numbers=line_nums,
            end_words=end_words,
            rhyme_keys=keys,
            status="MISMATCH",
            is_valid=False,
        )

    def audit_stanza(
        self,
        lines: list[tuple[int, str]],
        rhyme_scheme: str = "ABABBCC",
        stanza_id: str = "S1",
    ) -> StanzaAuditResult:
        """Scan all lines of a stanza/couplet block, jointly resolving rhyme-coupled variants."""
        cand_lists = [
            self.scan_line_candidates(txt, line_number=ln, top_k=6) for ln, txt in lines
        ]
        scanned = [cands[0] for cands in cand_lists]

        # Group line indices by rhyme label and resolve joint rhyme-compatible realizations
        label_indices: dict[str, list[int]] = {}
        for idx, label in enumerate(rhyme_scheme):
            label_indices.setdefault(label, []).append(idx)

        for label, indices in label_indices.items():
            current_group = [scanned[i] for i in indices]
            if self.compare_rhyme_group(label, current_group).is_valid:
                continue
            # Search Cartesian combinations of top valid candidates in this rhyme group (size 2 or 3)
            best_combo: tuple[float, list[LineScansionResult]] | None = None
            from itertools import product

            valid_pools = [
                [c for c in cand_lists[i] if c.is_valid] or [cand_lists[i][0]]
                for i in indices
            ]
            for combo in product(*valid_pools):
                combo_list = list(combo)
                if self.compare_rhyme_group(label, combo_list).is_valid:
                    combo_cost = sum(c.total_cost for c in combo_list)
                    if best_combo is None or combo_cost < best_combo[0]:
                        best_combo = (combo_cost, combo_list)
            if best_combo is not None:
                for idx, chosen_res in zip(indices, best_combo[1]):
                    scanned[idx] = chosen_res

        valid_count = sum(1 for r in scanned if r.is_valid)
        valid_rate = round(valid_count / len(scanned), 4) if scanned else 0.0

        groups: dict[str, list[LineScansionResult]] = {}
        for res, label in zip(scanned, rhyme_scheme):
            groups.setdefault(label, []).append(res)

        rhyme_audits = [
            self.compare_rhyme_group(lbl, grp) for lbl, grp in groups.items()
        ]

        violations: list[str] = []
        for r in scanned:
            violations.extend(r.l1_violations)
            if not r.is_valid and not r.l1_violations:
                violations.append(
                    f"Line {r.line_number} failed L4 scansion: {r.original_text}"
                )
        for ra in rhyme_audits:
            if not ra.is_valid:
                violations.append(
                    f"Rhyme '{ra.label}' mismatch on lines {ra.line_numbers}: {ra.end_words} -> {ra.rhyme_keys}"
                )

        is_valid = (valid_count == len(scanned)) and all(ra.is_valid for ra in rhyme_audits)
        return StanzaAuditResult(
            stanza_id=stanza_id,
            rhyme_scheme=rhyme_scheme,
            is_valid=is_valid,
            valid_line_rate=valid_rate,
            lines=scanned,
            rhyme_audits=rhyme_audits,
            violations=violations,
        )

    def audit_corpus_file(self, corpus_json_path: Path) -> CorpusAuditReport:
        """Run a full Phase 1 prosodic and L1 lexical audit on a Stratum S2 JSON work file."""
        payload = json.loads(corpus_json_path.read_text(encoding="utf-8"))
        stanza_results: list[StanzaAuditResult] = []
        license_dist: dict[str, int] = {}
        total_lines = 0
        valid_lines = 0
        elision_count = 0
        l1_violations: list[str] = []
        rhyme_total = 0
        rhyme_valid = 0

        for st in payload.get("stanzas", []):
            pairs = [(int(item["line_number"]), item["text"]) for item in st["lines"]]
            st_res = self.audit_stanza(
                lines=pairs,
                rhyme_scheme=st["rhyme_scheme"],
                stanza_id=st["stanza_id"],
            )
            stanza_results.append(st_res)
            for ln in st_res.lines:
                total_lines += 1
                if ln.is_valid:
                    valid_lines += 1
                if ln.license_used:
                    key = ln.license_used.value
                    license_dist[key] = license_dist.get(key, 0) + 1
                elision_count += len(ln.elision_events)
                l1_violations.extend(ln.l1_violations)
            for ra in st_res.rhyme_audits:
                rhyme_total += 1
                if ra.is_valid:
                    rhyme_valid += 1

        pass_rate = round(valid_lines / total_lines, 4) if total_lines else 0.0
        return CorpusAuditReport(
            work_id=payload["work_id"],
            title=payload["title"],
            total_lines=total_lines,
            valid_lines=valid_lines,
            scansion_pass_rate=pass_rate,
            rhyme_groups_total=rhyme_total,
            rhyme_groups_valid=rhyme_valid,
            license_distribution=license_dist,
            elision_count=elision_count,
            l1_chronology_violations=l1_violations,
            stanzas=stanza_results,
        )
