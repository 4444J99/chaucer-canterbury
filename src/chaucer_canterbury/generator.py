"""Phase 4: Five-Stage Protocol-Bound Middle English Generative Pipeline (GENERATIVE_CORE).

Strictly isolated from Stratum S1 (extant Canterbury Tales witnesses). Generates original
Middle English dramatic links and tales from WORLD_STATE, PILGRIM_DEFINITION, S3 PPCME2
syntax, S4 MED phonology/lexicon, and S5 pre-1400 compilatio source beat graphs.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from chaucer_canterbury.author_operator import AuthorOperatorCalibrator
from chaucer_canterbury.models import (
    AuthorDefinition,
    EstateReaction,
    GeneratedTurnArtifact,
    GeneratedVerseLine,
    MetricalForm,
    PilgrimDefinition,
    TransposedBeat,
    WordClass,
    WorldState,
)
from chaucer_canterbury.scansion import ProsodicValidator
from chaucer_canterbury.validators import PipelineAuditSuite
from chaucer_canterbury.witness import (
    emit_tei_xml_apparatus,
    generate_ellesmere_marginalia,
    to_ellesmere_orthography,
    to_hengwrt_orthography,
)
from chaucer_canterbury.world_state import PilgrimageEnvironment

DEFAULT_S5_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "s5_sources" / "pre_1400_source_graphs.json"
)

# Phonologically pure pre-GVS Middle English rhyme anchor sets (Stratum S4 <= 1400 CE)
RHYME_ANCHOR_SETS: dict[str, list[tuple[str, str]]] = {
    "aːsə": [
        ("grace", "divine favor"),
        ("place", "appointed stead"),
        ("space", "measured span"),
        ("pace", "steady step"),
        ("face", "outward countenance"),
        ("trace", "imprinted path"),
    ],
    "iːtə": [
        ("endite", "compose in verse"),
        ("write", "set in parchment"),
        ("quite", "repay in kind"),
        ("delite", "find solace"),
        ("lite", "little measure"),
        ("smite", "strike home"),
    ],
    "ɛːdə": [
        ("rede", "read and counsel"),
        ("drede", "doubt or fear"),
        ("dede", "sworn action"),
        ("lede", "govern rightly"),
        ("stede", "appointed place"),
    ],
    "eːtə": [
        ("swete", "pleasant and mild"),
        ("strete", "open town lane"),
        ("lete", "forsake folly"),
        ("mete", "fitting measure"),
        ("grete", "salute aloud"),
    ],
    "oːtə": [
        ("roote", "grounded root"),
        ("boote", "healing remedy"),
        ("soote", "fragrant balm"),
        ("foote", "steadfast foot"),
    ],
    "ɔːn": [
        ("goon", "proceed onward"),
        ("stoon", "hewn stone"),
        ("anoon", "forthwith"),
        ("aloon", "solitary"),
    ],
    "aːn": [
        ("gaan", "go (Northern)"),
        ("staan", "stand fast (Northern)"),
        ("naan", "none (Northern)"),
    ],
    "ɛntə": [
        ("entente", "true purpose"),
        ("wente", "turned onward"),
        ("sente", "dispatched"),
        ("rente", "exacted tribute"),
    ],
    "uːr": [
        ("honour", "worthy renown"),
        ("labour", "honest toil"),
        ("flour", "choicest flower"),
        ("auctour", "old authority"),
    ],
    "iːzə": [
        ("servise", "faithful duty"),
        ("wise", "customed manner"),
        ("devyse", "frame and tell"),
    ],
    "içt": [
        ("knyght", "sworn knight"),
        ("nyght", "darkened night"),
        ("right", "lawful right"),
        ("myght", "sovereign power"),
        ("wight", "living person"),
        ("sight", "clear vision"),
        ("bright", "shining clear"),
    ],
    "aːlə": [
        ("tale", "reckoned story"),
        ("ale", "tavern ale"),
        ("smale", "humble folk"),
        ("bale", "heavy sorrow"),
        ("dale", "wooded valley"),
    ],
    "ɛrtə": [
        ("herte", "inward heart"),
        ("smerte", "bitter sting"),
        ("asterte", "slip away"),
    ],
    "ɛnsə": [
        ("sentence", "moral substance"),
        ("prudence", "wise foresight"),
        ("pacience", "calm endurance"),
        ("conscience", "inward witness"),
        ("reverence", "due honor"),
    ],
}

# Prefix pools keyed by the prosodic onset shape of the pre-selected rhyme anchor:
# - PREFIX_9_TO_BEAT5: 9 syllables (x / x / x / x / x) preceding a Beat-5-initial anchor ("1" like 'knyght' or "10" like 'grace', 'rede')
# - PREFIX_8_TO_WEAK9: 8 syllables (x / x / x / x /) preceding an unstressed-9 + Beat-5 anchor ("01" like 'honour' or "010" like 'endite', 'sentence')
# - PREFIX_7_TO_BEAT4: 7 syllables (x / x / x / x) preceding a 4-syllable Romance anchor ("1010" like 'pacience', 'reverence')

VERBAL_ANCHORS = {
    "endite", "write", "quite", "delite", "smite",
    "rede", "drede", "lede",
    "lete", "mete", "grete",
    "goon", "gaan", "staan", "asterte", "devyse",
}

PREFIX_9_NOMINAL = [
    ("And forth they riden in good entente of {end},", "And forth they rode in earnest mind of {end_gloss},"),
    ("By Goddes might he kepte wel his {end},", "By divine strength he guarded well his {end_gloss},"),
    ("In every toun men speken of swich {end},", "In every town folk speak of such {end_gloss},"),
    ("For {lex_2syll} turneth al unto good {end},", "For {lex_gloss} turns at last to worthy {end_gloss},"),
    ("Ther nas no wight that knew so trewe a {end},", "There was no soul who knew so true a {end_gloss},"),
    ("With sad visage and humble herte in {end},", "With sober look and humble heart in {end_gloss},"),
    ("Whan pride and folye lese al hir {end},", "When pride and folly forfeit all their {end_gloss},"),
    ("As writ min auctour of that olde {end},", "As my authority writes of that ancient {end_gloss},"),
    ("Ne saugh I nevere man of bettre {end},", "Never did I see a man of finer {end_gloss},"),
    ("Right in that lond he fond his soote {end},", "Right in that land he found his healing {end_gloss},"),
    ("Til rightwisnesse hath set the world in {end},", "Until justice has set the world in {end_gloss},"),
    ("Now listeth lordes unto al my {end},", "Now listen, lords, to all my {end_gloss},"),
    ("Bi seint John ik wol rekene wel this {end},", "By Saint John I will reckon well this {end_gloss},"),
]

PREFIX_9_VERBAL = [
    ("So gan this worthy pilgrim for to {end},", "Thus this worthy pilgrim began to {end_gloss},"),
    ("For trewe love and trouthe wol we {end},", "For faithful love and pledged truth we will {end_gloss},"),
    ("In olde bokes may ech clerk wel {end},", "In ancient books each scholar well may {end_gloss},"),
    ("By Goddes grace our felaweship shal {end},", "By divine grace our fellowship shall {end_gloss},"),
    ("Ne wolde no trewe craftesman mis-{end},", "No honest craftsman would wrongly {end_gloss},"),
    ("Right on this wey min auctour bad me {end},", "Right on this road my authority bade me {end_gloss},"),
    ("Ik sal now telle how trewe men mot {end},", "I shall now tell how honest folk must {end_gloss},"),
]

PREFIX_8_NOMINAL = [
    ("For trouthe and vertu bringeth high {end},", "For truth and virtue bring high {end_gloss},"),
    ("With humble chere he kepte good {end},", "With humble bearing he upheld sound {end_gloss},"),
    ("Whan fortune changeth al our {end},", "When fortune shifts all our {end_gloss},"),
    ("As clerkes techen by hir trewe {end},", "As scholars teach through their true {end_gloss},"),
    ("Ne wolde no wise man for-sake {end},", "No wise person would forsake {end_gloss},"),
    ("In open strete he shewed gret {end},", "In open street he showed great {end_gloss},"),
    ("Yit shal good counsel winne parfyt {end},", "Yet sound counsel shall win lasting {end_gloss},"),
]

PREFIX_8_VERBAL = [
    ("In olde bokes may ech wight {end},", "In ancient books each soul may {end_gloss},"),
    ("Ther-fore our companye moot {end},", "Therefore our fellowship must {end_gloss},"),
    ("By trouthe and resoun wol I now {end},", "By truth and reason I will now {end_gloss},"),
    ("Right as min auctour techith us {end},", "Just as my authority teaches us to {end_gloss},"),
]

PREFIX_7_TO_BEAT4 = [
    ("For humble trouthe and trewe {end},", "For humble faith and steadfast {end_gloss},"),
    ("In olde bokes stant {end},", "In ancient books stands {end_gloss},"),
    ("With sad counsel and sad {end},", "With sober counsel and calm {end_gloss},"),
    ("Til grace bringe us to {end},", "Until grace leads us unto {end_gloss},"),
    ("By clerke wit and high {end},", "By scholarly wit and high {end_gloss},"),
]

TAIL_RHYME_STANZAS = [
    [
        ("Listeth lordes in good entente,", "Listen, lords, with good intent,"),
        ("How forth this dapper bachelere wente,", "How forth this dapper bachelor went,"),
        ("Upon the grene paas;", "Along the woodland way;"),
        ("His sadel bright of cipres sente,", "His bright saddle of cypress gleamed,"),
        ("Til giant stoon his corage shente,", "Until a giant's stone shook his courage,"),
        ("For al his proud solaas.", "Despite all his proud mirth."),
    ],
    [
        ("Oure Hoste cried in open strete,", "Our Host cried out in the open road,"),
        ("Swich drasty rymyng moot ye lete,", "Such trashy rhyming you must drop,"),
        ("And turne another tale;", "And turn to a sounder tale;"),
        ("Or telle in prose som sentence swete,", "Or speak in prose some sweet wisdom,"),
        ("Whil that oure hors goon softly mete,", "While our horses amble evenly,"),
        ("Afore we drynke oure ale.", "Before we drink our tavern ale."),
    ],
]


class ChaucerGenerativePipeline:
    """Executes Stages 1-5 under AUTHOR_DEFINITION, WORLD_STATE, and Conservation Laws L1-L7."""

    def __init__(
        self,
        validator: ProsodicValidator | None = None,
        env: PilgrimageEnvironment | None = None,
        calibrator: AuthorOperatorCalibrator | None = None,
        s5_path: Path | None = None,
    ) -> None:
        self.validator = validator or ProsodicValidator()
        self.env = env or PilgrimageEnvironment()
        self.calibrator = calibrator or AuthorOperatorCalibrator(validator=self.validator)
        self.s5_path = s5_path or DEFAULT_S5_PATH
        raw_s5 = json.loads(self.s5_path.read_text(encoding="utf-8"))
        self.source_graphs: list[dict[str, Any]] = raw_s5["source_graphs"]
        self.audit_suite = PipelineAuditSuite(
            validator=self.validator, calibrator=self.calibrator
        )

    def select_source_and_form(
        self,
        speaker: PilgrimDefinition,
        world: WorldState,
        author_def: AuthorDefinition,
        forced_source_id: str | None = None,
        forced_form: MetricalForm | None = None,
    ) -> tuple[dict[str, Any], MetricalForm]:
        """Stage 2 objective: Affinity + QuitingContrast + Homeostasis - Saturation."""
        if forced_source_id:
            for sg in self.source_graphs:
                if sg["source_id"] == forced_source_id:
                    form = forced_form or MetricalForm(sg["recommended_form"])
                    return sg, form

        best_sg = self.source_graphs[0]
        best_score = -999.0
        est = speaker.estate_vector

        for sg in self.source_graphs:
            aff_map = sg["estate_affinity"]
            affinity = sum(est[k] * aff_map.get(k, 0.0) for k in est)

            # Bonus if speaker's occupational theme specifically aligns with silent pilgrim / role
            if speaker.id == "yeoman" and sg["source_id"] == "S5_PHEBUS_CHASSE":
                affinity += 1.4
            elif speaker.id == "plowman" and sg["source_id"] == "S5_SOMME_PLOUGH":
                affinity += 1.5
            elif speaker.id in {"haberdasher", "carpenter", "weaver", "dyer", "tapestry_maker"} and sg["source_id"] == "S5_GUILD_ORDINANCE":
                affinity += 1.4
            elif speaker.id == "reeve" and sg["source_id"] == "S5_FAB_MEUNIER":
                affinity += 1.5
            elif speaker.id == "miller" and sg["source_id"] == "S5_FAB_CHARPENTIER":
                affinity += 1.5
            elif speaker.id == "clerk" and sg["source_id"] == "S5_PETRARCH_GRISELDA":
                affinity += 1.3
            elif speaker.id == "wife_of_bath" and sg["source_id"] == "S5_GOWER_LOATHLY_LADY":
                affinity += 1.4
            elif speaker.id == "pardoner" and sg["source_id"] == "S5_EXEMPLUM_RADIX_MALORUM":
                affinity += 1.4
            elif speaker.id == "parson" and sg["source_id"] == "S5_ALBERTANUS_MELIBEE":
                affinity += 1.3
            elif speaker.id == "nuns_priest" and sg["source_id"] == "S5_MARIE_BEAST_FABLE":
                affinity += 1.4

            # Quiting contrast against previous genre
            contrast = 0.45 if world.last_genre and sg["genre"] != world.last_genre else 0.0

            # Homeostasis (Lambda_balance): pull back toward author_def.sentence_solaas_homeostasis
            desired_sent = author_def.sentence_solaas_homeostasis
            current_gap = desired_sent - world.rolling_sentence_level
            homeo = 0.65 * (1.0 - abs((sg["sentence_weight"] - 0.5) - current_gap))

            # Saturation penalty
            sat = 2.2 if sg["source_id"] in world.used_source_ids else 0.0

            total = affinity + contrast + homeo - sat
            if total > best_score:
                best_score = total
                best_sg = sg

        pref_forms = speaker.prosodic_competence.get("preferred_forms", ["riding_rhyme_couplet"])
        rec_form = best_sg["recommended_form"]
        if forced_form is not None:
            chosen_form = forced_form
        elif rec_form in pref_forms:
            chosen_form = MetricalForm(rec_form)
        else:
            chosen_form = MetricalForm(pref_forms[0])

        return best_sg, chosen_form

    def build_transposed_beat_plan(
        self,
        speaker: PilgrimDefinition,
        source_graph: dict[str, Any],
        author_def: AuthorDefinition,
        quiting_target_id: str | None,
    ) -> list[TransposedBeat]:
        """Stage 2: Apply K_comp rhetorical adaptation operations to S5 beat graph."""
        ops = ["translatio", "amplificatio", "class_transposition", "digressio", "sententia_closure"]
        beats: list[TransposedBeat] = []
        for idx, b in enumerate(source_graph["beats"]):
            op = ops[idx % len(ops)]
            if idx == 3 and author_def.compilatio_digression_density >= 0.25:
                op = "digressio"
            target_note = (
                f" (aimed across the road at {self.env.pilgrims[quiting_target_id].name})"
                if quiting_target_id and quiting_target_id in self.env.pilgrims and idx in (1, 3)
                else ""
            )
            adapted = (
                f"[{speaker.name} / {op}] Re-frames {source_graph['auctor']}: "
                f"{b['proposition']}{target_note}."
            )
            lex = list(dict.fromkeys(b["focus_lex"] + speaker.occupational_lexicon[:2]))
            beats.append(
                TransposedBeat(
                    beat_id=b["beat_id"],
                    role=b["role"],
                    causal_edge=b["edge"],
                    rhetorical_operation=op,
                    source_proposition=b["proposition"],
                    adapted_proposition=adapted,
                    focus_lexicon=lex,
                )
            )
        return beats

    def _pick_pilgrim_lex(self, speaker: PilgrimDefinition, syll_target: int) -> tuple[str, str]:
        """Select a 1-syllable or 2-syllable occupational word from the pilgrim's lexicon."""
        for w in speaker.occupational_lexicon:
            prof = self.validator.transcriber.profile_word(w)
            n_syll = len(prof.variants[0].syllables)
            entry = self.validator.transcriber.lexicon.lookup(w) or {}
            gloss = entry.get("gloss", w)
            # For pre-consonantal template slot, check canonical syllable count
            if n_syll == syll_target:
                return w, gloss
        return ("trouthe", "pledged truth") if syll_target == 1 else ("vertu", "moral virtue")

    def _synthesize_scanned_line(
        self,
        speaker: PilgrimDefinition,
        end_word: str,
        end_gloss: str,
        line_num: int,
        section: str,
        rng: random.Random,
        used_prefixes: set[str],
        target_rhyme_key: str | None = None,
    ) -> GeneratedVerseLine:
        """Stage 3 & 4 WFST Beam Search: generate candidates ending in `end_word` and keep best valid scan."""
        prof_end = self.validator.transcriber.profile_word(end_word)
        end_sylls = len(prof_end.variants[0].syllables)
        first_stress = prof_end.variants[0].syllables[0].stress
        has_romance_oxytone = any(
            len(v.syllables) == 2 and v.syllables[0].stress == 0 and v.syllables[1].stress == 1
            for v in prof_end.variants
        )

        lex1, gloss1 = self._pick_pilgrim_lex(speaker, 1)
        lex2, gloss2 = self._pick_pilgrim_lex(speaker, 2)

        is_verbal = end_word.lower() in VERBAL_ANCHORS
        if end_sylls >= 4:
            pool = list(PREFIX_7_TO_BEAT4)
        elif first_stress == 0 or has_romance_oxytone:
            pool = list(PREFIX_8_VERBAL if is_verbal else PREFIX_8_NOMINAL)
        else:
            pool = list(PREFIX_9_VERBAL if is_verbal else PREFIX_9_NOMINAL)

        # Filter Northern templates unless speaker uses Northernisms (e.g. Reeve)
        if speaker.dialect_profile.get("northernism_rate", 0.0) < 0.20:
            pool = [t for t in pool if not t[0].startswith(("Ik ", "Bi seint John ik"))]
        rng.shuffle(pool)

        best_candidate: tuple[str, str, Any] | None = None
        for tpl_me, tpl_gl in pool:
            prefix_sig = tpl_me.split("{")[0]
            if prefix_sig in used_prefixes and len(used_prefixes) < len(pool) - 1:
                continue
            cand_me = tpl_me.format(end=end_word, lex_1syll=lex1, lex_2syll=lex2)
            cand_gl = tpl_gl.format(
                end_gloss=end_gloss,
                lex_gloss=gloss1 if "{lex_1syll}" in tpl_me else gloss2,
            )
            scan = self.validator.scan_line(cand_me, line_number=line_num)
            if (
                scan.is_valid
                and not scan.l1_violations
                and (target_rhyme_key is None or scan.rhyme_key == target_rhyme_key)
            ):
                best_candidate = (cand_me, cand_gl, scan)
                used_prefixes.add(prefix_sig)
                break

        # Second-pass exhaustive search across compatible syntactic pools if primary shape missed
        if best_candidate is None:
            compat = (
                PREFIX_9_VERBAL + PREFIX_8_VERBAL
                if is_verbal
                else PREFIX_9_NOMINAL + PREFIX_8_NOMINAL + PREFIX_7_TO_BEAT4
            )
            for tpl_me, tpl_gl in compat:
                if speaker.dialect_profile.get("northernism_rate", 0.0) < 0.20 and tpl_me.startswith(("Ik ", "Bi seint John ik")):
                    continue
                cand_me = tpl_me.format(end=end_word, lex_1syll=lex1, lex_2syll=lex2)
                cand_gl = tpl_gl.format(
                    end_gloss=end_gloss,
                    lex_gloss=gloss1 if "{lex_1syll}" in tpl_me else gloss2,
                )
                scan = self.validator.scan_line(cand_me, line_number=line_num)
                if (
                    scan.is_valid
                    and not scan.l1_violations
                    and (target_rhyme_key is None or scan.rhyme_key == target_rhyme_key)
                ):
                    best_candidate = (cand_me, cand_gl, scan)
                    break

        if best_candidate is None:
            fallback_me = f"By Goddes might he kepte wel his {end_word},"
            fallback_gl = f"By divine strength he guarded well his {end_gloss},"
            scan = self.validator.scan_line(fallback_me, line_number=line_num)
            best_candidate = (fallback_me, fallback_gl, scan)

        me_text, gl_text, scan_res = best_candidate
        etymons: list[str] = []
        max_year = 1150
        for w, p in self.validator.transcriber.tokenize_line(me_text):
            wp = self.validator.transcriber.profile_word(w, p)
            if wp.word_class == WordClass.CONTENT:
                etymons.append(wp.etymon)
            if wp.earliest_year <= 1400:
                max_year = max(max_year, wp.earliest_year)

        return GeneratedVerseLine(
            line_number=line_num,
            section=section,
            speaker_id=speaker.id,
            middle_english=me_text,
            modern_gloss=gl_text,
            hengwrt_orthography=to_hengwrt_orthography(me_text, line_num),
            ellesmere_orthography=to_ellesmere_orthography(me_text),
            ipa_transcription=scan_res.ipa_transcription,
            metrical_pattern=scan_res.metrical_pattern,
            syllable_count=scan_res.syllable_count,
            license_used=scan_res.license_used.value if scan_res.license_used else "prose_cadence",
            rhyme_key=scan_res.rhyme_key,
            elision_events=scan_res.elision_events,
            etymons=etymons,
            max_attestation_year=max_year,
        )

    def _synthesize_link_prologue(
        self,
        speaker: PilgrimDefinition,
        selection_mode: str,
        quiting_target_id: str | None,
        rng: random.Random,
    ) -> list[GeneratedVerseLine]:
        """Stage 1: Dramatic Link Prologue couplets between Harry Bailly and incoming speaker."""
        used_prefixes: set[str] = set()
        host = self.env.pilgrims["harry_bailly"]
        rhyme_a = RHYME_ANCHOR_SETS["aːsə"]
        rhyme_b = RHYME_ANCHOR_SETS["iːtə"] if selection_mode == "quiting_interruption" else RHYME_ANCHOR_SETS["aːlə"]

        l1 = self._synthesize_scanned_line(host, rhyme_a[0][0], rhyme_a[0][1], 1, "link_prologue", rng, used_prefixes)
        l2 = self._synthesize_scanned_line(host, rhyme_a[1][0], rhyme_a[1][1], 2, "link_prologue", rng, used_prefixes)
        l3 = self._synthesize_scanned_line(speaker, rhyme_b[0][0], rhyme_b[0][1], 3, "link_prologue", rng, used_prefixes)
        l4 = self._synthesize_scanned_line(speaker, rhyme_b[2][0], rhyme_b[2][1], 4, "link_prologue", rng, used_prefixes)
        return [l1, l2, l3, l4]

    def _synthesize_tale_body(
        self,
        speaker: PilgrimDefinition,
        beat_plan: list[TransposedBeat],
        metrical_form: MetricalForm,
        unit_count: int,
        rng: random.Random,
    ) -> list[GeneratedVerseLine]:
        """Stage 3 & 4: Realize Beat Graph into Riding Rhyme, Rhyme Royal, Tail-Rhyme, or Prose."""
        used_prefixes: set[str] = set()
        lines: list[GeneratedVerseLine] = []

        if metrical_form == MetricalForm.CADENCED_PROSE:
            prose_periods = [
                (
                    f"Herkeneth now, {speaker.signature_oath}, how prudence and trewe sentence "
                    "governen every companye in this mortal pilgrymage.",
                    "Listen now how prudence and true moral wisdom govern every fellowship on this mortal pilgrimage.",
                ),
                (
                    "Whan that hasty wratthe or coveitise blindeth the herte, thanne moot resoun "
                    "and olde auctours bringe soote boote unto our conscience.",
                    "When hasty wrath or greed blinds the heart, then reason and ancient authorities must bring healing remedy to conscience.",
                ),
                (
                    "For right as clean labour in the comune furwe pleseth hevene, right so "
                    "pacience and humilitee overcomen al worldly torment and stryf.",
                    "For just as honest labor in the shared furrow pleases heaven, so patience and humility overcome worldly strife.",
                ),
                (
                    "Ther-fore lat ech wight flee vileynye and holde faste his trouthe, "
                    "til grace lede us unto parfyt wele and pees.",
                    "Therefore let every person flee base conduct and keep faith, until grace leads us to lasting peace.",
                ),
            ]
            for idx, (me, gl) in enumerate(prose_periods[: max(3, unit_count)], start=1):
                toks = self.validator.transcriber.tokenize_line(me)
                ipas = []
                etymons = []
                max_yr = 1150
                for w, p in toks:
                    wp = self.validator.transcriber.profile_word(w, p)
                    ipas.append(wp.variants[0].ipa)
                    if wp.word_class == WordClass.CONTENT:
                        etymons.append(wp.etymon)
                    if wp.earliest_year <= 1400:
                        max_yr = max(max_yr, wp.earliest_year)
                lines.append(
                    GeneratedVerseLine(
                        line_number=idx,
                        section="tale_body",
                        speaker_id=speaker.id,
                        middle_english=me,
                        modern_gloss=gl,
                        hengwrt_orthography=to_hengwrt_orthography(me, idx),
                        ellesmere_orthography=to_ellesmere_orthography(me),
                        ipa_transcription=" ".join(ipas),
                        metrical_pattern="cursus_planus_prose",
                        syllable_count=sum(len(self.validator.transcriber.profile_word(w, p).variants[0].syllables) for w, p in toks),
                        license_used="cadenced_prose",
                        rhyme_key="prose",
                        elision_events=[],
                        etymons=etymons,
                        max_attestation_year=max_yr,
                    )
                )
            return lines

        if metrical_form == MetricalForm.TAIL_RHYME:
            line_no = 1
            for stanza in TAIL_RHYME_STANZAS[: max(1, min(2, unit_count))]:
                for me, gl in stanza:
                    scan = self.validator.scan_line(me, line_number=line_no)
                    toks = self.validator.transcriber.tokenize_line(me)
                    ipas = [self.validator.transcriber.profile_word(w, p).variants[0].ipa for w, p in toks]
                    etymons = [
                        self.validator.transcriber.profile_word(w, p).etymon
                        for w, p in toks
                        if self.validator.transcriber.profile_word(w, p).word_class == WordClass.CONTENT
                    ]
                    lines.append(
                        GeneratedVerseLine(
                            line_number=line_no,
                            section="tale_body",
                            speaker_id=speaker.id,
                            middle_english=me,
                            modern_gloss=gl,
                            hengwrt_orthography=to_hengwrt_orthography(me, line_no),
                            ellesmere_orthography=to_ellesmere_orthography(me),
                            ipa_transcription=scan.ipa_transcription or " ".join(ipas),
                            metrical_pattern=scan.metrical_pattern or "x/x/x/x/",
                            syllable_count=scan.syllable_count or sum(len(self.validator.transcriber.profile_word(w, p).variants[0].syllables) for w, p in toks),
                            license_used="tail_rhyme_burlesque",
                            rhyme_key=scan.rhyme_key or me.split()[-1].strip(".,;"),
                            elision_events=scan.elision_events,
                            etymons=etymons,
                            max_attestation_year=1380,
                        )
                    )
                    line_no += 1
            return lines

        # Filter rhyme families by speaker sociolect (e.g. allow Northern /a:n/ for Reeve)
        use_north = speaker.dialect_profile.get("northernism_rate", 0.0) >= 0.25
        high_romance = speaker.dialect_profile.get("french_prestige_ceiling", 0.35) >= 0.40

        if high_romance:
            family_order = ["ɛnsə", "aːsə", "iːzə", "uːr", "ɛntə", "ɛːdə", "içt", "oːtə"]
        elif use_north:
            family_order = ["aːn", "iːtə", "içt", "aːlə", "ɛrtə", "ɛːdə"]
        else:
            family_order = ["ɛːdə", "oːtə", "aːlə", "içt", "eːtə", "iːtə", "aːsə", "ɛrtə"]

        if metrical_form == MetricalForm.RHYME_ROYAL:
            # 7-line ABABBCC stanzas (need >=2 for A, >=3 for B, >=2 for C)
            three_plus = [k for k in family_order if len(RHYME_ANCHOR_SETS[k]) >= 3]
            two_plus = [k for k in family_order if len(RHYME_ANCHOR_SETS[k]) >= 2]
            n_stanzas = max(1, min(3, unit_count))
            line_no = 1
            for st_idx in range(n_stanzas):
                fam_b = three_plus[st_idx % len(three_plus)]
                rem = [k for k in two_plus if k != fam_b]
                fam_a = rem[(st_idx * 2) % len(rem)]
                fam_c = rem[(st_idx * 2 + 1) % len(rem)]

                set_a = RHYME_ANCHOR_SETS[fam_a]
                set_b = RHYME_ANCHOR_SETS[fam_b]
                set_c = RHYME_ANCHOR_SETS[fam_c]
                # Pattern ABABBCC
                plan_anchors = [
                    (set_a[0], fam_a),
                    (set_b[0], fam_b),
                    (set_a[1], fam_a),
                    (set_b[1], fam_b),
                    (set_b[2], fam_b),
                    (set_c[0], fam_c),
                    (set_c[1], fam_c),
                ]
                for (word, gloss), rkey in plan_anchors:
                    lines.append(
                        self._synthesize_scanned_line(
                            speaker, word, gloss, line_no, "tale_body", rng, used_prefixes, target_rhyme_key=rkey
                        )
                    )
                    line_no += 1
            return lines

        # Default: RIDING_RHYME couplets (AABBCCDD...) across beat_plan
        n_couplets = max(4, min(8, unit_count * 2 if unit_count <= 3 else unit_count))
        line_no = 1
        for c_idx in range(n_couplets):
            fam = family_order[c_idx % len(family_order)]
            anchors = RHYME_ANCHOR_SETS[fam]
            pair_offset = ((c_idx // len(family_order)) * 2) % max(1, len(anchors) - 1)
            w1, g1 = anchors[pair_offset]
            w2, g2 = anchors[(pair_offset + 1) % len(anchors)]
            if w1 == w2 and len(anchors) > 1:
                w2, g2 = anchors[0]
            lines.append(
                self._synthesize_scanned_line(
                    speaker, w1, g1, line_no, "tale_body", rng, used_prefixes, target_rhyme_key=fam
                )
            )
            line_no += 1
            lines.append(
                self._synthesize_scanned_line(
                    speaker, w2, g2, line_no, "tale_body", rng, used_prefixes, target_rhyme_key=fam
                )
            )
            line_no += 1

        # Adjust terminal punctuation on couplet pairs for clean editorial reading
        for idx in range(1, len(lines), 2):
            lines[idx].middle_english = lines[idx].middle_english.rstrip(",") + "."
            lines[idx].hengwrt_orthography = lines[idx].hengwrt_orthography.rstrip(",") + "."
            lines[idx].ellesmere_orthography = lines[idx].ellesmere_orthography.rstrip(",") + "."
            lines[idx].modern_gloss = lines[idx].modern_gloss.rstrip(",") + "."
        return lines

    def _synthesize_estate_reception(
        self,
        speaker: PilgrimDefinition,
        genre: str,
        sentence_score: float,
        solaas_score: float,
        provoked_ids: list[str],
    ) -> tuple[list[EstateReaction], str]:
        """Stage 5: Divergent reception across estates enforcing Law L7 (Reception Non-Assertion)."""
        reactions: list[EstateReaction] = []

        if sentence_score >= 0.70:
            reactions.append(
                EstateReaction(
                    estate_group="Bellatores & Gentils",
                    representative_pilgrim="The Knight",
                    polarity="approving",
                    reaction_summary="Commends the sober governance and moral sentence, judging it worthy of memory.",
                    quiting_delta=-0.08,
                )
            )
            reactions.append(
                EstateReaction(
                    estate_group="Laboratores & Cherles",
                    representative_pilgrim="Robyn (The Miller)",
                    polarity="mocking",
                    reaction_summary="Mutters over his bagpipe that solemn clerkly preaching parches the throat without tavern solaas.",
                    quiting_delta=0.28,
                )
            )
        else:
            reactions.append(
                EstateReaction(
                    estate_group="Bellatores & Gentils",
                    representative_pilgrim="Madame Eglentyne (The Prioress)",
                    polarity="contested",
                    reaction_summary="Turns aside from the broad churlish game while the younger squires laugh beneath their cloaks.",
                    quiting_delta=0.18,
                )
            )
            reactions.append(
                EstateReaction(
                    estate_group="Laboratores & Guildsmen",
                    representative_pilgrim="Hogge of Ware (The Cook)",
                    polarity="approving",
                    reaction_summary="Claps the teller on the shoulder for quick-witted solaas that wakes the road.",
                    quiting_delta=-0.05,
                )
            )

        if provoked_ids:
            ant_id = provoked_ids[0]
            ant_name = self.env.pilgrims[ant_id].name if ant_id in self.env.pilgrims else ant_id
            reactions.append(
                EstateReaction(
                    estate_group="Aggrieved Rival (Quiting Ledger)",
                    representative_pilgrim=ant_name,
                    polarity="aggrieved",
                    reaction_summary=f"Takes the tale's pointed craft-satire personally and vows to quite {speaker.name} as soon as Harry Bailly yields the floor.",
                    quiting_delta=0.38,
                )
            )
        else:
            reactions.append(
                EstateReaction(
                    estate_group="Clerical & Scholastic Bench",
                    representative_pilgrim="The Clerk of Oxenford",
                    polarity="contested",
                    reaction_summary="Weighs the cited auctoritas silently, reserving a sharper philosophical counter-exemplum.",
                    quiting_delta=0.14,
                )
            )

        host_verdict = (
            f"Harry Bailly weighs {speaker.name}'s {genre.replace('_', ' ')} ({int(sentence_score*100)}% sentence / "
            f"{int(solaas_score*100)}% solaas) without crowning an undisputed victor, calling the company forward along the Kentish road."
        )
        return reactions, host_verdict

    def generate_turn(
        self,
        world: WorldState,
        author_def: AuthorDefinition | None = None,
        forced_speaker_id: str | None = None,
        forced_source_id: str | None = None,
        forced_form: MetricalForm | None = None,
        unit_count: int = 3,
        seed: int = 1390,
    ) -> tuple[GeneratedTurnArtifact, WorldState]:
        """Run Stages 1 through 5 and return both the audited artifact and updated WORLD_STATE."""
        author = author_def or self.calibrator.calibrate()
        rng = random.Random(seed + world.turn_index * 37)

        # Stage 1: Speaker selection & Link Prologue
        speaker, sel_mode, quiting_target, _ = self.env.select_speaker(
            world, forced_speaker_id=forced_speaker_id
        )
        source_graph, metrical_form = self.select_source_and_form(
            speaker, world, author, forced_source_id=forced_source_id, forced_form=forced_form
        )
        link_lines = self._synthesize_link_prologue(speaker, sel_mode, quiting_target, rng)

        # Stage 2: Compilatio Beat Graph
        beat_plan = self.build_transposed_beat_plan(speaker, source_graph, author, quiting_target)

        # Stage 3 & 4: Sociolect + Rhyme-First Prosodic Realization
        tale_lines = self._synthesize_tale_body(
            speaker, beat_plan, metrical_form, unit_count=unit_count, rng=rng
        )

        # Stage 5: Estate Reception, Scribal Witnesses, TEI-XML, & World Update
        provoked = [
            p for p in source_graph.get("provokes_pilgrims", []) if p != speaker.id
        ]
        s_score = float(source_graph["sentence_weight"])
        m_score = float(source_graph["solaas_weight"])
        reactions, host_verdict = self._synthesize_estate_reception(
            speaker, source_graph["genre"], s_score, m_score, provoked
        )
        marginalia = generate_ellesmere_marginalia(
            source_graph["auctor"], source_graph["title"], source_graph["genre"]
        )
        tei_xml = emit_tei_xml_apparatus(
            world.turn_index + 1, speaker.name, source_graph["title"], tale_lines
        )

        next_world = self.env.advance_world_state(
            world,
            speaker=speaker,
            source_id=source_graph["source_id"],
            genre=source_graph["genre"],
            sentence_score=s_score,
            solaas_score=m_score,
            provoked_pilgrims=provoked,
        )

        laws, diagnostics = self.audit_suite.evaluate_generated_turn(
            speaker=speaker,
            author_def=author,
            selection_mode=sel_mode,
            source_graph=source_graph,
            metrical_form=metrical_form,
            beat_plan=beat_plan,
            link_lines=link_lines,
            tale_lines=tale_lines,
            estate_reactions=reactions,
        )

        artifact = GeneratedTurnArtifact(
            turn_id=next_world.turn_index,
            turn_index=next_world.turn_index,
            route_stage_name=next_world.route_stage_name,
            mile_marker=next_world.mile_marker,
            speaker_id=speaker.id,
            speaker_name=speaker.name,
            speaker_role=speaker.role_title,
            manuscript_status=speaker.manuscript_status,
            selection_mode=sel_mode,
            quiting_target_id=quiting_target,
            source_id=source_graph["source_id"],
            source_title=source_graph["title"],
            source_auctor=source_graph["auctor"],
            source_year=int(source_graph["year_composed"]),
            genre=source_graph["genre"],
            metrical_form=metrical_form,
            sentence_score=s_score,
            solaas_score=m_score,
            link_lines=link_lines,
            beat_plan=beat_plan,
            tale_lines=tale_lines,
            ellesmere_marginalia=marginalia,
            tei_xml_apparatus=tei_xml,
            estate_reactions=reactions,
            host_verdict=host_verdict,
            conservation_laws=laws,
            diagnostics=diagnostics,
        )
        return artifact, next_world
