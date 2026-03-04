# Contributing Guidelines

Thank you for your interest in contributing to **SupportOps AI Monitor**. This project is maintained as a stable portfolio piece and professional reference. We welcome contributions that align with the platform's architectural philosophy and operational scope.

---

## Contribution Scope

To maintain the project's technical integrity and focused design, contributions are categorized as follows:

### Accepted Contributions
- **Bug Fixes**: Addressing simulation inaccuracies, database edge cases, or UI rendering issues.
- **Documentation**: Enhancing the README, technical documentation, or inline code commentary.
- **Analytics**: Introducing new visualization panels or operational metrics that utilize the existing SQLite schema.
- **Reliability**: Improving test suite coverage and deterministic logic verification.

### Out of Scope
- **Architectural Modification**: Replacing the core SQLite persistence layer or the modular four-stage pipeline.
- **Dependencies**: Introducing heavy third-party frameworks or build systems that deviate from the lightweight Python/Streamlit stack.
- **Major Refactors**: Large-scale rewrites that alter the established design language or project structure.

---

## Development Workflow

### 1. Environment Setup

Clone the repository and prepare your local environment:

```bash
git clone https://github.com/Archit-Konde/supportops-ai-monitor.git
cd supportops-ai-monitor
python -m venv venv
# Activate venv (OS specific)
pip install -r "Source Code/requirements.txt"
```

### 2. Verification
Before implementing changes, verify that the current baseline is stable:

```bash
# Set PYTHONPATH to 'Source Code/src' if needed
pytest "Source Code/tests/" -v
```
All tests must pass in the default simulation environment.

### 3. Standards and Style
All code contributions must adhere to the following standards:

- **Naming**: Use clear, descriptive, and consistent variable names.
- **Code Style**: Maximum line length of **120 characters**.
- **Persistence**: Database operations must follow the established `try/finally conn.close()` pattern in `src/database.py`.
- **Simulation**: Ensure all new features support the built-in **simulation mode** for zero-cost demonstration.

### 4. Quality Control
Execute these checks locally before submitting a pull request:

```bash
# Syntax and Logical Error Check
flake8 "Source Code/src/" "Source Code/tests/" --count --select=E9,F63,F7,F82 --show-source --statistics

# Full Test Suite
pytest "Source Code/tests/" -v --tb=short
```

---

## Submission Process

1.  **Fork** the repository and create a feature branch.
2.  **Commit** with clear, descriptive messages.
3.  **Open a Pull Request** detailing the problem solved and the technical approach taken.

---

## Code of Conduct

Maintain a professional, constructive, and direct communication style. Technical clarity and respectful collaboration are prioritized.

---

*By contributing to this project, you agree that your work will be licensed under the [MIT License](LICENSE).*
