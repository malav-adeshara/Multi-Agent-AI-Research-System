# Multi Agent AI Research System

Overview
- ResearchMind: a Streamlit + CLI multi-agent research pipeline (Search → Reader → Writer → Critic).
- LLM backend: Groq (`ChatGroq`, model `openai/gpt-oss-120b`).
- Web search: Tavily. Page scraping: requests + BeautifulSoup.

Repository structure
- `agents.py` — agent factories, reader prompt, writer/critic chains.
- `app.py` — Streamlit UI (`streamlit run app.py`).
- `pipeline.py` — CLI pipeline (`python pipeline.py`).
- `tools.py` — `web_search` + `scrape_url` LangChain tools.
- `runtime.py` — env validation, logging, retry/backoff helpers.
- `tests/` — pytest suite (mocked external APIs).
- `requirements.txt` — pinned dependencies (UTF-8).
- `pytest.ini` — pytest discovery + `live` marker.

Prerequisites
- Python 3.10 or later (3.12 recommended; `.venv` is tested on 3.12).
- Git to clone the repo.
- API keys for Groq and Tavily.

Quickstart
1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Provide environment variables in `.env` (project root):

```
GROQ_API_KEY=...
TAVILY_API_KEY=...
```

Missing keys are validated at startup (CLI) and on Run (UI) with a clear error.

4. Run:

```bash
# Streamlit UI (recommended)
streamlit run app.py

# CLI pipeline (interactive topic prompt)
python pipeline.py
```

Note: the CLI reconfigures stdout to UTF-8 so Windows consoles do not crash on Unicode research text.

Dependencies
- See `requirements.txt` for exact pins:

```
streamlit==1.57.0
langchain==1.3.1
langchain-core==1.4.0
langchain-groq==1.1.2
tavily-python==0.7.24
beautifulsoup4==4.14.3
requests==2.34.2
python-dotenv==1.2.2
rich==15.0.0
httpx==0.28.1
```

Required `.env` keys:
- `GROQ_API_KEY` — LLM backend (ChatGroq)
- `TAVILY_API_KEY` — web search tool

Reliability features
- Transient API errors (timeouts, connection resets, rate limits) are retried with exponential backoff in tools and pipeline LLM steps.
- Failed/empty web search skips the reader step instead of crashing.
- Streamlit shows per-step WAITING / RUNNING / DONE / FAILED cards and surfaces errors in an Issues panel.
- Optional file/console logging via the `researchmind` logger (`runtime.setup_logging`).

Development notes
- Keep secrets out of the repo; use `.env` or your environment.
- `requirements.txt` matches the working venv pins; re-freeze with `pip freeze > requirements.txt` when you intentionally change deps.

Testing & linting
- Unit/integration tests live in `tests/` (mocked Tavily/Groq — no network needed):

```bash
.venv\Scripts\activate   # Windows
pytest
```

- Optional live smoke (real APIs; needs `.env` keys + network):

```bash
pytest --live
```

- `pytest.ini` sets test discovery to `tests/`. Live tests are skipped unless you pass `--live`.
- Contributing: keep changes focused and include tests for new behavior.

License
- No license file present. Add a `LICENSE` file if you want to open-source this project and make the licensing explicit.

Contact
- If this is your personal workspace, add author and contact information here.
