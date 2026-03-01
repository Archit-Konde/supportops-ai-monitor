# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (optional — simulation mode works without a key)
cp .env.example .env  # then add OPENAI_API_KEY

# Run the dashboard
streamlit run app.py
# Opens at http://localhost:8501

# Generate standalone ticket JSON (no Streamlit)
python ticket_generator.py
```

## Architecture

Four modules with a one-way data pipeline:

```
ticket_generator.py  →  database.py  →  ai_triage.py  →  database.py
       ↓                     ↓                ↓
  generates dicts       INSERT tickets    UPDATE ai fields
                                           + INSERT api logs
```

**`app.py`** — Streamlit dashboard only. No business logic. Calls the other three modules, renders charts with Plotly, and lets users generate/triage tickets via sidebar controls.

**`ticket_generator.py`** — Builds ticket dicts from `TICKET_TEMPLATES` (5 categories: api, billing, account, safety, other). Fills placeholders with Faker data. The `category` field on the generated ticket is ground truth but is intentionally overwritten by AI triage.

**`database.py`** — All SQLite operations. DB file lives at `db/supportops.db` (created automatically). Two tables: `tickets` and `api_health_logs`. All connections are short-lived (open → execute → close per function). Uses `INSERT OR IGNORE` on tickets to prevent duplicates on re-runs.

**`ai_triage.py`** — Calls OpenAI `gpt-4o-mini` to classify category, sentiment, and produce a one-line summary. Logs every API call (latency, status code, error type) to `api_health_logs`. Falls back to `_simulate_triage()` when `OPENAI_API_KEY` is absent — simulation uses Gaussian latency (mean 820ms, σ 200ms) and a 10% error rate to generate realistic observability data without API costs.

## Key Conventions

- **Simulation mode is the default** — the app is fully demonstrable with no API key. Don't assume a key is present when debugging triage issues.
- **`category` is set twice** — once by the generator (as ground truth) and again by `ai_triage.update_ticket_ai_fields()`. The DB value always reflects the AI-assigned category after triage runs.
- **No migrations** — schema is defined in `database.init_db()` with `CREATE TABLE IF NOT EXISTS`. Schema changes require dropping and recreating `db/supportops.db`.
- **No tests** — this is a portfolio project with no test suite.
- **No build step** — plain Python, no packaging or compilation.

## Environment

Only one env variable: `OPENAI_API_KEY` in `.env`. The `dotenv` package loads it automatically at module import time in `ai_triage.py`.
