# Deploying to HuggingFace Spaces

HuggingFace Spaces runs Streamlit natively and persists a `/data` directory between restarts — this solves the SQLite ephemeral filesystem problem without any database migration.

---

## Steps

### 1. Create a HF Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Set **SDK** to `Streamlit`
3. Set visibility to `Public`
4. Name it `supportops-ai-monitor`

### 2. Set the DB_PATH environment variable

In your Space settings → **Variables and secrets**, add:

```
DB_PATH = /data/supportops.db
```

This tells the app to write the SQLite database to HF's persisted `/data` directory instead of the ephemeral container filesystem. The `/data` directory survives restarts and new deploys.

Optionally, also add:

```
OPENAI_API_KEY = sk-...
```

(If absent, the app runs in simulation mode — fully functional with no cost.)

### 3. Add the HF README frontmatter

HuggingFace requires a YAML block at the top of the repo's `README.md` to configure the Space. Since our GitHub `README.md` is already formatted for GitHub, create the Space as an **empty repo** on HF and add this frontmatter to the HF copy only.

The frontmatter for the HF Space `README.md` should be:

```yaml
---
title: SupportOps AI Monitor
emoji: 🎫
colorFrom: yellow
colorTo: gray
sdk: streamlit
sdk_version: "1.32.0"
app_file: app.py
pinned: false
license: mit
short_description: Enterprise AI support ops dashboard — ticket triage, API health monitoring
---
```

### 4. Push the code to the HF Space

```bash
# Add the HF Space as a second remote
git remote add hf https://huggingface.co/spaces/YOUR_HF_USERNAME/supportops-ai-monitor

# Push main branch
git push hf main
```

Replace `YOUR_HF_USERNAME` with your HuggingFace username.

HuggingFace will detect `requirements.txt` and `app.py` automatically — no Dockerfile needed (though one is present and will be used if detected).

### 5. Update the GitHub repo About section

Once the Space is live, update the GitHub homepage URL from the portfolio root to the Space URL:

```bash
gh repo edit Archit-Konde/supportops-ai-monitor \
  --homepage "https://huggingface.co/spaces/YOUR_HF_USERNAME/supportops-ai-monitor"
```

---

## What Changes in the Code

The only code change required is already committed — `database.py` now reads `DB_PATH` from the environment:

```python
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "db", "supportops.db"),
)
```

Local development still uses `db/supportops.db` (no env var set). HF Spaces uses `/data/supportops.db` (env var set in Space secrets). No other changes needed.

---

## Verification

After deploying:
1. Open the Space URL — the dashboard should load
2. Use the sidebar to generate 10 tickets and triage them
3. Restart the Space (Settings → Factory reboot) — tickets should persist after restart
4. Confirm `DB_PATH` is set correctly in Space logs if the DB appears empty after restart
