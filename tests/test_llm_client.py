"""
Tests for llm_client.py — all OpenAI calls are mocked.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services import llm_client
from app.services.llm_client import (
    LLMAuthError,
    LLMRateLimitError,
    LLMServiceError,
    LLMUnavailableError,
)


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


def test_is_available_false_when_no_key():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        assert llm_client.is_available() is False


def test_is_available_true_when_key_set():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}, clear=False):
        assert llm_client.is_available() is True


# ---------------------------------------------------------------------------
# chat_json — happy path
# ---------------------------------------------------------------------------


def _mock_openai_json_response(content: dict):
    """Build a minimal mock that looks like an OpenAI ChatCompletion response."""
    msg = MagicMock()
    msg.content = json.dumps(content)
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("app.services.llm_client._api_key", return_value="sk-test")
@patch("app.services.llm_client._model", return_value="gpt-4o-mini")
def test_chat_json_returns_parsed_dict(mock_model, mock_key):
    expected = {"narrative": "Great candidate.", "suggestions": []}
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_json_response(expected)

    with patch("app.services.llm_client._openai_chat_json") as mock_fn:
        mock_fn.return_value = expected
        result = llm_client.chat_json("system", "user")

    assert result == expected


# ---------------------------------------------------------------------------
# chat_json — error mapping
# ---------------------------------------------------------------------------


def test_chat_json_raises_unavailable_when_no_key():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        with pytest.raises(LLMUnavailableError):
            llm_client.chat_json("sys", "user")


@patch("app.services.llm_client._api_key", return_value="sk-bad")
def test_chat_json_maps_auth_error(mock_key):
    with patch("app.services.llm_client._openai_chat_json") as mock_fn:
        mock_fn.side_effect = LLMAuthError("bad key")
        with pytest.raises(LLMAuthError):
            llm_client.chat_json("sys", "user")


@patch("app.services.llm_client._api_key", return_value="sk-test")
def test_chat_json_maps_rate_limit(mock_key):
    with patch("app.services.llm_client._openai_chat_json") as mock_fn:
        mock_fn.side_effect = LLMRateLimitError("rate limited")
        with pytest.raises(LLMRateLimitError):
            llm_client.chat_json("sys", "user")


@patch("app.services.llm_client._api_key", return_value="sk-test")
def test_chat_json_maps_service_error(mock_key):
    with patch("app.services.llm_client._openai_chat_json") as mock_fn:
        mock_fn.side_effect = LLMServiceError("500")
        with pytest.raises(LLMServiceError):
            llm_client.chat_json("sys", "user")


def test_gemini_key_auto_detect():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "AIzaSyB_test", "LLM_PROVIDER": ""}, clear=False):
        assert llm_client._provider() == "gemini"
        assert llm_client._model() == "gemini-2.5-flash"

