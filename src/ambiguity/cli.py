"""CLI entry point for ambiguity."""

import argparse
import json
import sys
from . import __version__
from .analyzer import Analysis
from .profile import get_profile


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _cmd_analyze(args)
    elif args.command == "learn":
        return _cmd_learn(args)
    elif args.command == "dismiss":
        return _cmd_dismiss(args)
    elif args.command == "config":
        return _cmd_config(args)

    parser.print_help()
    return 0


def _cmd_analyze(args) -> int:
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


if __name__ == "__main__":
    raise SystemExit(main())
