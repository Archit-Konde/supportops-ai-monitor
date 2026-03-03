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

  <a name="readme-top"></a>
  # SupportOps AI Monitor

  [![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)
  ![Status](https://img.shields.io/badge/Status-Active-success)
  [![Technology](https://img.shields.io/badge/Technology-Python%20%7C%20Streamlit%20%7C%20Plotly-blueviolet)](https://github.com/Archit-Konde/supportops-ai-monitor)
  [![Developed by Archit Konde](https://img.shields.io/badge/Developed%20by-Archit%20Konde-blue.svg)](https://github.com/Archit-Konde)

  An intelligent observability platform for enterprise support operations — synthesizing ticket data, GPT-powered triage intelligence, and real-time API health monitoring into a unified operational dashboard.

  **[Source Code](Source%20Code/)** &nbsp;·&nbsp; **[Architecture](docs/ARCHITECTURE.md)** &nbsp;·&nbsp; **[Live Demo](https://huggingface.co/spaces/Archit-Konde/supportops-ai-monitor)** &nbsp;·&nbsp; **[Documentation](https://archit-konde.github.io/supportops-ai-monitor/)**

</div>

---

<div align="center">

    [Overview](#overview) &nbsp;·&nbsp; [Features](#features) &nbsp;·&nbsp; [Structure](#project-structure) &nbsp;·&nbsp; [Quick Start](#quick-start) &nbsp;·&nbsp; [Usage Guidelines](#usage-guidelines) &nbsp;·&nbsp; [License](#license) &nbsp;·&nbsp; [Citation](#citation)

</div>

---



<!-- OVERVIEW -->
<a name="overview"></a>
## Overview

**SupportOps AI Monitor** is an enterprise-grade observability platform that models the complete lifecycle of a modern support operations pipeline — from synthetic ticket generation and intelligent triage to real-time API health monitoring and operational analytics. The system is engineered to demonstrate how engineering teams can transform raw support data into structured, actionable intelligence.

The platform implements a multi-stage data pipeline where tickets are generated, classified by GPT-4o-mini (or a statistically faithful simulation engine), persisted in SQLite, and rendered through an interactive Streamlit dashboard with Plotly visualisations.

> [!IMPORTANT]
> ### No API Key Needed
> The dashboard works out of the box. A built-in simulation engine generates realistic triage results — latency curves, error distributions, and classification outputs — so you can explore every feature without provisioning an OpenAI key.

> [!NOTE]
> ### Beyond a Demo
> This isn't a mock-up. The simulation models Gaussian latency (μ 820ms), a 10% error rate across three failure types, and multi-category sentiment classification — mirroring how a production triage pipeline actually behaves.


---

<!-- FEATURES -->
<a name="features"></a>
## Features

| Feature | Description |
|---------|-------------|
| **Ticket Generation Engine** | Generates realistic synthetic tickets from **Faker-powered templates** across five operational categories — API, billing, account, safety, and general. |
| **Intelligent Triage System** | Classifies tickets using **OpenAI GPT-4o-mini** with automatic fallback to a **Gaussian simulation engine** when no API key is present. |
| **Observability Dashboard** | Real-time KPIs, interactive **Plotly visualisations**, and operational trend analysis rendered through a polished **Streamlit** interface. |
| **API Health Monitor** | Tracks latency distributions, success rates, HTTP status codes, and error-type breakdowns across the triage pipeline. |
| **PDF Report Generation** | Downloadable operational reports with light-theme styling, brand accents, and structured data tables via **xhtml2pdf**. |
| **CSV / Excel Upload** | Ingest external ticket data directly through the sidebar for custom analysis and triage. |
| **Zero-Cost Demo Mode** | Full functionality without an OpenAI API key — simulation mode is indistinguishable from live triage in the dashboard. |

> [!NOTE]
> ### Interactive Design
> The dashboard features a premium, terminal-inspired dark theme with yellow accents, smooth animations, a back-to-top button, and a hidden developer easter egg. The visual language is designed for clarity and operational focus.

### Tech Stack
- **Language**: Python 3.11+
- **Frontend**: **Streamlit** & **Plotly** (Interactive Charts & KPIs)
- **Intelligence**: **OpenAI GPT-4o-mini** (with simulation fallback)
- **Data Layer**: **Pandas** & **SQLite** (Persistence & Analytics)
- **Testing**: **Pytest** (46-test suite covering all business logic modules)
- **Deployment**: **Docker** & **HuggingFace Spaces**
- **Reporting**: **xhtml2pdf** & **Kaleido** (PDF Generation)

---

<!-- STRUCTURE -->
<a name="project-structure"></a>
## Project Structure

```python
supportops-ai-monitor/
│
├── docs/                                # Documentation & GitHub Pages
│   ├── index.html                       # Terminal-style landing page
│   ├── 404.html                         # Custom error page
│   ├── ARCHITECTURE.md                  # Technical deep-dive & diagrams
│   ├── sample-tickets.csv               # Example CSV for upload feature
│   └── assets/                          # Visual assets
│
├── Source Code/                          # Application Source Layer
│   ├── src/                             # Python source modules
│   │   ├── app.py                       # Streamlit dashboard — UI & rendering
│   │   ├── ai_triage.py                 # GPT-4o-mini triage & simulation engine
│   │   ├── database.py                  # SQLite persistence layer
│   │   └── ticket_generator.py          # Faker-powered ticket generator
│   ├── tests/                           # Pytest test suite
│   │   ├── conftest.py                  # Shared fixtures
│   │   ├── test_ai_triage.py            # Triage module tests
│   │   ├── test_database.py             # Database module tests
│   │   └── test_ticket_generator.py     # Generator module tests
│   ├── infrastructure/                  # Deployment documentation
│   │   └── huggingface.md               # HuggingFace Spaces guide
│   ├── .streamlit/                      # Streamlit configuration
│   │   └── config.toml                  # Theme & server settings
│   ├── Dockerfile                       # Container deployment
│   ├── .dockerignore                    # Docker build exclusions
│   ├── pytest.ini                       # Test discovery config
│   └── requirements.txt                 # Python dependencies
│
├── .github/                             # GitHub workflows & templates
├── .gitattributes                       # Line ending normalisation
├── .gitignore                           # Version control exclusions
├── CITATION.cff                         # Academic citation metadata
├── codemeta.json                        # Machine-readable software metadata
├── LICENSE                              # MIT License
└── README.md                            # Project entrance (this file)
```

---

<!-- QUICK START -->
<a name="quick-start"></a>
## Quick Start

### 1. Prerequisites
- **Python 3.11+**: Required for runtime execution. [Download Python](https://www.python.org/downloads/)
- **Git**: For version control and cloning. [Download Git](https://git-scm.com/downloads)
- **Docker**: (Optional) For containerised deployment. [Download Docker](https://www.docker.com/products/docker-desktop/)

### 2. Installation & Setup

#### Step 1: Clone the Repository
Open your terminal and clone the repository:
```bash
git clone https://github.com/Archit-Konde/supportops-ai-monitor.git
cd supportops-ai-monitor
```

#### Step 2: Configure Virtual Environment
Prepare an isolated environment to manage dependencies:

**Windows (Command Prompt / PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux (Terminal):**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Core Dependencies
Install the required libraries from the source directory:
```bash
pip install -r "Source Code/requirements.txt"
```

### 3. Execution

#### A. Interactive Dashboard
Launch the Streamlit-based observability dashboard:
```bash
streamlit run "Source Code/src/app.py"
```

**Dashboard Access**: Once initialised, navigate to **http://localhost:8501**. Use the sidebar controls to generate tickets, adjust batch sizes, and observe the triage pipeline in real time.

> [!TIP]
> ### Live Operational Demo
>
> Experience the full **SupportOps AI Monitor** dashboard directly in your browser through the working **HuggingFace Space**. This deployment features the complete simulation engine, PDF report generation, and all operational analytics — demonstrating the platform at zero cost.
>
> **[Launch SupportOps AI Monitor on HuggingFace](https://huggingface.co/spaces/Archit-Konde/supportops-ai-monitor)**

#### B. Docker Deployment
Build and run the application in a container:
```bash
cd "Source Code"
docker build -t supportops-ai-monitor .
docker run -p 8501:8501 supportops-ai-monitor
```

#### C. Test Suite
Run the full pytest suite to validate all business logic modules:
```bash
cd "Source Code"
pytest
```

> [!NOTE]
> ### OpenAI API Key (Optional)
> To enable live GPT-4o-mini triage instead of simulation mode, create a `.env` file in the project root:
> ```
> OPENAI_API_KEY=your_openai_api_key_here
> ```
> The dashboard will automatically detect the key and switch to live mode.

---

<!-- USAGE GUIDELINES -->
<a name="usage-guidelines"></a>
## Usage Guidelines

This repository is openly shared to support learning and knowledge exchange across the engineering community.

**For Engineers**
Use this project as a reference implementation for building **observability dashboards**, **simulation engines**, and **AI-powered triage systems**. The source code is structured for clarity and annotated for self-paced exploration.

**For Educators**
This project may serve as a practical case study for courses in **Software Engineering**, **Data Visualisation**, **AI Integration**, and **DevOps**. Attribution is appreciated when utilising content.

**For Researchers**
The architecture and simulation methodology may provide insights into **synthetic data generation**, **API health modelling**, and **operational intelligence design patterns**.

---

<!-- LICENSE -->
<a name="license"></a>
## License

This repository is made available under the **MIT License**. See the [LICENSE](LICENSE) file for complete terms.

> [!NOTE]
> **Summary**: You are free to share and adapt this content for any purpose, even commercially, as long as you provide appropriate attribution to the original author.

Copyright © 2026 Archit Konde

---

<!-- CITATION -->
<a name="citation"></a>
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

<!-- FOOTER -->
<div align="center">

  [↑ Back to Top](#readme-top)

  [Overview](#overview) &nbsp;·&nbsp; [Features](#features) &nbsp;·&nbsp; [Structure](#project-structure) &nbsp;·&nbsp; [Quick Start](#quick-start) &nbsp;·&nbsp; [Usage Guidelines](#usage-guidelines) &nbsp;·&nbsp; [License](#license) &nbsp;·&nbsp; [Citation](#citation)

  <br>

  🎫 **[Live Demo](https://huggingface.co/spaces/Archit-Konde/supportops-ai-monitor)** &nbsp;·&nbsp; 📖 **[Documentation](https://archit-konde.github.io/supportops-ai-monitor/)** &nbsp;·&nbsp; 🏗️ **[Architecture](docs/ARCHITECTURE.md)**

  ---

  #### Designed & Developed by [Archit Konde](https://archit-konde.github.io/)

  *Transforming support data into operational intelligence.*

</div>
