import agents
from langchain_core.runnables import RunnableSequence


def test_llm_model_configuration():
    assert agents.llm.model_name == "openai/gpt-oss-120b"
    # ChatGroq may coerce temperature=0.0 to a tiny epsilon
    assert agents.llm.temperature is not None
    assert float(agents.llm.temperature) < 1e-6


def test_build_search_agent_returns_graph():
    agent = agents.build_search_agent()
    assert agent is not None
    assert type(agent).__name__ == "CompiledStateGraph"


def test_build_reader_agent_returns_graph():
    agent = agents.build_reader_agent()
    assert agent is not None
    assert type(agent).__name__ == "CompiledStateGraph"


def test_writer_and_critic_are_runnable_sequences():
    assert isinstance(agents.writer_chain, RunnableSequence)
    assert isinstance(agents.critic_chain, RunnableSequence)


def test_build_reader_prompt_requires_scrape_and_includes_full_search():
    topic = "AI agents"
    search = (
        "Title: Docs\nURL: https://docs.example.com/agent\nSnippet: deep content\n"
        + "Title: News\nURL: https://news.example.com/ai\nSnippet: more\n"
    )
    prompt = agents.build_reader_prompt(topic, search)

    assert "Topic: AI agents" in prompt
    assert "https://docs.example.com/agent" in prompt
    assert "https://news.example.com/ai" in prompt
    assert "MUST call the scrape_url tool" in prompt
    assert "Do not ask the user" in prompt
    # full search payload is embedded (no truncation marker / cut)
    assert search in prompt


def test_build_reader_prompt_safe_with_braces_in_search():
    search = "JSON-ish {not_a_placeholder} and more"
    prompt = agents.build_reader_prompt("t", search)
    assert "{not_a_placeholder}" in prompt
    assert "Topic: t" in prompt
