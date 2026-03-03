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
  [![Live Demo](https://img.shields.io/badge/Live_Demo-HuggingFace-ffd21e?style=flat&logo=huggingface&logoColor=black)](https://architechs-supportops-ai-monitor.hf.space/)
  [![Developed by Archit Konde](https://img.shields.io/badge/Developed%20by-Archit%20Konde-blue.svg)](https://github.com/Archit-Konde)

  A monitoring platform for support operations that combines synthetic ticket generation, AI-powered triage, and API health tracking into a single dashboard.

  **[Source Code](Source%20Code/)** &nbsp;·&nbsp; **[Architecture](docs/ARCHITECTURE.md)** &nbsp;·&nbsp; **[Live Demo](https://architechs-supportops-ai-monitor.hf.space/)** &nbsp;·&nbsp; **[Documentation](https://archit-konde.github.io/supportops-ai-monitor/)**

</div>

---

<div align="center">

[Overview](#overview) &nbsp;·&nbsp; [Features](#features) &nbsp;·&nbsp; [Structure](#project-structure) &nbsp;·&nbsp; [Quick Start](#quick-start) &nbsp;·&nbsp; [Usage Guidelines](#usage-guidelines) &nbsp;·&nbsp; [License](#license) &nbsp;·&nbsp; [Citation](#citation)

</div>

---

<!-- OVERVIEW -->
<a name="overview"></a>
## Overview

**SupportOps AI Monitor** is a tool built to help teams understand the lifecycle of support tickets. It simulates a production environment by generating synthetic tickets, triaging them using GPT-4o-mini (or a simulation engine), and tracking the performance of these API calls in real-time.

The project demonstrates how to structure support data and turn it into clear metrics for operational review. It uses a multi-stage pipeline: tickets are created, classified, stored in a local SQLite database, and visualized on a dashboard.

> [!IMPORTANT]
> ### Simulation Mode
> You do not need an OpenAI API key to use this. The tool has a built-in simulation engine that models realistic triage results including latency, errors, and classification. This allows you to test the dashboard's features immediately without any setup cost.

> [!NOTE]
> ### System Modelling
> This dashboard models real-world patterns such as Gaussian latency (averaging 820ms) and common API failure types. The goal is to provide a realistic look at how a support system performs under different conditions.

---

<!-- FEATURES -->
<a name="features"></a>
## Features

| Feature | Description |
|---------|-------------|
| **Ticket Generation** | Creates synthetic tickets using **Faker** across categories like API, billing, account, and safety. |
| **AI Triage** | Uses **GPT-4o-mini** to classify tickets. It automatically falls back to a simulation engine if no API key is set. |
| **Operational Dashboard** | Displays KPIs and charts for ticket volume, priority, and sentiment using **Streamlit** and **Plotly**. |
| **Health Monitoring** | Logs API latency, success rates, and HTTP status codes to monitor system performance. |
| **Reporting** | Generates downloadable PDF reports with data tables and charts using **xhtml2pdf**. |
| **Data Import** | Allows you to upload your own CSV or Excel files for custom triage and analysis. |
| **Developer Tools** | Includes a terminal-themed UI, a back-to-top button for long pages, and a hidden developer menu. |

### Tech Stack
- **Language**: Python 3.11+
- **Frontend**: **Streamlit** (UI) and **Plotly** (Charts)
- **AI**: **OpenAI GPT-4o-mini** (with simulation fallback)
- **Storage**: **SQLite** (Local Database) and **Pandas** (Data Processing)
- **Testing**: **Pytest** (Automated logic tests)
- **Deployment**: **Docker** and **HuggingFace Spaces**

---

<!-- STRUCTURE -->
<a name="project-structure"></a>
## Project Structure

```python
supportops-ai-monitor/
│
├── docs/                                # Documentation files
│   ├── ARCHITECTURE.md                  # Tech deep-dive
│   ├── sample-tickets.csv               # Example data for testing
│   └── assets/                          # Images and icons
│
├── Source Code/                         # Application source code
│   ├── src/                             # Core Python modules
│   │   ├── app.py                       # Dashboard and UI logic
│   │   ├── ai_triage.py                 # Triage and simulation logic
│   │   ├── database.py                  # Database operations
│   │   └── ticket_generator.py          # Synthetic data logic
│   ├── tests/                           # Automated test suite
│   ├── infrastructure/                  # Deployment guides
│   ├── .streamlit/                      # UI configuration
│   ├── Dockerfile                       # Container setup
│   └── requirements.txt                 # Dependencies
│
├── CITATION.cff                         # Citation info
├── LICENSE                              # MIT License
└── README.md                            # This file
```

---

<!-- QUICK START -->
<a name="quick-start"></a>
## Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **Git**
- **Docker** (Optional, for containers)

### 2. Setup

#### Step 1: Clone the Repository
```bash
git clone https://github.com/Archit-Konde/supportops-ai-monitor.git
cd supportops-ai-monitor
```

#### Step 2: Virtual Environment
**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r "Source Code/requirements.txt"
```

### 3. Running the App

#### A. Local Dashboard
```bash
streamlit run "Source Code/src/app.py"
```
The app will be available at **http://localhost:8501**.

> [!TIP]
> ### Online Demo
> You can try the live version of the dashboard here without installing anything:  
> **[Open Live Demo on HuggingFace](https://architechs-supportops-ai-monitor.hf.space/)**

#### B. Using Docker
```bash
cd "Source Code"
docker build -t supportops-ai-monitor .
docker run -p 8501:8501 supportops-ai-monitor
```

#### C. Running Tests
```bash
cd "Source Code"
pytest
```

---

<!-- USAGE GUIDELINES -->
<a name="usage-guidelines"></a>
## Usage Guidelines

**For Engineers**

Use this project as a reference for building dashboards, data simulations, or AI pipelines. The code is structured to be readable and easy to follow.

**For Educators**

This project can be used as a case study for software engineering, data visualization, or AI integration. Please attribute the work if you use it in your curriculum.

**For Researchers**

The simulation logic and data pipeline provide a starting point for studying synthetic data and system performance modeling.

---

<!-- LICENSE -->
<a name="license"></a>
## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more information.

Copyright © 2026 Archit Konde

---

<!-- CITATION -->
<a name="citation"></a>
## Citation

If you use this project in your work, please cite it:

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

  🎫 **[Live Demo](https://architechs-supportops-ai-monitor.hf.space/)** &nbsp;·&nbsp; 📖 **[Documentation](https://archit-konde.github.io/supportops-ai-monitor/)** &nbsp;·&nbsp; 🏗️ **[Architecture](docs/ARCHITECTURE.md)**

  ---

  #### Designed & Developed by [Archit Konde](https://archit-konde.github.io/)

  *Transforming support data into operational intelligence.*

</div>
