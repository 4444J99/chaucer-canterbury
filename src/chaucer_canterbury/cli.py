"""Command-line interface for chaucer-canterbury (Phases 1 through 5)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chaucer_canterbury.author_operator import AuthorOperatorCalibrator
from chaucer_canterbury.blind_scansion import (
    BlindScansionEvaluator,
    render_blind_scansion_markdown,
)
from chaucer_canterbury.generator import ChaucerGenerativePipeline
from chaucer_canterbury.models import MetricalForm
from chaucer_canterbury.scansion import ProsodicValidator
from chaucer_canterbury.validators import run_holdout_counterfactual_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chaucer-canterbury",
        description="Protocol-bound Middle English phonology, Author-Operator calibration, and Canterbury Tales generation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_trans = sub.add_parser("transcribe", help="Profile a Middle English word or line into IPA variants.")
    p_trans.add_argument("text", help="Middle English word or line.")
    p_trans.add_argument("--json", action="store_true", help="Emit raw JSON.")

    p_scan = sub.add_parser("scan-line", help="Scan a single Middle English verse line.")
    p_scan.add_argument("line", help="Middle English pentameter line.")
    p_scan.add_argument("--json", action="store_true", help="Emit raw JSON.")

    p_audit = sub.add_parser("audit-corpus", help="Audit a Stratum S2 calibration JSON file.")
    p_audit.add_argument("path", type=Path, help="Path to S2 JSON file.")
    p_audit.add_argument("--json", action="store_true", help="Emit raw JSON.")

    p_cal = sub.add_parser("calibrate", help="Calibrate AUTHOR_DEFINITION from S2 + S3 corpora.")
    p_cal.add_argument("--json", action="store_true", help="Emit raw JSON.")

    p_gen = sub.add_parser("generate-turn", help="Run Five-Stage generative pipeline for one pilgrimage turn.")
    p_gen.add_argument("--speaker", default=None, help="Optional Pilgrim ID (e.g., yeoman, plowman, miller).")
    p_gen.add_argument("--form", default=None, choices=[m.value for m in MetricalForm], help="Optional metrical vehicle.")
    p_gen.add_argument("--units", type=int, default=3, help="Number of couplet pairs / stanzas.")
    p_gen.add_argument("--json", action="store_true", help="Emit raw JSON.")

    p_cf = sub.add_parser("run-counterfactuals", help="Execute 6 Leave-One-Tale-Out & Silent-Pilgrim counterfactuals.")
    p_cf.add_argument("--json", action="store_true", help="Emit raw JSON.")

    p_vh = sub.add_parser(
        "validate-holdout",
        help="Run Validation Plan 02 blind scansion and rhyme holdout evaluation.",
    )
    p_vh.add_argument(
        "--set",
        dest="holdout_set",
        default="ALL",
        choices=["H1", "H2", "H3", "H4", "N1", "REF70", "ALL"],
        help="Holdout set to evaluate (default: ALL).",
    )
    p_vh.add_argument(
        "--engine-version",
        default="v0.1-baseline",
        help="Engine version label recorded in the output report.",
    )
    p_vh.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write full JSON report.",
    )
    p_vh.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
        help="Optional path to write Markdown summary report.",
    )
    p_vh.add_argument("--json", action="store_true", help="Emit raw JSON.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validator = ProsodicValidator()
    transcriber = validator.transcriber

    if args.command == "transcribe":
        tokens = transcriber.tokenize_line(args.text)
        profiles = [transcriber.profile_word(w, p) for w, p in tokens]
        if args.json:
            print(json.dumps([p.model_dump() for p in profiles], indent=2, ensure_ascii=False))
        else:
            for p in profiles:
                vars_str = ", ".join(f"[{v.ipa}] (stress={v.stress_pattern}, cost={v.cost})" for v in p.variants)
                print(
                    f"{p.surface:<16} norm={p.normalized:<14} class={p.word_class.value:<8} "
                    f"final_e={p.final_e_class.value:<18} -> {vars_str}"
                )
        return 0

    if args.command == "scan-line":
        res = validator.scan_line(args.line)
        if args.json:
            print(json.dumps(res.model_dump(), indent=2, ensure_ascii=False))
        else:
            status = "VALID" if res.is_valid else "INVALID"
            lic = res.license_used.value if res.license_used else "none"
            print(f"[{status}] {res.original_text}")
            print(f"  IPA:      {res.ipa_transcription}")
            print(f"  Pattern:  {res.metrical_pattern}  ({res.syllable_count} sylls, license={lic}, cost={res.total_cost})")
            print(f"  Rhyme:    /{res.rhyme_key}/")
            if res.elision_events:
                print(f"  Sandhi:   {', '.join(res.elision_events)}")
        return 0 if res.is_valid else 1

    if args.command == "audit-corpus":
        report = validator.audit_corpus_file(args.path)
        if args.json:
            print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"Work: {report.title} ({report.work_id})")
            print(f"Lines Valid: {report.valid_lines}/{report.total_lines} ({report.scansion_pass_rate * 100:.1f}%)")
            print(f"Rhyme Groups Valid: {report.rhyme_groups_valid}/{report.rhyme_groups_total}")
            print(f"Elision/Sandhi Events Resolved: {report.elision_count}")
        return 0 if report.valid_lines == report.total_lines and report.rhyme_groups_valid == report.rhyme_groups_total else 1

    if args.command == "calibrate":
        cal = AuthorOperatorCalibrator(validator=validator).calibrate()
        if args.json:
            print(json.dumps(cal.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"AUTHOR_DEFINITION ({cal.total_calibrated_lines} S2 lines)")
            print(f"  Romance/Germanic Ratio: {cal.etymological_rom_gmc_ratio}")
            print(f"  Feminine Ending Rate:   {cal.feminine_ending_rate}")
            print(f"  V2 Topicalization Rate: {cal.v2_topicalization_rate}")
            print(f"  Etymology Distribution: {cal.etymology_distribution}")
        return 0

    if args.command == "generate-turn":
        pipe = ChaucerGenerativePipeline(validator=validator)
        world = pipe.env.initial_world_state()
        form = MetricalForm(args.form) if args.form else None
        artifact, _ = pipe.generate_turn(
            world, forced_speaker_id=args.speaker, forced_form=form, unit_count=args.units
        )
        if args.json:
            print(json.dumps(artifact.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"Turn {artifact.turn_index}: {artifact.speaker_name} ({artifact.selection_mode})")
            print(f"Source: {artifact.source_title} [{artifact.source_auctor}, {artifact.source_year} CE] | Form: {artifact.metrical_form.value}")
            print("--- Tale Body ---")
            for ln in artifact.tale_lines:
                print(f"  {ln.line_number:>2}. {ln.middle_english}")
                print(f"      [{ln.metrical_pattern}] /{ln.rhyme_key}/ -> {ln.modern_gloss}")
            passed = sum(1 for c in artifact.conservation_laws if c.passed)
            print(f"Conservation Laws Passed: {passed}/{len(artifact.conservation_laws)}")
        return 0

    if args.command == "run-counterfactuals":
        pipe = ChaucerGenerativePipeline(validator=validator)
        rep = run_holdout_counterfactual_suite(pipe)
        if args.json:
            print(json.dumps(rep.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"Counterfactual Convergence: {rep.convergent_scenarios}/{rep.total_scenarios}")
            print(f"All L6 Non-Copying Passed:  {rep.all_l6_non_copying_passed}")
            print(f"Mean Prosody Pass Rate:     {rep.mean_prosody_pass_rate * 100:.1f}%")
            for r in rep.results:
                print(f"  - {r.scenario_id}: {r.emergent_speaker_name} -> {r.selected_genre} (converged={r.structural_convergence}, L6={r.non_copying_l6_passed})")
        return 0 if rep.all_l6_non_copying_passed else 1

    if args.command == "validate-holdout":
        evaluator = BlindScansionEvaluator(
            validator=validator,
            engine_version=args.engine_version,
        )
        report = evaluator.run(selected_set=args.holdout_set)
        payload_str = json.dumps(report.model_dump(), indent=2, ensure_ascii=False)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload_str + "\n", encoding="utf-8")
        if args.markdown_output is not None:
            args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_output.write_text(
                render_blind_scansion_markdown(report), encoding="utf-8"
            )
        if args.json:
            print(payload_str)
        else:
            print(render_blind_scansion_markdown(report))
        return 0 if report.all_thresholds_passed else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
