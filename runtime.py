"""Runtime helpers: env validation, logging, and transient-error retries."""
from __future__ import annotations

import logging
import os
import time
from typing import Callable, Iterable, Optional, TypeVar

from dotenv import load_dotenv

load_dotenv()

T = TypeVar("T")

REQUIRED_ENV_KEYS = ("GROQ_API_KEY", "TAVILY_API_KEY")

_LOGGER_NAME = "researchmind"
_logging_configured = False


class MissingEnvironmentError(RuntimeError):
    """Raised when required API keys are missing or empty."""


def _inject_streamlit_secrets() -> None:
    """Copy Streamlit Cloud / .streamlit/secrets.toml keys into os.environ."""
    try:
        import streamlit as st
    except Exception:
        return
    try:
        secrets = getattr(st, "secrets", None)
        if secrets is None:
            return
        for key in REQUIRED_ENV_KEYS:
            if os.getenv(key):
                continue
            try:
                val = secrets[key]
            except Exception:
                continue
            if val is not None and str(val).strip():
                os.environ[key] = str(val).strip()
    except Exception:
        return


def load_runtime_env() -> None:
    """Load .env then Streamlit secrets into the process environment."""
    load_dotenv()
    _inject_streamlit_secrets()


# Ensure keys are available as early as possible for local + cloud runs.
load_runtime_env()


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a single project logger (idempotent)."""
    global _logging_configured
    logger = logging.getLogger(_LOGGER_NAME)
    if not _logging_configured:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
        _logging_configured = True
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)


def missing_env_keys(keys: Iterable[str] = REQUIRED_ENV_KEYS) -> list[str]:
    """Return required env keys that are missing or blank."""
    missing = []
    for key in keys:
        val = os.getenv(key)
        if not val or not str(val).strip():
            missing.append(key)
    return missing


def require_env_keys(keys: Iterable[str] = REQUIRED_ENV_KEYS) -> None:
    """Raise MissingEnvironmentError if any required key is unset/blank."""
    # Re-check Streamlit secrets (covers cloud runs where .env is absent).
    _inject_streamlit_secrets()
    missing = missing_env_keys(keys)
    if missing:
        raise MissingEnvironmentError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Set them in .env (local) or Streamlit Cloud App settings → Secrets "
            "(keys: GROQ_API_KEY, TAVILY_API_KEY)."
        )


def is_transient_error(exc: BaseException) -> bool:
    """Best-effort classification of retryable network/rate-limit errors."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    transient_markers = (
        "timeout",
        "timed out",
        "connection",
        "temporarily",
        "rate limit",
        "ratelimit",
        "429",
        "502",
        "503",
        "504",
        "reset",
        "unavailable",
        "getaddrinfo",
        "name resolution",
    )
    if any(marker in name for marker in ("timeout", "connection", "ratelimit")):
        return True
    return any(marker in text for marker in transient_markers)


def call_with_retries(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    retry_on: Optional[Callable[[BaseException], bool]] = None,
    sleep: Optional[Callable[[float], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> T:
    """Call fn(), retrying transient failures with exponential backoff."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    should_retry = retry_on or is_transient_error
    log = logger or get_logger()
    sleeper = sleep if sleep is not None else time.sleep
    last_exc: Optional[BaseException] = None

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - classified below
            last_exc = exc
            if attempt >= attempts or not should_retry(exc):
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            log.warning(
                "Transient error on attempt %s/%s (%s); retrying in %.1fs",
                attempt,
                attempts,
                type(exc).__name__,
                delay,
            )
            sleeper(delay)

    assert last_exc is not None
    raise last_exc
