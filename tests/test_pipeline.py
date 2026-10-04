from tests.fakes import FakeAgent, FakeChain
from unittest.mock import patch

import pytest

import pipeline
from runtime import MissingEnvironmentError


SEARCH_OK = (
    "Title: Doc\nURL: https://docs.example.com/x\nSnippet: info\n"
    "Title: News\nURL: https://news.example.com/y\nSnippet: more\n"
)
READER_OK = "Deep scraped content about the topic from docs.example.com."
REPORT_OK = "## Report\nIntroduction\nKey Findings\nConclusion\nSources"
FEEDBACK_OK = "Score: 8/10\nStrengths:\n- clear\nOne line verdict:\ngood work"


def _run_with_mocks(search_content, reader_content, report, feedback):
    search_agent = FakeAgent(search_content)
    reader_agent = FakeAgent(reader_content)
    writer = FakeChain(report)
    critic = FakeChain(feedback)

    with patch.object(pipeline, "build_search_agent", return_value=search_agent), \
         patch.object(pipeline, "build_reader_agent", return_value=reader_agent), \
         patch.object(pipeline, "writer_chain", writer), \
         patch.object(pipeline, "critic_chain", critic), \
         patch.object(pipeline, "require_env_keys"), \
         patch.object(pipeline, "_llm_step", side_effect=lambda label, fn: fn()):
        state = pipeline.run_research_pipeline("test topic")

    return state, search_agent, reader_agent, writer, critic


def test_run_research_pipeline_happy_path_returns_all_keys():
    state, search_agent, reader_agent, writer, critic = _run_with_mocks(
        SEARCH_OK, READER_OK, REPORT_OK, FEEDBACK_OK
    )

    assert set(state.keys()) == {
        "search_results",
        "scraped_content",
        "report",
        "feedback",
    }
    assert state["search_results"] == SEARCH_OK
    assert state["scraped_content"] == READER_OK
    assert state["report"] == REPORT_OK
    assert state["feedback"] == FEEDBACK_OK


def test_reader_receives_full_search_results_not_truncated():
    long_search = SEARCH_OK + ("URL: https://example.com/deep-page\n" * 200)
    state, search_agent, reader_agent, writer, critic = _run_with_mocks(
        long_search, READER_OK, REPORT_OK, FEEDBACK_OK
    )

    assert reader_agent.calls, "reader agent was not invoked"
    prompt = reader_agent.calls[0]["messages"][0][1]
    assert long_search in prompt
    assert "https://example.com/deep-page" in prompt


def test_pipeline_skips_reader_when_search_failed():
    state, search_agent, reader_agent, writer, critic = _run_with_mocks(
        "WEB_SEARCH_FAILED: could not reach the search API. Error: boom",
        READER_OK,
        REPORT_OK,
        FEEDBACK_OK,
    )

    assert state["scraped_content"].startswith("SKIPPED_READER")
    assert reader_agent.calls == []
    assert state["report"] == REPORT_OK
    assert state["feedback"] == FEEDBACK_OK


def test_pipeline_skips_reader_when_search_empty():
    state, search_agent, reader_agent, writer, critic = _run_with_mocks(
        "WEB_SEARCH_EMPTY: no results found for this query.",
        READER_OK,
        REPORT_OK,
        FEEDBACK_OK,
    )

    assert state["scraped_content"].startswith("SKIPPED_READER")
    assert reader_agent.calls == []


def test_writer_receives_combined_search_and_reader_payload():
    state, search_agent, reader_agent, writer, critic = _run_with_mocks(
        SEARCH_OK, READER_OK, REPORT_OK, FEEDBACK_OK
    )

    assert writer.calls, "writer was not invoked"
    payload = writer.calls[0]
    assert payload["topic"] == "test topic"
    assert SEARCH_OK in payload["research"]
    assert READER_OK in payload["research"]


def test_critic_receives_report_payload():
    state, search_agent, reader_agent, writer, critic = _run_with_mocks(
        SEARCH_OK, READER_OK, REPORT_OK, FEEDBACK_OK
    )

    assert critic.calls, "critic was not invoked"
    assert critic.calls[0]["report"] == REPORT_OK


def test_ensure_utf8_stdout_does_not_raise():
    pipeline._ensure_utf8_stdout()


def test_pipeline_requires_env_keys(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with patch.object(pipeline, "build_search_agent"), \
         patch.object(pipeline, "_llm_step", side_effect=lambda label, fn: fn()):
        with pytest.raises(MissingEnvironmentError):
            pipeline.run_research_pipeline("topic")
