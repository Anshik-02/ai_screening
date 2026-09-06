"""
LLM client abstraction for TalentRank Studio.

All AI-powered features route through this module.
- Provider and model are configured entirely via environment variables.
- The recruiter workflow has zero dependency on this module.
- When OPENAI_API_KEY is absent, is_available() returns False and callers
  fall back to deterministic rule-based outputs.

Environment variables:
    LLM_PROVIDER   : "openai"  (default, only provider currently supported)
    OPENAI_API_KEY : Your OpenAI secret key.
    OPENAI_MODEL   : Model name (default: gpt-4o-mini).

NOTE: API keys are never forwarded to the frontend.
"""

from __future__ import annotations

import json
import os
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass



# ---------------------------------------------------------------------------
# Custom error hierarchy
# ---------------------------------------------------------------------------


class LLMError(Exception):
    """Base class for all LLM client errors."""


class LLMUnavailableError(LLMError):
    """No API key is configured; LLM features are disabled."""


class LLMAuthError(LLMError):
    """The API key is invalid or not authorised."""


class LLMRateLimitError(LLMError):
    """The provider rate limit has been exceeded."""


class LLMServiceError(LLMError):
    """Any other provider-side failure (5xx, network issues, etc.)."""


# ---------------------------------------------------------------------------
# Configuration helpers  (read from env on every call so tests can patch)
# ---------------------------------------------------------------------------


def _api_key() -> str:
    return (os.getenv("OPENAI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")).strip()


def _provider() -> str:
    prov = os.getenv("LLM_PROVIDER", "").strip().lower()
    key = _api_key()
    if prov in ("gemini", "openai"):
        return prov
    if key.startswith("AIzaSy"):
        return "gemini"
    return "openai"


def _model() -> str:
    env_model = os.getenv("OPENAI_MODEL", "").strip() or os.getenv("GEMINI_MODEL", "").strip()
    provider = _provider()
    if env_model and env_model != "gpt-4o-mini":
        return env_model
    if provider == "gemini":
        return "gemini-2.5-flash"
    return "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def is_available() -> bool:
    """Return True if the LLM client is fully configured and ready."""
    return bool(_api_key())


def chat_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """
    Send a chat request and parse the response as JSON.

    The provider is instructed to return JSON (`response_format=json_object`).

    Raises:
        LLMUnavailableError: No API key configured.
        LLMAuthError:        Invalid / unauthorized API key.
        LLMRateLimitError:   Rate limit exceeded.
        LLMServiceError:     Other provider-side failure.
        ValueError:          Provider returned non-JSON despite the format hint.
    """
    _require_key()
    return _dispatch_json(system_prompt, user_prompt, temperature=temperature)


def chat_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.5,
) -> str:
    """
    Send a chat request and return the raw text response.

    Raises:
        LLMUnavailableError: No API key configured.
        LLMAuthError:        Invalid / unauthorized API key.
        LLMRateLimitError:   Rate limit exceeded.
        LLMServiceError:     Other provider-side failure.
    """
    _require_key()
    return _dispatch_text(system_prompt, user_prompt, temperature=temperature)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_key() -> None:
    if not _api_key():
        raise LLMUnavailableError(
            "API key is not set. "
            "Set OPENAI_API_KEY or GEMINI_API_KEY in your .env file to enable AI features."
        )


def _dispatch_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
) -> dict[str, Any]:
    provider = _provider()
    if provider == "gemini":
        return _gemini_chat_json(system_prompt, user_prompt, temperature=temperature)
    if provider == "openai":
        return _openai_chat_json(system_prompt, user_prompt, temperature=temperature)
    raise LLMServiceError(f"Unsupported LLM_PROVIDER: '{provider}'. Supported: 'openai', 'gemini'.")


def _dispatch_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
) -> str:
    provider = _provider()
    if provider == "gemini":
        return _gemini_chat_text(system_prompt, user_prompt, temperature=temperature)
    if provider == "openai":
        return _openai_chat_text(system_prompt, user_prompt, temperature=temperature)
    raise LLMServiceError(f"Unsupported LLM_PROVIDER: '{provider}'. Supported: 'openai', 'gemini'.")


def _gemini_chat_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
) -> dict[str, Any]:
    import urllib.request
    import urllib.error

    key = _api_key()
    model = _model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    combined_prompt = f"System Instruction: {system_prompt}\n\nUser Request: {user_prompt}"
    payload = {
        "contents": [{"parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 403):
            raise LLMAuthError(f"Gemini API key invalid or unauthorized ({exc.code}).") from exc
        if exc.code == 429:
            raise LLMRateLimitError("Gemini rate limit exceeded.") from exc
        raise LLMServiceError(f"Gemini API error ({exc.code}): {exc.reason}") from exc
    except Exception as exc:
        if isinstance(exc, json.JSONDecodeError):
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc
        raise LLMServiceError(f"Failed to communicate with Gemini API: {exc}") from exc


def _gemini_chat_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
) -> str:
    import urllib.request
    import urllib.error

    key = _api_key()
    model = _model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    combined_prompt = f"System Instruction: {system_prompt}\n\nUser Request: {user_prompt}"
    payload = {
        "contents": [{"parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 403):
            raise LLMAuthError(f"Gemini API key invalid or unauthorized ({exc.code}).") from exc
        if exc.code == 429:
            raise LLMRateLimitError("Gemini rate limit exceeded.") from exc
        raise LLMServiceError(f"Gemini API error ({exc.code}): {exc.reason}") from exc
    except Exception as exc:
        raise LLMServiceError(f"Failed to communicate with Gemini API: {exc}") from exc


def _openai_chat_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
) -> dict[str, Any]:
    try:
        from openai import (
            OpenAI,
            AuthenticationError,
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
            APIStatusError,
        )
    except ImportError as exc:
        raise LLMServiceError(
            "The 'openai' package is not installed. Run: pip install openai>=1.40.0"
        ) from exc

    try:
        client = OpenAI(api_key=_api_key())
        response = client.chat.completions.create(
            model=_model(),
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    except AuthenticationError as exc:
        raise LLMAuthError(
            "OpenAI API key is invalid or not authorised. Check OPENAI_API_KEY."
        ) from exc
    except RateLimitError as exc:
        raise LLMRateLimitError(
            "OpenAI rate limit exceeded. Please wait a moment and try again."
        ) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise LLMServiceError(
            "Could not reach OpenAI. Check your internet connection and retry."
        ) from exc
    except APIStatusError as exc:
        raise LLMServiceError(
            f"OpenAI returned an error ({exc.status_code}). Please retry later."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc


def _openai_chat_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
) -> str:
    try:
        from openai import (
            OpenAI,
            AuthenticationError,
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
            APIStatusError,
        )
    except ImportError as exc:
        raise LLMServiceError(
            "The 'openai' package is not installed. Run: pip install openai>=1.40.0"
        ) from exc

    try:
        client = OpenAI(api_key=_api_key())
        response = client.chat.completions.create(
            model=_model(),
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""

    except AuthenticationError as exc:
        raise LLMAuthError(
            "OpenAI API key is invalid or not authorised. Check OPENAI_API_KEY."
        ) from exc
    except RateLimitError as exc:
        raise LLMRateLimitError(
            "OpenAI rate limit exceeded. Please wait a moment and try again."
        ) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise LLMServiceError(
            "Could not reach OpenAI. Check your internet connection and retry."
        ) from exc
    except APIStatusError as exc:
        raise LLMServiceError(
            f"OpenAI returned an error ({exc.status_code}). Please retry later."
        ) from exc

