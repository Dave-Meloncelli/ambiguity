import pytest
from ambiguity.hooks import (
    HookConfig, _extract_prompt_text, _handle_result,
    AnthropicHook, OpenaiHook,
)


def test_hook_config_defaults():
    c = HookConfig()
    assert c.gate == 6.0
    assert c.on_exceed == "warn"


def test_hook_config_custom():
    c = HookConfig(gate=3.0, on_exceed="block")
    assert c.gate == 3.0
    assert c.on_exceed == "block"


def test_extract_prompt_text_from_messages():
    messages = [{"role": "user", "content": "hello world"}]
    result = _extract_prompt_text(messages, {})
    assert result == "hello world"


def test_extract_prompt_text_from_kwargs():
    result = _extract_prompt_text(None, {"prompt": "hello"})
    assert result == "hello"


def test_extract_prompt_text_empty():
    assert _extract_prompt_text([], {}) == ""


def test_extract_prompt_text_content_list():
    messages = [{"role": "user", "content": [{"type": "text", "text": "hello"}]}]
    result = _extract_prompt_text(messages, {})
    assert result == "hello"


def test_extract_prompt_text_mixed():
    messages = [{"role": "user", "content": "first"}]
    result = _extract_prompt_text(messages, {"prompt": "second"})
    assert "first" in result
    assert "second" in result


def test_handle_result_below_gate():
    _handle_result(5.0, "medium", 6.0, "warn")


def test_handle_result_warn(capsys):
    _handle_result(7.0, "high", 6.0, "warn")
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "7.0" in captured.err


def test_handle_result_block():
    import pytest
    with pytest.raises(RuntimeError, match="BLOCKED"):
        _handle_result(8.0, "high", 6.0, "block")


def test_anthropic_hook_import_error():
    import importlib
    if importlib.util.find_spec("anthropic") is None:
        with pytest.raises(ImportError):
            AnthropicHook(api_key="test")


def test_openai_hook_import_error():
    import importlib
    import os
    key = os.environ.get("OPENAI_API_KEY")
    if not key and importlib.util.find_spec("openai") is None:
        with pytest.raises(ImportError):
                OpenaiHook(api_key="test")
