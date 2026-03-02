# SupportOps AI Monitor

[![CI](https://github.com/Archit-Konde/supportops-ai-monitor/actions/workflows/lint-test.yml/badge.svg)](https://github.com/Archit-Konde/supportops-ai-monitor/actions/workflows/lint-test.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776ab.svg?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-C9A84C.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Demo-HuggingFace_Spaces-FFD21E.svg?logo=huggingface&logoColor=black)](https://architechs-supportops-ai-monitor.hf.space)

Simulates enterprise AI support operations — ticket generation, GPT-4o-mini triage, API health monitoring, and an observability dashboard. Runs entirely in simulation mode with no API key required.

<!-- TODO: Replace with actual screenshot → docs/assets/screenshots/dashboard.png -->

---

## Features

- **Realistic ticket generation** — 5 categories (API, billing, account, safety, other) with Faker-powered enterprise data
- **AI triage** — classifies category, analyses sentiment, and produces a one-line summary via `gpt-4o-mini`
- **API health monitoring** — logs every API call with latency, HTTP status code, and error type
- **Observability dashboard** — Streamlit + Plotly charts for ticket volume, priority distribution, sentiment trends, and API health
- **Simulation mode** — full demo at zero cost, no API key needed
- **CSV/Excel upload** — bring your own ticket data, auto-triaged by the AI pipeline

---

## Quick Start

```bash
git clone https://github.com/Archit-Konde/supportops-ai-monitor.git
cd supportops-ai-monitor
pip install -r requirements.txt
streamlit run src/app.py
```

Opens at `http://localhost:8501`. Use the sidebar to generate and triage tickets.

> **Simulation mode** is the default. Add `OPENAI_API_KEY` to `.env` for real triage. See [`.env.example`](.env.example).

---

## How It Works

```
ticket_generator.py  →  database.py  →  ai_triage.py  →  app.py (dashboard)
```

Tickets are generated from Faker-powered templates, stored in SQLite, triaged by GPT-4o-mini (or simulation), and visualised in real time. Every API call is logged with latency, status code, and error type for observability.

For architecture diagrams, database schema, and simulation details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Tech Stack

Python 3.11+ · Streamlit · OpenAI (`gpt-4o-mini`) · SQLite · Plotly · Pandas · Faker · pytest · Docker

---

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines and local CI checks.

---

## License

[MIT](LICENSE)

---

## Author

**Archit Konde**
[Portfolio](https://archit-konde.github.io) · [GitHub](https://github.com/Archit-Konde) · [LinkedIn](https://linkedin.com/in/architkonde)
