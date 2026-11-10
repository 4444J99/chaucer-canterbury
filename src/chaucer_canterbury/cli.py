"""Command-line interface for Phase 1 Middle English phonology and scansion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chaucer_canterbury.phonology import MiddleEnglishTranscriber
from chaucer_canterbury.scansion import ProsodicValidator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chaucer-prosody",
        description="Middle English phonological transcriber, final -e resolver, and pentameter validator.",
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
            if res.l1_violations:
                print(f"  L1 Viol:  {'; '.join(res.l1_violations)}")
            if res.l4_notes:
                print(f"  L4 Notes: {'; '.join(res.l4_notes)}")
        return 0 if res.is_valid else 1

    if args.command == "audit-corpus":
        report = validator.audit_corpus_file(args.path)
        if args.json:
            print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"Work: {report.title} ({report.work_id})")
            print(
                f"Lines Valid: {report.valid_lines}/{report.total_lines} "
                f"({report.scansion_pass_rate * 100:.1f}%)"
            )
            print(
                f"Rhyme Groups Valid: {report.rhyme_groups_valid}/{report.rhyme_groups_total}"
            )
            print(f"Elision/Sandhi Events Resolved: {report.elision_count}")
            print(f"License Distribution: {report.license_distribution}")
            for st in report.stanzas:
                if st.violations:
                    print(f"  Stanza {st.stanza_id} violations:")
                    for v in st.violations:
                        print(f"    - {v}")
        return 0 if report.valid_lines == report.total_lines and report.rhyme_groups_valid == report.rhyme_groups_total else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
