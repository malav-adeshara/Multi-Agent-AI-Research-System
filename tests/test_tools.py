from unittest.mock import MagicMock, patch

import pytest

import tools


def test_web_search_happy_path_formats_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "title": "Title One",
                "url": "https://example.com/one",
                "content": "x" * 500,
            },
            {
                "title": "Title Two",
                "url": "https://example.com/two",
                "content": "short snippet",
            },
        ]
    }
    with patch.object(tools, "tavily", mock_client):
        out = tools.web_search.func("quantum computing")

    assert "Title: Title One" in out
    assert "URL: https://example.com/one" in out
    assert "Snippet: " in out
    assert "----" in out
    mock_client.search.assert_called_once_with(query="quantum computing", max_results=5)


def test_web_search_empty_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}
    with patch.object(tools, "tavily", mock_client):
        out = tools.web_search.func("nothing here")

    assert out.startswith("WEB_SEARCH_EMPTY")


def test_web_search_api_failure_returns_error_string():
    mock_client = MagicMock()
    mock_client.search.side_effect = RuntimeError("network down")
    with patch.object(tools, "tavily", mock_client):
        out = tools.web_search.func("anything")

    assert out.startswith("WEB_SEARCH_FAILED")
    assert "network down" in out


def test_web_search_handles_missing_fields():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"content": "only content"},
            {},
        ]
    }
    with patch.object(tools, "tavily", mock_client):
        out = tools.web_search.func("q")

    assert "(no title)" in out
    assert "URL: \n" in out or "URL:" in out


def test_scrape_url_happy_path_extracts_text():
    html = """
    <html><head><script>var x=1;</script><style>.a{}</style></head>
    <body><nav>nav</nav><p>Hello World</p><footer>foot</footer></body></html>
    """
    mock_resp = MagicMock()
    mock_resp.text = html
    with patch.object(tools.requests, "get", return_value=mock_resp) as mock_get:
        out = tools.scrape_url.func("https://example.com")

    assert "Hello World" in out
    assert "var x=1" not in out
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["timeout"] == 8


def test_scrape_url_failure_returns_message_not_raise():
    with patch.object(tools.requests, "get", side_effect=RuntimeError("net down")):
        out = tools.scrape_url.func("https://example.com")

    assert out.startswith("Could not scrape URL")
    assert "net down" in out


@pytest.mark.parametrize(
    "search_text",
    [
        "",
        "WEB_SEARCH_FAILED: boom",
        "WEB_SEARCH_EMPTY: none",
    ],
)
def test_pipeline_reader_skip_conditions_use_search_prefixes(search_text):
    """Mirror pipeline skip logic for empty/failed search outputs."""
    skip = (
        not search_text.strip()
        or search_text.startswith("WEB_SEARCH_FAILED")
        or search_text.startswith("WEB_SEARCH_EMPTY")
    )
    assert skip is True
