"""Async and additional LLM provider hooks — auto-analyze prompts before submission."""

from __future__ import annotations

from typing import Any, Literal

from .analyzer import Analysis
from .hooks import HookConfig, _extract_prompt_text, _handle_result, _log_hook_call

__all__ = [
    "AsyncAnthropicHook",
    "AsyncOpenaiHook",
    "GoogleHook",
    "OllamaHook",
    "AzureOpenaiHook",
]


class _AsyncAnthropicMessagesProxy:
    def __init__(self, client: Any, config: HookConfig):
        self._client = client
        self._config = config

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        messages = kwargs.get("messages", [])
        prompt = _extract_prompt_text(messages, kwargs)
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)
        return await self._client.messages.create(*args, **kwargs)


class AsyncAnthropicHook:
    """Wraps anthropic.AsyncAnthropic — analyzes prompts before each async messages.create() call."""

    def __init__(self, api_key: str | None = None, config: HookConfig | None = None):
        self._config = config or HookConfig()
        try:
            import anthropic

            self._client = (
                anthropic.AsyncAnthropic(api_key=api_key)
                if api_key
                else anthropic.AsyncAnthropic()
            )
        except ImportError:
            raise ImportError("anthropic SDK not installed (pip install anthropic)")

    @property
    def messages(self) -> _AsyncAnthropicMessagesProxy:
        return _AsyncAnthropicMessagesProxy(self._client, self._config)


class _AsyncOpenaiChatProxy:
    def __init__(self, client: Any, config: HookConfig):
        self._client = client
        self._config = config

    def completions(self) -> _AsyncOpenaiCompletionsProxy:
        return _AsyncOpenaiCompletionsProxy(self._client, self._config)


class _AsyncOpenaiCompletionsProxy:
    def __init__(self, client: Any, config: HookConfig):
        self._client = client
        self._config = config

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        messages = kwargs.get("messages", [])
        prompt = _extract_prompt_text(messages, kwargs)
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)
        return await self._client.chat.completions.create(*args, **kwargs)


class AsyncOpenaiHook:
    """Wraps openai.AsyncOpenAI — analyzes prompts before each async chat.completions.create() call."""

    def __init__(self, api_key: str | None = None, config: HookConfig | None = None):
        self._config = config or HookConfig()
        try:
            import openai

            self._client = (
                openai.AsyncOpenAI(api_key=api_key)
                if api_key
                else openai.AsyncOpenAI()
            )
        except ImportError:
            raise ImportError("openai SDK not installed (pip install openai)")

    @property
    def chat(self) -> _AsyncOpenaiChatProxy:
        return _AsyncOpenaiChatProxy(self._client, self._config)


class GoogleHook:
    """Wraps google.genai — analyzes prompts before each generation."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-pro",
        config: HookConfig | None = None,
    ):
        self._config = config or HookConfig()
        self._model_name = model_name
        try:
            import google.genai as genai

            if api_key:
                genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name)
        except ImportError:
            raise ImportError(
                "google-genai SDK not installed (pip install google-genai)"
            )

    def generate(self, prompt: str) -> str:
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)
        response = self._model.generate_content(prompt)
        return response.text


class OllamaHook:
    """Uses requests to talk to a local Ollama instance — analyzes prompts before generation."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        config: HookConfig | None = None,
    ):
        self._config = config or HookConfig()
        self._base_url = base_url.rstrip("/")
        self._model = model
        try:
            import requests  # noqa: F401
        except ImportError:
            raise ImportError("requests not installed (pip install requests)")

    def generate(self, prompt: str) -> dict[str, Any]:
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)

        import requests

        resp = requests.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()


class _AzureChatProxy:
    def __init__(self, client: Any, config: HookConfig):
        self._client = client
        self._config = config

    def completions(self) -> _AzureCompletionsProxy:
        return _AzureCompletionsProxy(self._client, self._config)


class _AzureCompletionsProxy:
    def __init__(self, client: Any, config: HookConfig):
        self._client = client
        self._config = config

    def create(self, *args: Any, **kwargs: Any) -> Any:
        messages = kwargs.get("messages", [])
        prompt = _extract_prompt_text(messages, kwargs)
        analysis = Analysis(prompt)
        score = analysis.score.total
        band = analysis.score.band
        _log_hook_call(prompt, score, band, self._config.gate, self._config.on_exceed)
        _handle_result(score, band, self._config.gate, self._config.on_exceed)
        return self._client.chat.completions.create(*args, **kwargs)


class AzureOpenaiHook:
    """Wraps openai.AzureOpenAI — analyzes prompts before each chat.completions.create() call."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        config: HookConfig | None = None,
    ):
        self._config = config or HookConfig()
        try:
            import openai

            self._client = openai.AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
            )
        except ImportError:
            raise ImportError("openai SDK not installed (pip install openai)")

    @property
    def chat(self) -> _AzureChatProxy:
        return _AzureChatProxy(self._client, self._config)
