"""CLI entry point for ambiguity."""

import argparse
import json
import sys
from . import __version__
from .analyzer import Analysis
from .profile import get_profile
from .flow import flow_test, render_flow_report, render_flow_json
from .compare import compare, render_compare_report, render_compare_json, write_experiment_files
from .audit import audit, render_audit_report, render_audit_json
from .translate import translate, render_translate_report, render_translate_json
from .clarify import clarify, render_clarify_report, render_clarify_json
from .memory import log_interaction, summary as memory_summary
from .import_discover import discover, render_import_report, render_import_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ambiguity",
        description="Deterministic prompt analysis — pre-flight linter for human-to-model translation.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze a prompt for ambiguity")
    analyze.add_argument("prompt", nargs="?", help="Prompt text to analyze")
    analyze.add_argument("--json", action="store_true", help="Output as JSON")
    analyze.add_argument("--udl", action="store_true", help="Include UDL envelope in JSON output")
    analyze.add_argument("--pipe", action="store_true", help="Read prompt from stdin")
    analyze.add_argument("--quiet", action="store_true", help="Suppress output if score below threshold")
    analyze.add_argument("--gate", type=float, metavar="THRESHOLD", default=0.0, help="Exit code 1 if score exceeds threshold (e.g. --gate 6.0)")
    analyze.add_argument("--watch", type=str, metavar="DIR", help="Watch directory for new/modified .md files, analyze continuously")

    learn = sub.add_parser("learn", help="Teach the tool a new verb, acronym, or keyword")
    learn.add_argument("type", choices=["verb", "acronym", "keyword"], help="Thing to learn")
    learn.add_argument("value", help="The verb, acronym, or keyword")
    learn.add_argument("--containers", nargs="*", help="Container names")
    learn.add_argument("--specificity", type=float, default=0.5, help="Verb specificity (0-1)")
    learn.add_argument("--expansion", help="Acronym expansion")

    dismiss = sub.add_parser("dismiss", help="Dismiss a flag type (suppresses future advisories)")
    dismiss.add_argument("flag_type", help="Flag type to suppress (e.g. 'no explicit constraints')")

    config = sub.add_parser("config", help="View current profile configuration")
    config.add_argument("--reset", action="store_true", help="Reset profile to defaults")

    flow = sub.add_parser("flow-test", help="Scan documentation for duplication, dead links, missing coverage")
    flow.add_argument("--json", action="store_true", help="Output as JSON")

    compare_p = sub.add_parser("compare", help="Run prompt with and without pre-flight, compare outputs")
    compare_p.add_argument("prompt", nargs="?", help="Prompt text to compare")
    compare_p.add_argument("--pipe", action="store_true", help="Read prompt from stdin")
    compare_p.add_argument("--json", action="store_true", help="Output as JSON")
    compare_p.add_argument("--no-llm", action="store_true", help="Skip LLM calls, only generate prompts")
    compare_p.add_argument("--provider", choices=["anthropic", "openai", "auto"], default="auto", help="LLM provider")
    compare_p.add_argument("--output-dir", type=str, default=None, help="Directory to write experiment files")

    audit_p = sub.add_parser("audit", help="Audit claimed file creations against actual filesystem state")
    audit_p.add_argument("prompt", nargs="?", help="Prompt text with claimed file paths")
    audit_p.add_argument("--pipe", action="store_true", help="Read prompt from stdin")
    audit_p.add_argument("--dir", type=str, default=".", help="Directory to scan for actual files")
    audit_p.add_argument("--json", action="store_true", help="Output as JSON")

    translate_p = sub.add_parser("translate", help="Resolve ambiguity — expand acronyms, replace vague verbs, add constraints")
    translate_p.add_argument("prompt", nargs="?", help="Prompt text to de-ambiguate")
    translate_p.add_argument("--pipe", action="store_true", help="Read prompt from stdin")
    translate_p.add_argument("--json", action="store_true", help="Output as JSON")

    clarify_p = sub.add_parser("clarify", help="Generate clarification questions from ambiguity analysis")
    clarify_p.add_argument("prompt", nargs="?", help="Prompt text to analyze for questions")
    clarify_p.add_argument("--pipe", action="store_true", help="Read prompt from stdin")
    clarify_p.add_argument("--json", action="store_true", help="Output as JSON")

    log_p = sub.add_parser("log", help="Log an interaction to docs/memory.md")
    log_p.add_argument("prompt", nargs="?", help="Prompt text to log")
    log_p.add_argument("--pipe", action="store_true", help="Read prompt from stdin")
    log_p.add_argument("--action", default="none", choices=["none", "translate", "clarify", "skip"], help="Action taken")
    log_p.add_argument("--outcome", default="accepted", choices=["accepted", "rejected", "modified"], help="User's response")
    log_p.add_argument("--note", default="", help="Optional note for context")
    log_p.add_argument("--summary", action="store_true", help="Show recent log summary instead of logging")

    import_p = sub.add_parser("import", help="Discover and import prompt history from agent harnesses")
    import_p.add_argument("--consent", action="store_true", help="Confirm consent to scan harness directories")
    import_p.add_argument("--execute", action="store_true", help="Actually import (default is dry-run)")
    import_p.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "translate":
        return _cmd_translate(args)
    if args.command == "clarify":
        return _cmd_clarify(args)
    if args.command == "log":
        return _cmd_log(args)
    if args.command == "import":
        return _cmd_import(args)
    if args.command == "compare":
        return _cmd_compare(args)
    if args.command == "audit":
        return _cmd_audit(args)
    if args.command == "analyze":
        return _cmd_analyze(args)
    elif args.command == "learn":
        return _cmd_learn(args)
    elif args.command == "dismiss":
        return _cmd_dismiss(args)
    elif args.command == "config":
        return _cmd_config(args)
    elif args.command == "flow-test":
        return _cmd_flow_test(args)

    parser.print_help()
    return 0


def _cmd_analyze(args) -> int:
    if args.watch:
        return _cmd_watch(args.watch)

    prompt = args.prompt

    if args.pipe or (not prompt and not sys.stdin.isatty()):
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("error: no prompt provided (pass as argument or pipe via stdin)", file=sys.stderr)
        return 1

    profile = get_profile()

    from .advisory import advisory, set_suppressed
    suppressed = profile.suppressed_flags()
    if suppressed:
        set_suppressed(suppressed)

    analysis = Analysis(prompt)
    adv = advisory(analysis.result, analysis.score)
    profile.record(analysis.result, analysis.score, adv)

    if args.quiet and analysis.score.total < profile.adjusted_threshold():
        return 0

    gate = args.gate
    if gate > 0.0 and analysis.score.total > gate:
        if args.json:
            output = analysis.full_output(include_udl=args.udl)
            print(json.dumps(output, indent=2))
        else:
            print(analysis.terminal_report())
        print(f"[ambiguity] GATE: score {analysis.score.total:.1f} exceeds {gate:.1f}", file=sys.stderr)
        return 1

    if args.json:
        output = analysis.full_output(include_udl=args.udl)
        output["_profile"] = {
            "baseline": profile.score_baseline,
            "threshold": profile.adjusted_threshold(),
            "suppressed": list(profile.suppressed_flags()),
        }
        print(json.dumps(output, indent=2, sort_keys=False, ensure_ascii=False))
    else:
        print(analysis.terminal_report())

    return 0


def _cmd_watch(watch_dir: str) -> int:
    import time
    from pathlib import Path
    from .analyzer import Analysis
    from .advisory import advisory

    target = Path(watch_dir).resolve()
    if not target.is_dir():
        print(f"error: {watch_dir} is not a directory", file=sys.stderr)
        return 1

    seen: dict[str, float] = {}
    print(f"[ambiguity] watching {target} for .md files (Ctrl+C to stop)", file=sys.stderr)
    try:
        while True:
            for fp in sorted(target.rglob("*.md")):
                mtime = fp.stat().st_mtime
                key = str(fp)
                last = seen.get(key, 0.0)
                if mtime > last:
                    seen[key] = mtime
                    if last > 0.0:
                        text = fp.read_text(encoding="utf-8", errors="replace").strip()
                        if text:
                            analysis = Analysis(text)
                            ts = time.strftime("%H:%M:%S")
                            print(f"[{ts}] {fp.name}: {analysis.score.total:.1f}/10 ({analysis.score.band})  {advisory(analysis.result, analysis.score) or ''}")
                            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        print(file=sys.stderr)
        return 0


def _cmd_learn(args) -> int:
    profile = get_profile()
    if args.type == "verb":
        profile.learn_verb(args.value, args.containers, args.specificity)
        print(f"learned verb '{args.value}' (containers: {args.containers}, specificity: {args.specificity})")
    elif args.type == "acronym":
        if not args.expansion:
            print("error: --expansion required for acronyms", file=sys.stderr)
            return 1
        profile.learn_acronym(args.value, args.expansion)
        print(f"learned acronym '{args.value}' -> '{args.expansion}'")
    elif args.type == "keyword":
        profile.learn_keyword(args.value, args.containers or [])
        print(f"learned keyword '{args.value}' (containers: {args.containers})")
    return 0


def _cmd_dismiss(args) -> int:
    profile = get_profile()
    profile.dismiss(args.flag_type)
    print(f"dismissed '{args.flag_type}' (will suppress after 3 dismissals)")
    return 0


def _cmd_config(args) -> int:
    profile = get_profile()
    if args.reset:
        path = profile.__class__.PROFILE_PATH if hasattr(profile.__class__, "PROFILE_PATH") else None
        if path and path.exists():
            path.unlink()
            print("profile reset to defaults")
        else:
            print("no profile to reset")
        return 0

    import json as _json
    info = {
        "entries": len(profile.entries),
        "score_baseline": profile.score_baseline,
        "threshold": profile.adjusted_threshold(),
        "suppressed_flags": list(profile.suppressed_flags()),
        "learned_verbs": len(profile.learned_verbs),
        "learned_acronyms": dict(list(profile.learned_acronyms.items())[:10]),
        "learned_keywords": len(profile.learned_keywords),
    }
    print(_json.dumps(info, indent=2))
    return 0


def _cmd_compare(args) -> int:
    prompt = args.prompt
    if args.pipe or (not prompt and not sys.stdin.isatty()):
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("error: no prompt provided", file=sys.stderr)
        return 1

    provider = None if args.provider == "auto" else args.provider
    result = compare(prompt, provider=provider, no_llm=args.no_llm)

    if args.output_dir:
        path = write_experiment_files(result, args.output_dir)
        print(f"Experiment files written to {path}", file=sys.stderr)

    if args.json:
        print(json.dumps(render_compare_json(result), indent=2))
    else:
        print(render_compare_report(result))

    return 0


def _cmd_audit(args) -> int:
    prompt = args.prompt
    if args.pipe or (not prompt and not sys.stdin.isatty()):
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("error: no prompt provided", file=sys.stderr)
        return 1

    result = audit(prompt, directory=args.dir)
    if args.json:
        print(json.dumps(render_audit_json(result), indent=2))
    else:
        print(render_audit_report(result))
    return 1 if result.missing_files or result.permission_issues else 0


def _cmd_flow_test(args) -> int:
    report = flow_test()
    if args.json:
        print(json.dumps(render_flow_json(report), indent=2, sort_keys=False))
    else:
        print(render_flow_report(report))
    return 1 if report.summary["errors"] > 0 else 0


def _cmd_translate(args) -> int:
    prompt = args.prompt
    if args.pipe or (not prompt and not sys.stdin.isatty()):
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("error: no prompt provided", file=sys.stderr)
        return 1

    result = translate(prompt)
    if args.json:
        print(json.dumps(render_translate_json(result), indent=2))
    else:
        print(render_translate_report(result))
    return 0


def _cmd_clarify(args) -> int:
    prompt = args.prompt
    if args.pipe or (not prompt and not sys.stdin.isatty()):
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("error: no prompt provided", file=sys.stderr)
        return 1

    result = clarify(prompt)
    if args.json:
        print(json.dumps(render_clarify_json(result), indent=2))
    else:
        print(render_clarify_report(result))
    return 1 if result.questions else 0


def _cmd_log(args) -> int:
    if args.summary:
        print(memory_summary())
        return 0

    prompt = args.prompt
    if args.pipe or (not prompt and not sys.stdin.isatty()):
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("error: no prompt provided", file=sys.stderr)
        return 1

    from .memory import log_interaction
    from .translate import translate as do_translate

    changes = None
    if args.action == "translate":
        t_result = do_translate(prompt)
        changes = t_result.changes

    path = log_interaction(prompt, action=args.action, changes=changes, outcome=args.outcome, note=args.note)
    if not path:
        print("error: docs/memory.md not found", file=sys.stderr)
        return 1
    print(f"logged to {path}")
    return 0


def _cmd_import(args) -> int:
    result = discover(consent=args.consent, dry_run=not args.execute)
    if args.json:
        print(json.dumps(render_import_json(result), indent=2))
    else:
        print(render_import_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
