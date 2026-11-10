"""Inter-word phonological sandhi and final -e elision/apocope resolver."""

from __future__ import annotations

from chaucer_canterbury.models import (
    ContextualRealization,
    FinalEClass,
    PhonologicalVariant,
    Syllable,
    WordProfile,
)

STRONG_CAESURA_PUNCT = frozenset({";", ":", ".", "!", "?", "—", "–"})


class FinalEResolver:
    """Builds context-sensitive phonological lattices across a Middle English verse line."""

    def resolve_line_lattice(
        self, profiles: list[WordProfile]
    ) -> list[list[ContextualRealization]]:
        """Return candidate ContextualRealizations for every word position in a line."""
        n = len(profiles)
        lattice: list[list[ContextualRealization]] = []

        for idx, prof in enumerate(profiles):
            is_line_final = idx == n - 1
            next_prof = profiles[idx + 1] if not is_line_final else None
            has_strong_caesura = any(p in STRONG_CAESURA_PUNCT for p in prof.trailing_punct)

            word_candidates: list[ContextualRealization] = []
            seen_keys: set[tuple[str, str]] = set()

            for var in prof.variants:
                realizations = self._realize_variant_in_context(
                    prof=prof,
                    var=var,
                    is_line_final=is_line_final,
                    next_prof=next_prof,
                    has_strong_caesura=has_strong_caesura,
                )
                for r in realizations:
                    dedup_key = (
                        r.ipa_realized,
                        "".join(str(s.stress) for s in r.syllables),
                    )
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        word_candidates.append(r)

            lattice.append(word_candidates)

        return lattice

    def _realize_variant_in_context(
        self,
        prof: WordProfile,
        var: PhonologicalVariant,
        is_line_final: bool,
        next_prof: WordProfile | None,
        has_strong_caesura: bool,
    ) -> list[ContextualRealization]:
        out: list[ContextualRealization] = []
        ends_in_elidable_schwa = bool(var.syllables) and var.syllables[-1].is_final_schwa

        # Line-final position: etymological/inflectional final -e is ALWAYS sounded (feminine ending)
        if is_line_final:
            # Disallow apocopated variants at line-end when canonical form has inflectional/etymological -e
            if (
                prof.final_e_class in {FinalEClass.ETYMOLOGICAL, FinalEClass.INFLECTIONAL}
                and not var.ipa.endswith("ə")
            ):
                return []
            event = "preserved_final_e" if ends_in_elidable_schwa else "none"
            out.append(
                ContextualRealization(
                    surface=prof.surface,
                    ipa_realized=var.ipa,
                    syllables=[s.model_copy() for s in var.syllables],
                    sandhi_event=event,
                    cost=var.cost,
                )
            )
            return out

        assert next_prof is not None
        triggers_prevocalic = next_prof.starts_with_vowel
        triggers_weak_h = next_prof.weak_h

        if ends_in_elidable_schwa and (triggers_prevocalic or triggers_weak_h):
            elided_sylls = self._elide_final_schwa(var.syllables)
            if elided_sylls:
                elided_ipa = ".".join(
                    f"ˈ{s.ipa}" if s.stress == 1 else (f"ˌ{s.ipa}" if s.stress == 2 else s.ipa)
                    for s in elided_sylls
                )
                event_name = "elided_prevocalic" if triggers_prevocalic else "elided_weak_h"
                # Prevocalic / weak-h elision is the zero-cost default in Chaucerian meter
                out.append(
                    ContextualRealization(
                        surface=prof.surface,
                        ipa_realized=elided_ipa,
                        syllables=elided_sylls,
                        sandhi_event=event_name,
                        cost=var.cost,
                    )
                )

            # Across a strong syntactic pause (caesura), non-elision (hiatus / epic caesura) is possible at higher cost
            hiatus_penalty = 0.25 if has_strong_caesura else 0.85
            out.append(
                ContextualRealization(
                    surface=prof.surface,
                    ipa_realized=var.ipa,
                    syllables=[s.model_copy() for s in var.syllables],
                    sandhi_event="hiatus_retained",
                    cost=var.cost + hiatus_penalty,
                )
            )
            return out

        # Pre-consonantal context
        if ends_in_elidable_schwa:
            # Sounded pre-consonantal final -e (standard Chaucerian verse realization)
            out.append(
                ContextualRealization(
                    surface=prof.surface,
                    ipa_realized=var.ipa,
                    syllables=[s.model_copy() for s in var.syllables],
                    sandhi_event="preserved_final_e",
                    cost=var.cost,
                )
            )
            # In multi-syllable stems or optional-apocope words, pre-consonantal apocope can also occur
            apoc_cost = (
                0.08
                if prof.final_e_class == FinalEClass.OPTIONAL_APOCOPE
                else (0.35 if len(var.syllables) >= 2 else None)
            )
            if apoc_cost is not None:
                apoc_sylls = self._elide_final_schwa(var.syllables)
                if apoc_sylls:
                    apoc_ipa = ".".join(
                        f"ˈ{s.ipa}" if s.stress == 1 else (f"ˌ{s.ipa}" if s.stress == 2 else s.ipa)
                        for s in apoc_sylls
                    )
                    out.append(
                        ContextualRealization(
                            surface=prof.surface,
                            ipa_realized=apoc_ipa,
                            syllables=apoc_sylls,
                            sandhi_event="apocopated",
                            cost=var.cost + apoc_cost,
                        )
                    )
            return out

        # Monosyllabic function words ending in 'ə' ('the', 'ne') elide before vowels ('th'array', 'n'is')
        if (
            len(var.syllables) == 1
            and prof.normalized in {"the", "ne", "to"}
            and triggers_prevocalic
        ):
            out.append(
                ContextualRealization(
                    surface=prof.surface,
                    ipa_realized=var.ipa,
                    syllables=[s.model_copy() for s in var.syllables],
                    sandhi_event="none",
                    cost=var.cost,
                )
            )
            return out

        out.append(
            ContextualRealization(
                surface=prof.surface,
                ipa_realized=var.ipa,
                syllables=[s.model_copy() for s in var.syllables],
                sandhi_event="apocopated" if "apocope" in var.note else "none",
                cost=var.cost,
            )
        )
        return out

    @staticmethod
    def _elide_final_schwa(syllables: list[Syllable]) -> list[Syllable]:
        """Remove final unstressed schwa syllable and re-attach its onset consonants to previous coda."""
        if len(syllables) < 2:
            return []
        last = syllables[-1]
        if not last.ipa.endswith("ə"):
            return []
        residual_consonants = last.ipa[:-1]
        trimmed = [s.model_copy() for s in syllables[:-1]]
        trimmed[-1].ipa = trimmed[-1].ipa + residual_consonants
        trimmed[-1].is_final_schwa = False
        return trimmed
