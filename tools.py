from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from rich import print
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web for recent & reliable information on a topic. Returns Titles, URLs, & Snippets."""
    try:
        results = tavily.search(query=query, max_results=5)
    except Exception as e:
        return f"WEB_SEARCH_FAILED: could not reach the search API. Error: {str(e)}"

    hits = results.get("results") or []
    if not hits:
        return "WEB_SEARCH_EMPTY: no results found for this query."

    out = []
    for r in hits:
        title = r.get("title") or "(no title)"
        url = r.get("url") or ""
        snippet = (r.get("content") or "")[:300]
        out.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n")

    return "\n----\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading"""
    try:
        resp = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0"
        })
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"