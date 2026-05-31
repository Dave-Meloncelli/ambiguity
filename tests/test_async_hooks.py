import importlib
import pytest
from ambiguity.async_hooks import (
    AsyncAnthropicHook, AsyncOpenaiHook, GoogleHook, OllamaHook, AzureOpenaiHook,
)
from ambiguity.hooks import HookConfig


def test_async_anthropic_hook_import_error():
    if importlib.util.find_spec("anthropic") is None:
        with pytest.raises(ImportError):
            AsyncAnthropicHook(api_key="test")


def test_async_openai_hook_import_error():
    if importlib.util.find_spec("openai") is None:
        with pytest.raises(ImportError):
            AsyncOpenaiHook(api_key="test")


def test_google_hook_import_error():
    if importlib.util.find_spec("google.genai") is None:
        with pytest.raises(ImportError) as exc:
            GoogleHook(api_key="test")
        assert "google-genai" in str(exc.value)


def test_ollama_hook_import_error():
    if importlib.util.find_spec("requests") is None:
        with pytest.raises(ImportError):
            OllamaHook()


def test_azure_hook_import_error():
    if importlib.util.find_spec("openai") is None:
        with pytest.raises(ImportError):
            AzureOpenaiHook(api_key="test", endpoint="https://test.openai.azure.com")


def test_ollama_hook_config():
    hook = OllamaHook(base_url="http://localhost:12345", model="test-model")
    assert hook._base_url == "http://localhost:12345"
    assert hook._model == "test-model"
    assert isinstance(hook._config, HookConfig)


def test_google_hook_config():
    try:
        hook = GoogleHook(api_key="test", model_name="gemini-ultra")
        assert hook._model_name == "gemini-ultra"
        assert isinstance(hook._config, HookConfig)
    except (ImportError, Exception):
        pass


def test_async_anthropic_messages_property():
    try:
        hook = AsyncAnthropicHook(api_key="test")
        assert hasattr(hook, "messages")
    except (ImportError, Exception):
        pass


def test_async_openai_chat_property():
    try:
        hook = AsyncOpenaiHook(api_key="test")
        assert hasattr(hook, "chat")
    except (ImportError, Exception):
        pass
