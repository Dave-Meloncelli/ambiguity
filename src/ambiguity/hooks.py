"""LLM client wrappers — auto-analyze prompts before submission."""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .analyzer import Analysis

HOOK_LOG = Path.home() / ".ambiguity" / "hooks.log"
HOOK_LOG.parent.mkdir(parents=True, exist_ok=True)

HookAction = Literal["warn", "block", "log"]


@dataclass
class HookConfig:
    gate: float = 6.0
    on_exceed: HookAction = "warn"
    log_path: Path = HOOK_LOG


def _extract_prompt_text(messages: list | None, kwargs: dict) -> str:
    texts: list[str] = []
    if messages:
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
            elif isinstance(content, str):
                texts.append(content)
    prompt = kwargs.get("prompt", "")
    if prompt:
        texts.append(str(prompt))
    return "\n".join(texts)


def _log_hook_call(prompt: str, score: float, band: str, threshold: float, action: str) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt_preview": prompt[:120],
        "score": round(score, 1),
        "band": band,
        "threshold": threshold,
        "action": action,
    }
    with open(HOOK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _handle_result(score: float, band: str, threshold: float, action: HookAction) -> None:
    if score < threshold:
        return
    msg = f"[ambiguity] score {score:.1f}/{band} exceeds gate {threshold:.1f}"
    if action == "warn":
        print(f"WARNING: {msg}", file=sys.stderr)
    elif action == "block":
        raise RuntimeError(f"BLOCKED: {msg}")
    elif action == "log":
        pass


class AnthropicHook:
    """Wraps anthropic.Anthropic — analyzes prompts before each messages.create() call."""

    def __init__(self, api_key: str | None = None, config: HookConfig | None = None):
        self._config = config or HookConfig()
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        except ImportError:
            raise ImportError("anthropic SDK not installed (pip install anthropic)")

    @property
    def messages(self):
        return _AnthropicMessagesProxy(self._client, self._config)


class _AnthropicMessagesProxy:
    def __init__(self, client, config: HookConfig):
        self._client = client
        self._config = config

    def create(self, *args, **kwargs):
        messages = kwargs.get("messages", [])
        prompt = _extract_prompt_text(messages, kwargs)
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)
        return self._client.messages.create(*args, **kwargs)


class OpenaiHook:
    """Wraps openai.OpenAI — analyzes prompts before each chat.completions.create() call."""

    def __init__(self, api_key: str | None = None, config: HookConfig | None = None):
        self._config = config or HookConfig()
        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()
        except ImportError:
            raise ImportError("openai SDK not installed (pip install openai)")

    @property
    def chat(self):
        return _OpenaiChatProxy(self._client, self._config)


class _OpenaiChatProxy:
    def __init__(self, client, config: HookConfig):
        self._client = client
        self._config = config

    def completions(self):
        return _OpenaiCompletionsProxy(self._client, self._config)


class _OpenaiCompletionsProxy:
    def __init__(self, client, config: HookConfig):
        self._client = client
        self._config = config

    def create(self, *args, **kwargs):
        messages = kwargs.get("messages", [])
        prompt = _extract_prompt_text(messages, kwargs)
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)
        return self._client.chat.completions.create(*args, **kwargs)
