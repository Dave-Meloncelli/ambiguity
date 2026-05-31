from ambiguity.cli import build_parser


def test_build_parser_returns_argparse_parser():
    parser = build_parser()
    assert parser is not None
    assert parser.prog == "ambiguity"


def test_parser_has_analyze_command():
    parser = build_parser()
    args = parser.parse_args(["analyze", "test prompt"])
    assert args.command == "analyze"


def test_parser_has_pipe_flag():
    parser = build_parser()
    args = parser.parse_args(["analyze", "--pipe"])
    assert args.command == "analyze"
    assert args.pipe is True


def test_parser_has_json_flag():
    parser = build_parser()
    args = parser.parse_args(["analyze", "test", "--json"])
    assert args.json is True


def test_parser_has_gate_flag():
    parser = build_parser()
    args = parser.parse_args(["analyze", "test", "--gate", "7.0"])
    assert args.gate == 7.0


def test_parser_has_quiet_flag():
    parser = build_parser()
    args = parser.parse_args(["analyze", "test", "--quiet"])
    assert args.quiet is True


def test_parser_learn_command():
    parser = build_parser()
    args = parser.parse_args(["learn", "verb", "deploy"])
    assert args.command == "learn"


def test_parser_dismiss_command():
    parser = build_parser()
    args = parser.parse_args(["dismiss", "test_flag"])
    assert args.command == "dismiss"


def test_parser_config_command():
    parser = build_parser()
    args = parser.parse_args(["config"])
    assert args.command == "config"


def test_parser_technical_command():
    parser = build_parser()
    args = parser.parse_args(["technical", "test prompt", "--json"])
    assert args.command == "technical"
    assert args.json is True


def test_parser_technical_self_test():
    parser = build_parser()
    args = parser.parse_args(["technical", "--self-test"])
    assert args.self_test is True


def test_parser_compare_command():
    parser = build_parser()
    args = parser.parse_args(["compare", "test prompt", "--no-llm"])
    assert args.command == "compare"
    assert args.no_llm is True


def test_parser_review_command():
    parser = build_parser()
    args = parser.parse_args(["review", "test prompt", "--response", "ok"])
    assert args.command == "review"
    assert args.response == "ok"


def test_parser_translate_command():
    parser = build_parser()
    args = parser.parse_args(["translate", "test prompt", "--json"])
    assert args.command == "translate"
    assert args.json is True


def test_parser_clarify_command():
    parser = build_parser()
    args = parser.parse_args(["clarify", "test prompt", "--json"])
    assert args.command == "clarify"
    assert args.json is True


def test_parser_audit_command():
    parser = build_parser()
    args = parser.parse_args(["audit"])
    assert args.command == "audit"


def test_parser_flow_test_command():
    parser = build_parser()
    args = parser.parse_args(["flow-test"])
    assert args.command == "flow-test"


def test_help():
    parser = build_parser()
    help_text = parser.format_help()
    assert "analyze" in help_text
    assert "learn" in help_text
    assert "compare" in help_text
