from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from benchbro.adapters.base import Capabilities, ModelMeta
from benchbro.adapters.detection import detect_backends
from benchbro.adapters.ollama import OllamaAdapter
from benchbro.adapters.openai_compat import OpenAICompatAdapter


# ---------------------------------------------------------------------------
# 1. Capabilities dataclass
# ---------------------------------------------------------------------------

def test_capabilities_dataclass():
    caps = Capabilities(
        supports_logprobs=True,
        supports_batching=False,
        supports_chat=True,
        supports_stop_sequences=True,
        supports_token_count=False,
        max_context_known=4096,
        backend_type="ollama",
    )
    assert caps.supports_logprobs is True
    assert caps.supports_batching is False
    assert caps.supports_chat is True
    assert caps.supports_stop_sequences is True
    assert caps.supports_token_count is False
    assert caps.max_context_known == 4096
    assert caps.backend_type == "ollama"


# ---------------------------------------------------------------------------
# 2. ModelMeta dataclass
# ---------------------------------------------------------------------------

def test_model_meta_dataclass():
    meta = ModelMeta(
        name="llama3:8b",
        param_count=8_000_000_000,
        quant_format="Q4_K_M",
        context_length=8192,
        backend="ollama",
        file_hash="abc123",
        extra={"source": "huggingface"},
    )
    assert meta.name == "llama3:8b"
    assert meta.param_count == 8_000_000_000
    assert meta.quant_format == "Q4_K_M"
    assert meta.context_length == 8192
    assert meta.backend == "ollama"
    assert meta.file_hash == "abc123"
    assert meta.extra == {"source": "huggingface"}


# ---------------------------------------------------------------------------
# 3. OllamaAdapter.generate (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ollama_adapter_generate():
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="llama3:8b")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "Hello from Ollama!"}

    mock_post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await adapter.generate("Say hello", {})

    assert result == "Hello from Ollama!"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "api/generate" in call_kwargs[0][0]


# ---------------------------------------------------------------------------
# 4. OllamaAdapter capabilities
# ---------------------------------------------------------------------------

def test_ollama_adapter_capabilities():
    adapter = OllamaAdapter(base_url="http://localhost:11434", model_name="llama3:8b")
    caps = adapter.get_capabilities()
    assert caps.backend_type == "ollama"
    assert caps.supports_chat is True


# ---------------------------------------------------------------------------
# 5. OpenAICompatAdapter.generate (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openai_compat_adapter_generate():
    adapter = OpenAICompatAdapter(
        base_url="http://localhost:8080", model_name="mistral-7b"
    )

    openai_response = {
        "choices": [
            {
                "message": {"role": "assistant", "content": "Hello from OpenAI-compat!"},
                "finish_reason": "stop",
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = openai_response

    mock_post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await adapter.generate("Say hello", {})

    assert result == "Hello from OpenAI-compat!"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "chat/completions" in call_kwargs[0][0]


# ---------------------------------------------------------------------------
# 6. detect_backends — none running (connection refused)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_backends_none_running():
    import httpx

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await detect_backends()

    assert result == []
