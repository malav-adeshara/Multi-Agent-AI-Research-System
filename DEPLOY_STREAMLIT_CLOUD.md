# Deploy ResearchMind on Streamlit Community Cloud (Free)

This guide deploys the multi-agent research app so **anyone with the public URL** can run Search → Reader → Writer → Critic from anywhere.

**Cost:** Free tier of [Streamlit Community Cloud](https://share.streamlit.io/).

---

## What you need before starting

| Item | Where to get it | Notes |
|---|---|---|
| GitHub repo | This project pushed to GitHub | `https://github.com/malav-adeshara/Multi-Agent-AI-Research-System` |
| Groq API key | [console.groq.com](https://console.groq.com/) → API Keys | Starts with `gsk_` |
| Tavily API key | [app.tavily.com](https://app.tavily.com/) → API Keys | Starts with `tvly_` |
| Streamlit account | [share.streamlit.io](https://share.streamlit.io/) / [streamlit.io](https://streamlit.io/) | Sign in with GitHub |

**Important:** Do **not** commit API keys to GitHub. `.env` is already gitignored. Keys go into Streamlit Cloud **Secrets** only.

---

## Step 0 — Confirm the repo is ready on GitHub

On `main` you should have at least:

- `app.py` (Streamlit entrypoint — this is the file Cloud will run)
- `requirements.txt` (UTF-8 pins — Cloud installs from this)
- `agents.py`, `tools.py`, `pipeline.py`, `runtime.py`
- `tests/` (not required for deploy, but good hygiene)
- `.gitignore` (must ignore `.env`)

Latest verified baseline in this repo:

```text
db88b4e Phase 5: env validation, retries, logging, README accuracy
```

If your local copy is behind:

```bash
git pull origin main
git push origin main
```

---

## Step 1 — Open Streamlit Community Cloud

1. Go to [https://share.streamlit.io/](https://share.streamlit.io/)
2. Sign in with the **same GitHub account** that owns the repo.
3. Click **Create app** (or **New app**).

---

## Step 2 — Connect the GitHub repository

On the deploy form, set:

| Field | Value |
|---|---|
| **Repository** | `malav-adeshara/Multi-Agent-AI-Research-System` |
| **Branch** | `main` |
| **Main file path** | `app.py` |
| **Python version** | **3.12** (recommended; matches local `.venv`) |

> Use `app.py`, **not** `pipeline.py`.  
> `pipeline.py` is the CLI runner; Cloud serves the Streamlit UI.

If the repo does not appear, install/authorize the Streamlit GitHub app for that account (Cloud prompts you on first deploy).

---

## Step 3 — Add secrets (API keys)

Streamlit Cloud does **not** use your local `.env` file. Keys must be added as app secrets.

1. Before or after first deploy, open **App settings** → **Secrets**  
   (from the app page: menu → *Settings* / *Advanced settings* → *Secrets*).
2. Paste **exactly** this TOML block (replace the values):

```toml
GROQ_API_KEY = "gsk_your_groq_key_here"
TAVILY_API_KEY = "tvly_your_tavily_key_here"
```

3. Save.

### How the code reads secrets

- Local: `.env` → `load_dotenv()` / `runtime.load_runtime_env()`
- Cloud: Streamlit **Secrets** (`st.secrets`) → injected into `os.environ` by `runtime.py` before agents/tools build clients

Both keys are required. Missing keys show a clear error in the UI instead of a silent crash.

---

## Step 4 — Deploy

1. Click **Deploy**.
2. Wait for the build to finish (first deploy installs `requirements.txt` — can take a few minutes).
3. When ready you get a public URL like:

```text
https://<app-name>-<hash>-share.streamlit.app/
```

or the older style:

```text
https://<app-name>.streamlit.app/
```

4. Open the URL — the ResearchMind UI should load.

---

## Step 5 — Verify the deployment works

In the browser:

1. Enter a topic (e.g. `AI coding assistants trends 2025`).
2. Click **⚡ Run Research Pipeline**.
3. Confirm step cards move: Search → Reader → Writer → Critic (**DONE**).
4. Expand raw search / scraped content if needed.
5. Confirm **Final Research Report** renders and **Download Report (.md)** works.
6. Confirm **Critic Feedback** shows a score (e.g. `Score: x/10`).
7. Intentionally test error UI: temporarily remove a secret → Run → you should see a **Missing required API key** error (restore secrets after).

Also confirm Cloud logs (app page → **Manage app** → logs) show lines like:

```text
[researchmind] pipeline start topic=...
[researchmind] web_search ok ...
[researchmind] reader step done ...
```

---

## Step 6 — Share with anyone

The Streamlit Community Cloud URL is **public by default** on the free tier.

- Share the link as-is.
- Anyone can open it and run the pipeline (subject to your Groq/Tavily rate limits and quotas).
- Free apps **sleep** after inactivity; first visit after sleep may take ~30–60s to wake.

### Privacy / cost notes

- Users’ research topics are sent to **Groq** (LLM) and **Tavily** (search).
- Scraping uses public HTTP requests from Streamlit’s servers.
- You pay nothing for hosting on the free tier, but **API usage is billed/limited by Groq and Tavily**.
- Prefer free/trial API tiers for demos; monitor usage dashboards.

---

## App settings checklist (Cloud UI)

| Setting | Recommended value |
|---|---|
| App URL / name | e.g. `researchmind` |
| GitHub repo | `malav-adeshara/Multi-Agent-AI-Research-System` |
| Branch | `main` |
| Main file path | `app.py` |
| Python version | `3.12` |
| Secrets | `GROQ_API_KEY`, `TAVILY_API_KEY` |
| Packages | none extra (pure Python; `requirements.txt` is enough) |

No `packages.txt` is required (no apt system packages).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Build fails on pip install | `requirements.txt` wrong/encoding | Ensure UTF-8 file with pins (see repo `requirements.txt`) |
| App loads but Run errors “Missing required API key” | Secrets not set / wrong names | App settings → Secrets → exact keys `GROQ_API_KEY`, `TAVILY_API_KEY` |
| `ModuleNotFoundError` | Main file path wrong or branch mismatch | Main file = `app.py`, branch = `main` |
| Search step shows `WEB_SEARCH_FAILED` | Bad Tavily key, quota, or network from Cloud | Verify key at tavily.com; check quota |
| LLM steps fail / 429 | Groq rate limit | Wait and retry; check Groq dashboard; consider another model later |
| Reader skipped | Search returned empty/failed | Fix Tavily key/network first |
| App sleeps / slow first open | Free tier cold start | Wait for wake; click Run again |
| Unicode crash locally (not Cloud) | Windows console | Use `python pipeline.py` (app already sets UTF-8) or Streamlit UI |

---

## Local deploy check (optional, before Cloud)

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`, run one topic, then push `main` and deploy to Cloud.

---

## Redeploy after code changes

1. `git add` / `git commit` / `git push origin main`
2. Streamlit Cloud auto-redeploys on push to the connected branch  
   (or use **Rerun** / **Restart app** in Cloud UI if needed)

Secrets persist in Cloud settings — you do **not** re-enter them on every deploy.

---

## Security reminders

- Never commit `.env` or paste keys into GitHub issues/READMEs.
- Rotate keys if a repo or secret is ever exposed.
- Streamlit secrets are encrypted at rest and only exposed to your app.
- If the app must be private, Streamlit Cloud free tier is still public URL; for true auth/private apps look at Streamlit paid / self-host / reverse proxy options later.

---

## Quick command reference

```bash
# Local
streamlit run app.py
python pipeline.py          # CLI only

# Tests (before push)
pytest
pytest --live               # optional live API smoke

# Git
git push origin main        # triggers Cloud redeploy
```

---

## Summary

1. Push this repo to GitHub (`main`, `app.py` entrypoint).  
2. Create app on [share.streamlit.io](https://share.streamlit.io/).  
3. Set **Main file path = `app.py`**, **Python 3.12**.  
4. Add **Secrets**: `GROQ_API_KEY` + `TAVILY_API_KEY`.  
5. Deploy → open public URL → run a topic → share the link.

That’s it — free hosting, public access, full multi-agent pipeline.
