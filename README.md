# Multi Agent AI Research System

Overview
- A small research/workbench for experimenting with multi-agent AI patterns and pipelines.

Repository structure
- `agents.py` - agent implementations and orchestration helpers.
- `app.py` - application entrypoint / demo runner.
- `pipeline.py` - pipeline definitions that wire agents together.
- `tools.py` - utility functions used across the project.
- `requirements.txt` - Python dependencies for the project.

Prerequisites
- Python 3.10 or later (3.12 recommended; `.venv` is tested on 3.12).
- Git to clone the repo.

Quickstart
1. Create and activate a virtual environment (recommended):

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

3. Provide environment variables (if any):
- Create a `.env` file in the project root for any secrets or configuration used by the code.

4. Run the app or experiments:

If the project uses Streamlit interfaces:

```bash
streamlit run app.py
```

Or run directly with Python (some scripts are CLI/demo oriented):

```bash
python app.py
```

Dependencies
- See `requirements.txt` for exact pins matching the working environment:

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

Development notes
- Keep secrets and API keys out of the repo; use `.env` or your environment.
- Use the provided `requirements.txt` to reproduce the environment. Freeze updates with `pip freeze > requirements.txt` when you intend to record changes.

Testing & linting
- This repository doesn't include tests by default. Consider adding `pytest` and running `pytest` for test discovery.

Contributing
- Fork the repo, create a feature branch, and open a pull request. Keep changes focused and include tests for new behavior.

License
- No license file present. Add a `LICENSE` file if you want to open-source this project and make the licensing explicit.

Contact
- If this is your personal workspace, add author and contact information here.
