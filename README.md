---
title: SupportOps AI Monitor
emoji: 🎫
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 8501
pinned: false
---

<div align="center">

# SupportOps AI Monitor

**An intelligent observability platform for enterprise support operations.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-ff4b4b?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-C9A84C?style=flat)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live_Demo-HuggingFace-ffd21e?style=flat&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/Archit-Konde/supportops-ai-monitor)
[![Documentation](https://img.shields.io/badge/Docs-GitHub_Pages-222?style=flat&logo=github&logoColor=white)](https://archit-konde.github.io/supportops-ai-monitor/)

</div>

---

## Overview

SupportOps AI Monitor simulates a production-grade support operations environment — from synthetic ticket generation to GPT-powered triage and real-time API health monitoring. The platform is designed to demonstrate how modern engineering teams can transform raw support data into structured, actionable intelligence.

The entire system runs in **simulation mode** with no API key required. Every chart, metric, and operational insight is generated from a realistic data pipeline that models enterprise-scale support workflows.

---

## Features

| Capability | Description |
|:-----------|:------------|
| **Ticket Generation** | Faker-powered synthetic tickets across five categories — API, billing, account, safety, and general |
| **Intelligent Triage** | GPT-4o-mini classification with automatic fallback to a Gaussian simulation engine |
| **Observability Dashboard** | Real-time KPIs, Plotly visualisations, and operational trend analysis |
| **API Health Monitoring** | Latency tracking, success rates, and error-type breakdowns |
| **PDF Reports** | Downloadable operational reports with light-theme styling and brand accents |
| **CSV / Excel Upload** | Ingest external ticket data directly through the sidebar |
| **Zero-Cost Demo** | Full functionality without an OpenAI API key — simulation mode is indistinguishable from live triage |

---

## Quick Start

### Prerequisites

- Python 3.11 or later
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Archit-Konde/supportops-ai-monitor.git
cd supportops-ai-monitor

# Install dependencies
pip install -r "Source Code/requirements.txt"

# Launch the dashboard
streamlit run "Source Code/src/app.py"
```

The dashboard opens at **http://localhost:8501**. Use the sidebar controls to generate tickets and observe the system in action.

### Docker

```bash
cd "Source Code"
docker build -t supportops-ai-monitor .
docker run -p 8501:8501 supportops-ai-monitor
```

---

## Architecture

```
Source Code/
├── src/
│   ├── app.py                 # Streamlit dashboard — rendering and UI logic
│   ├── ai_triage.py           # GPT-4o-mini triage with simulation fallback
│   ├── database.py            # SQLite persistence layer
│   └── ticket_generator.py    # Faker-powered synthetic ticket engine
├── tests/                     # Pytest test suite
├── infrastructure/            # Deployment guides (HuggingFace Spaces)
├── .streamlit/                # Streamlit configuration
├── Dockerfile                 # Container deployment
└── requirements.txt           # Python dependencies
```

### Data Pipeline

```
ticket_generator  →  database  →  ai_triage  →  database  →  dashboard
      ↓                 ↓             ↓             ↓            ↓
 Generate dicts    INSERT rows    Classify &     UPDATE AI    Render with
 from templates    into SQLite    score tickets  fields       Plotly charts
```

### Simulation Engine

When no `OPENAI_API_KEY` is set, the triage module activates a simulation engine that models realistic API behaviour:

- **Latency** — Gaussian distribution (μ = 820ms, σ = 200ms, clamped 200–2000ms)
- **Error rate** — 10% failure rate across `rate_limit`, `server_error`, and `timeout`
- **Classification** — Random assignment from five valid categories and three sentiment levels

The simulation produces observability data that is statistically indistinguishable from real API calls, making the full dashboard demonstrable at zero cost.

> For a detailed technical deep-dive, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Tech Stack

| Layer | Technology |
|:------|:-----------|
| **Frontend** | Streamlit, Plotly, Custom CSS |
| **Intelligence** | OpenAI GPT-4o-mini (with simulation fallback) |
| **Data** | Pandas, SQLite |
| **Testing** | Pytest |
| **Deployment** | Docker, HuggingFace Spaces |
| **Reporting** | xhtml2pdf, Kaleido |

---

## Repository Structure

```
supportops-ai-monitor/
├── README.md                  # This file
├── LICENSE                    # MIT License
├── CITATION.cff               # Academic citation metadata
├── codemeta.json              # Machine-readable software metadata
├── .github/                   # GitHub workflows, templates, and policies
├── docs/                      # Documentation site and architecture reference
│   ├── index.html             # GitHub Pages landing page
│   ├── ARCHITECTURE.md        # Technical deep-dive
│   └── sample-tickets.csv     # Example CSV for upload feature
└── Source Code/               # Application source, tests, and deployment
    ├── src/                   # Python source modules
    ├── tests/                 # Test suite
    ├── infrastructure/        # Deployment documentation
    ├── Dockerfile             # Container configuration
    └── requirements.txt       # Python dependencies
```

---

## Testing

```bash
cd "Source Code"
pytest
```

The test suite covers all three business logic modules — ticket generation, database operations, and AI triage — with deterministic assertions that work in both simulation and live modes.

---

## Deployment

The application is deployed on **[HuggingFace Spaces](https://huggingface.co/spaces/Archit-Konde/supportops-ai-monitor)** using the Docker SDK. For deployment instructions, see **[infrastructure/huggingface.md](Source%20Code/infrastructure/huggingface.md)**.

---

## Citation

If you use this project in academic or professional work, please cite:

```bibtex
@software{konde2026supportops,
  title     = {SupportOps AI Monitor},
  author    = {Konde, Archit},
  year      = {2026},
  url       = {https://github.com/Archit-Konde/supportops-ai-monitor},
  license   = {MIT}
}
```

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Designed & Developed by [Archit Konde](https://archit-konde.github.io/)**

*Transforming support data into operational intelligence.*

</div>
