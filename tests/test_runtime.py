import logging
import os
from unittest.mock import MagicMock, patch

import pytest

import runtime
from runtime import (
    MissingEnvironmentError,
    call_with_retries,
    is_transient_error,
    missing_env_keys,
    require_env_keys,
    setup_logging,
)


def test_missing_env_keys_detects_blank_and_unset(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert set(missing_env_keys()) == {"GROQ_API_KEY", "TAVILY_API_KEY"}

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("TAVILY_API_KEY", "   ")
    assert missing_env_keys() == ["TAVILY_API_KEY"]

    monkeypatch.setenv("TAVILY_API_KEY", "tvly_test")
    assert missing_env_keys() == []


def test_require_env_keys_raises_with_helpful_message(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "tvly_test")
    with pytest.raises(MissingEnvironmentError) as exc:
        require_env_keys()
    assert "GROQ_API_KEY" in str(exc.value)
    assert "Secrets" in str(exc.value) or ".env" in str(exc.value)


def test_require_env_keys_passes_when_set(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly_test")
    require_env_keys()  # should not raise


def test_inject_streamlit_secrets_fills_missing_env(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    fake_st = MagicMock()
    fake_st.secrets = {"GROQ_API_KEY": "gsk_from_secrets", "TAVILY_API_KEY": "tvly_from_secrets"}

    with patch.dict("sys.modules", {"streamlit": fake_st}):
        runtime._inject_streamlit_secrets()

    assert os.environ.get("GROQ_API_KEY") == "gsk_from_secrets"
    assert os.environ.get("TAVILY_API_KEY") == "tvly_from_secrets"


def test_inject_streamlit_secrets_does_not_override_existing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "already_set")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    fake_st = MagicMock()
    fake_st.secrets = {"GROQ_API_KEY": "from_secrets", "TAVILY_API_KEY": "tvly_new"}

    with patch.dict("sys.modules", {"streamlit": fake_st}):
        runtime._inject_streamlit_secrets()

    assert os.environ.get("GROQ_API_KEY") == "already_set"
    assert os.environ.get("TAVILY_API_KEY") == "tvly_new"


def test_inject_streamlit_secrets_safe_without_streamlit(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "tvly_test")
    # Ensure import failure path does not raise
    with patch.dict("sys.modules", {"streamlit": None}):
        runtime._inject_streamlit_secrets()
    # still missing GROQ only
    assert runtime.missing_env_keys() == ["GROQ_API_KEY"]


@pytest.mark.parametrize(
    "exc,expected",
    [
        (TimeoutError("timed out"), True),
        (ConnectionError("connection reset"), True),
        (RuntimeError("Rate limit reached for model"), True),
        (RuntimeError("Error code: 429"), True),
        (ValueError("bad request"), False),
        (RuntimeError("invalid api key"), False),
    ],
)
def test_is_transient_error_classification(exc, expected):
    assert is_transient_error(exc) is expected


def test_call_with_retries_success_first_try():
    fn = MagicMock(return_value="ok")
    assert call_with_retries(fn, attempts=3, sleep=lambda _: None) == "ok"
    assert fn.call_count == 1


def test_call_with_retries_recovers_after_transient_failures():
    fn = MagicMock(side_effect=[ConnectionError("blip"), TimeoutError("t/o"), "ok"])
    sleeps = []
    assert call_with_retries(fn, attempts=3, sleep=sleeps.append) == "ok"
    assert fn.call_count == 3
    assert len(sleeps) == 2
    assert sleeps[0] < sleeps[1]  # exponential backoff


def test_call_with_retries_raises_after_exhaustion():
    fn = MagicMock(side_effect=ConnectionError("still down"))
    with pytest.raises(ConnectionError):
        call_with_retries(fn, attempts=2, base_delay=0.01, sleep=lambda _: None)
    assert fn.call_count == 2


def test_call_with_retries_does_not_retry_non_transient():
    fn = MagicMock(side_effect=ValueError("permanent"))
    with pytest.raises(ValueError):
        call_with_retries(fn, attempts=5, sleep=lambda _: None)
    assert fn.call_count == 1


def test_call_with_retries_respects_custom_retry_predicate():
    fn = MagicMock(side_effect=RuntimeError("rate limit"))
    with pytest.raises(RuntimeError):
        call_with_retries(fn, attempts=4, retry_on=lambda e: False, sleep=lambda _: None)
    assert fn.call_count == 1


def test_setup_logging_is_idempotent():
    logger1 = setup_logging()
    logger2 = setup_logging()
    assert logger1 is logger2
    assert logger1.name == "researchmind"
    assert logger1.handlers


def test_web_search_uses_retry_on_transient_then_succeeds():
    import tools

    mock_client = MagicMock()
    mock_client.search.side_effect = [
        ConnectionError("blip"),
        {"results": [{"title": "T", "url": "https://x.example", "content": "c"}]},
    ]
    with patch.object(tools, "tavily", mock_client), \
         patch.object(runtime, "time") as mock_time:
        mock_time.sleep = lambda _: None
        out = tools.web_search.func("q")
    assert "URL: https://x.example" in out
    assert mock_client.search.call_count == 2


def test_web_search_reports_failure_after_retries_exhausted():
    import tools

    mock_client = MagicMock()
    mock_client.search.side_effect = ConnectionError("down")
    with patch.object(tools, "tavily", mock_client), \
         patch.object(tools, "call_with_retries", side_effect=ConnectionError("down")):
        out = tools.web_search.func("q")
    assert out.startswith("WEB_SEARCH_FAILED")
    assert "down" in out
