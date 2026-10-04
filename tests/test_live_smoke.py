"""Optional live smoke tests — call real Tavily/Groq APIs.

Run explicitly (requires .env keys + network):

    pytest --live
"""
import os
from pathlib import Path

import pytest


def _load_env_keys():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


@pytest.mark.live
def test_live_web_search_and_llm_pipeline():
    _load_env_keys()
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("GROQ_API_KEY"):
        pytest.skip("TAVILY_API_KEY / GROQ_API_KEY not set")

    import tools
    from agents import llm

    search_out = tools.web_search.func("latest AI agent frameworks 2025")
    assert search_out
    assert not search_out.startswith("WEB_SEARCH_FAILED")

    reply = llm.invoke("Reply with exactly: OK")
    assert "OK" in reply.content
