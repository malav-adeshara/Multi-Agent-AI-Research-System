import sys
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain, build_reader_prompt


def _ensure_utf8_stdout() -> None:
    """Avoid Windows cp1252 crashes when printing research text with Unicode."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def run_research_pipeline(topic: str) -> dict:
    state = {}

    # Search Agent Working
    print("\n" + "= " * 40)
    print("step 1 - search agent is working ...")
    print("= " * 40)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })

    state["search_results"] = search_result["messages"][-1].content or ""

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
        print("\nscraped_content\n", state["scraped_content"])
    else:
        reader_agent = build_reader_agent()
        reader_result = reader_agent.invoke({
            "messages": [("user", build_reader_prompt(topic, search_results))]
        })
        state["scraped_content"] = reader_result["messages"][-1].content or ""
        print("\nscraped_content\n", state["scraped_content"])

    # step 3 - writer chain
    print("\n" + "= " * 40)
    print("step 3 - Writer is drafting the report ...")
    print("= " * 40)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    print("\n Final Report\n", state["report"])

    # critic report

    print("\n" + "= " * 40)
    print("step 4 - critic is reviewing the report")
    print("= " * 40)

    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\n critic report \n", state["feedback"])

    return state


if __name__ == "__main__":
    _ensure_utf8_stdout()
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)
