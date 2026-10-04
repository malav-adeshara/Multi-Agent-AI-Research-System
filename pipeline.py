import sys
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain, build_reader_prompt
from runtime import (
    MissingEnvironmentError,
    call_with_retries,
    get_logger,
    require_env_keys,
    setup_logging,
)

_logger = None


def _ensure_utf8_stdout() -> None:
    """Avoid Windows cp1252 crashes when printing research text with Unicode."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _llm_step(label: str, fn):
    """Run an LLM/agent step with retries on transient API errors."""
    return call_with_retries(fn, attempts=3, base_delay=2.0, logger=_logger)


def run_research_pipeline(topic: str) -> dict:
    global _logger
    setup_logging()
    _logger = get_logger()
    require_env_keys()
    _logger.info("pipeline start topic=%r", topic)

    state = {}

    # Search Agent Working
    print("\n" + "= " * 40)
    print("step 1 - search agent is working ...")
    print("= " * 40)

    search_agent = build_search_agent()
    search_result = _llm_step(
        "search",
        lambda: search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        }),
    )

    state["search_results"] = search_result["messages"][-1].content or ""
    _logger.info("search step done chars=%s", len(state["search_results"]))

    print("\nsearch result : ", state["search_results"])

    # step 2 - reader agent
    print("\n" + "= " * 40)
    print("step 2 - Reader agent is scraping top resources ...")
    print("= " * 40)

    search_results = state["search_results"]
    if not search_results.strip() or search_results.startswith("WEB_SEARCH_FAILED") or search_results.startswith("WEB_SEARCH_EMPTY"):
        state["scraped_content"] = (
            "SKIPPED_READER: no usable search results, so scraping was skipped. "
            f"Search output was: {search_results[:500]}"
        )
        _logger.warning("reader skipped: unusable search output")
        print("\nscraped_content\n", state["scraped_content"])
    else:
        reader_agent = build_reader_agent()
        reader_result = _llm_step(
            "reader",
            lambda: reader_agent.invoke({
                "messages": [("user", build_reader_prompt(topic, search_results))]
            }),
        )
        state["scraped_content"] = reader_result["messages"][-1].content or ""
        _logger.info("reader step done chars=%s", len(state["scraped_content"]))
        print("\nscraped_content\n", state["scraped_content"])

    # step 3 - writer chain
    print("\n" + "= " * 40)
    print("step 3 - Writer is drafting the report ...")
    print("= " * 40)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = _llm_step(
        "writer",
        lambda: writer_chain.invoke({
            "topic": topic,
            "research": research_combined
        }),
    )
    _logger.info("writer step done chars=%s", len(str(state["report"])))

    print("\n Final Report\n", state["report"])

    # critic report

    print("\n" + "= " * 40)
    print("step 4 - critic is reviewing the report")
    print("= " * 40)

    state["feedback"] = _llm_step(
        "critic",
        lambda: critic_chain.invoke({
            "report": state["report"]
        }),
    )
    _logger.info("critic step done chars=%s", len(str(state["feedback"])))

    print("\n critic report \n", state["feedback"])
    _logger.info("pipeline complete topic=%r", topic)

    return state


if __name__ == "__main__":
    _ensure_utf8_stdout()
    setup_logging()
    try:
        require_env_keys()
    except MissingEnvironmentError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1) from e
    topic = input("\n Enter a research topic : ")
    try:
        run_research_pipeline(topic)
    except MissingEnvironmentError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1) from e
