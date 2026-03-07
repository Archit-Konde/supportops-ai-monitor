"""
ai_triage.py
Calls the OpenAI API to categorize, sentiment-analyse, and summarize support tickets.
Logs every API call to the api_health_logs table for monitoring.
"""

import os
import time
import json
import random
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

import database as db


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_log(ticket_id: str, latency_ms: float, status_code: int = 200,
              success: int = 1, error_type: str | None = None) -> dict:
    """Build an API health log entry. Centralises the 7-key dict shape."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": "/v1/chat/completions",
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
        "success": success,
        "error_type": error_type,
        "ticket_id": ticket_id,
    }


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert support ticket triage specialist for an enterprise AI platform.
Analyze the support ticket and respond ONLY with a valid JSON object — no markdown, no explanation.

JSON format:
{
  "category": "<one of: api | billing | account | safety | other>",
  "sentiment": "<one of: positive | neutral | negative>",
  "summary": "<one sentence, max 20 words, describing the core issue>"
}"""


def _simulate_triage(ticket: dict) -> tuple[dict, dict]:
    """
    Fallback simulation when no API key is available.
    Returns (triage_result, log_entry) — mimics real API behavior including occasional errors.
    """
    # Simulate realistic latency
    latency = random.gauss(mu=820, sigma=200)
    latency = max(200, latency)
    time.sleep(latency / 1000)  # simulate network wait

    # Simulate occasional failures (10% error rate for realism)
    # Thresholds: 0–4% rate_limit, 4–7% server_error, 7–10% timeout
    rand = random.random()
    if rand < 0.04:
        return None, _make_log(ticket["ticket_id"], latency, 429, 0, "rate_limit")
    elif rand < 0.07:
        return None, _make_log(ticket["ticket_id"], latency, 500, 0, "server_error")
    elif rand < 0.10:
        return None, _make_log(ticket["ticket_id"], latency + 5000, 408, 0, "timeout")

    # Use category from generator as ground truth for simulation
    category = ticket.get("category", "other")
    
    # Derive sentiment from priority
    sentiment_map = {
        "critical": "negative",
        "high": "negative",
        "medium": "neutral",
        "low": "positive",
    }
    sentiment = sentiment_map.get(ticket.get("priority", "medium"), "neutral")

    # Generate a realistic summary from the subject
    subject = ticket.get("subject", "Support request")
    summary = f"Customer reports: {subject[:60].lower().rstrip('.')}."

    result = {
        "category": category,
        "sentiment": sentiment,
        "summary": summary,
    }
    return result, _make_log(ticket["ticket_id"], latency)


def triage_ticket(ticket: dict) -> dict | None:
    """
    Triage a single ticket via OpenAI API (or simulation).
    Logs the API call and updates the DB.
    Returns the triage result dict or None on failure.
    """
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        result, log = _simulate_triage(ticket)
        db.insert_api_log(log)
        if result:
            db.update_ticket_ai_fields(
                ticket["ticket_id"],
                result["category"],
                result["sentiment"],
                result["summary"],
            )
        return result

    # ── Real OpenAI call ──────────────────────────────────────────────────
    user_message = f"Subject: {ticket['subject']}\n\nBody:\n{ticket['body']}"
    start = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=120,
            temperature=0,
            timeout=30,
        )
        latency_ms = (time.time() - start) * 1000
        raw = response.choices[0].message.content.strip()

        # Parse JSON response — guard against malformed/non-JSON replies
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            db.insert_api_log(
                _make_log(ticket["ticket_id"], latency_ms, 200, 0, "parse_error")
            )
            return None

        # Validate fields
        valid_categories = {"api", "billing", "account", "safety", "other"}
        valid_sentiments = {"positive", "neutral", "negative"}
        if result.get("category") not in valid_categories:
            result["category"] = "other"
        if result.get("sentiment") not in valid_sentiments:
            result["sentiment"] = "neutral"

        db.insert_api_log(_make_log(ticket["ticket_id"], latency_ms))
        db.update_ticket_ai_fields(
            ticket["ticket_id"],
            result["category"],
            result["sentiment"],
            result["summary"],
        )
        return result

    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        error_str = str(e).lower()

        if "rate_limit" in error_str or "429" in error_str:
            error_type = "rate_limit"
            status_code = 429
        elif "timeout" in error_str or "408" in error_str:
            error_type = "timeout"
            status_code = 408
        elif "500" in error_str:
            error_type = "server_error"
            status_code = 500
        else:
            error_type = "unknown"
            status_code = 0

        db.insert_api_log(
            _make_log(ticket["ticket_id"], latency_ms, status_code, 0, error_type)
        )
        return None


def triage_batch(tickets: list[dict], progress_callback=None) -> dict:
    """
    Triage a list of tickets. Returns summary stats.
    progress_callback(i, total) is called after each ticket if provided.
    """
    success, failed = 0, 0
    for i, ticket in enumerate(tickets):
        result = triage_ticket(ticket)
        if result:
            success += 1
        else:
            failed += 1
        if progress_callback:
            progress_callback(i + 1, len(tickets))

    return {"success": success, "failed": failed, "total": len(tickets)}
