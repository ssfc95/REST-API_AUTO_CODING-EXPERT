"""
Tests for the REST-API AUTO CODING EXPERT service.

These tests use FastAPI's TestClient and mock the OpenAI client so no real API
key is required during CI.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main as app_module
from main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_openai_response(content: str = "분석 결과입니다.", model: str = "gpt-4o"):
    """Build a minimal mock that mimics openai.types.chat.ChatCompletion."""
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 200

    message = MagicMock()
    message.content = content

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    response.model = model
    response.usage = usage
    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def client():
    """Return a synchronous TestClient with a fresh _openai_client state."""
    app_module._openai_client = None
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_openai(monkeypatch):
    """Patch AsyncOpenAI so tests never hit the real API."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_openai_response()
    )

    monkeypatch.setattr("main._openai_client", mock_client)
    return mock_client


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
class TestHealthCheck:
    def test_returns_200_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /analyze — happy-path
# ---------------------------------------------------------------------------
class TestAnalyzeHappyPath:
    def test_returns_200_with_analysis(self, client, mock_openai):
        payload = {
            "code": "while True:\n    buy('005930', 10)",
            "language": "Python",
            "additional_context": "KOSPI momentum strategy",
        }
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["analysis"] == "분석 결과입니다."
        assert body["model"] == "gpt-4o"
        assert body["input_tokens"] == 100
        assert body["output_tokens"] == 200

    def test_optional_fields_omitted(self, client, mock_openai):
        """language and additional_context are optional."""
        payload = {"code": "buy('005930', 10)  # minimal code"}
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 200

    def test_system_prompt_included_in_call(self, client, mock_openai):
        """Verify the expert system prompt is forwarded to the LLM."""
        payload = {"code": "sell_all()  # dangerous code"}
        client.post("/analyze", json=payload)

        call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "50년 경력" in system_msg["content"]
        assert "이 코드는 시장의 변동성을 견딜 수 있겠습니까?" in system_msg["content"]

    def test_user_message_contains_code(self, client, mock_openai):
        """The submitted code must appear in the user message."""
        code_snippet = "def strategy(): pass  # unique-sentinel"
        payload = {"code": code_snippet}
        client.post("/analyze", json=payload)

        call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert code_snippet in user_msg["content"]

    def test_user_message_contains_language_and_context(self, client, mock_openai):
        payload = {
            "code": "buy('000660', 5)",
            "language": "Python",
            "additional_context": "SK Hynix momentum",
        }
        client.post("/analyze", json=payload)

        call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "Python" in user_msg["content"]
        assert "SK Hynix momentum" in user_msg["content"]


# ---------------------------------------------------------------------------
# /analyze — validation errors
# ---------------------------------------------------------------------------
class TestAnalyzeValidation:
    def test_missing_code_field(self, client):
        resp = client.post("/analyze", json={})
        assert resp.status_code == 422

    def test_code_too_short(self, client):
        """code must be at least 10 characters."""
        resp = client.post("/analyze", json={"code": "short"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /analyze — upstream error handling
# ---------------------------------------------------------------------------
class TestAnalyzeUpstreamError:
    def test_openai_error_returns_502(self, client, monkeypatch):
        from openai import OpenAIError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("connection failed")
        )
        monkeypatch.setattr("main._openai_client", mock_client)

        payload = {"code": "buy('005930', 10)  # test error path"}
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 502
        assert "connection failed" in resp.json()["detail"]
