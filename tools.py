from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from rich import print
from dotenv import load_dotenv

from runtime import call_with_retries, get_logger

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
_logger = get_logger()


@tool
def web_search(query: str) -> str:
    """Search the web for recent & reliable information on a topic. Returns Titles, URLs, & Snippets."""
    try:
        results = call_with_retries(
            lambda: tavily.search(query=query, max_results=5),
            attempts=3,
            base_delay=1.0,
            logger=_logger,
        )
    except Exception as e:
        _logger.error("web_search failed for query=%r: %s", query, e)
        return f"WEB_SEARCH_FAILED: could not reach the search API. Error: {str(e)}"

    hits = results.get("results") or []
    if not hits:
        _logger.warning("web_search returned no results for query=%r", query)
        return "WEB_SEARCH_EMPTY: no results found for this query."

    out = []
    for r in hits:
        title = r.get("title") or "(no title)"
        url = r.get("url") or ""
        snippet = (r.get("content") or "")[:300]
        out.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n")

    _logger.info("web_search ok query=%r hits=%s", query, len(hits))
    return "\n----\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading"""
    try:
        resp = call_with_retries(
            lambda: requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"}),
            attempts=2,
            base_delay=0.5,
            logger=_logger,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)[:3000]
        _logger.info("scrape_url ok url=%s chars=%s", url, len(text))
        return text
    except Exception as e:
        _logger.error("scrape_url failed url=%s: %s", url, e)
        return f"Could not scrape URL: {str(e)}"
