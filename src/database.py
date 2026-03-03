"""
database.py
Handles all SQLite operations for SupportOps AI Monitor.
Tables: tickets, api_health_logs
"""

import sqlite3
import os
from datetime import datetime, timezone

# HuggingFace Spaces persists /data between restarts — set DB_PATH=/data/supportops.db
# in the HF Space secrets/env vars to enable persistence.
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "db", "supportops.db"),
)


def get_connection():
    """Return a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like row access
    return conn


def init_db():
    """Create tables and indexes if they don't exist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # --- Tickets table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id   TEXT UNIQUE NOT NULL,
                created_at  TEXT NOT NULL,
                customer    TEXT NOT NULL,
                subject     TEXT NOT NULL,
                body        TEXT NOT NULL,
                priority    TEXT NOT NULL,       -- low / medium / high / critical
                status      TEXT DEFAULT 'open', -- open / in_progress / resolved
                category    TEXT,               -- AI-assigned: billing / api / account / safety / other
                sentiment   TEXT,               -- AI-assigned: positive / neutral / negative
                ai_summary  TEXT,               -- AI-generated one-line summary
                resolved_at TEXT
            )
        """)

        # --- API health log table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_health_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT NOT NULL,
                endpoint      TEXT NOT NULL,
                status_code   INTEGER NOT NULL,
                latency_ms    REAL NOT NULL,
                success       INTEGER NOT NULL,  -- 1 = success, 0 = failure
                error_type    TEXT,              -- null / rate_limit / timeout / server_error
                ticket_id     TEXT              -- associated ticket if applicable
            )
        """)

        # --- Indexes ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_success ON api_health_logs(success)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_health_logs(timestamp)")

        conn.commit()
    finally:
        conn.close()


# ── Ticket queries ──────────────────────────────────────────────────────────

def insert_ticket(ticket: dict):
    """Insert a ticket, ignoring duplicates by ticket_id."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO tickets
                (ticket_id, created_at, customer, subject, body, priority, status)
            VALUES
                (:ticket_id, :created_at, :customer, :subject, :body, :priority, :status)
        """, ticket)
        conn.commit()
    finally:
        conn.close()


def update_ticket_ai_fields(ticket_id: str, category: str, sentiment: str, ai_summary: str):
    """Update AI-assigned fields after triage."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE tickets
            SET category = ?, sentiment = ?, ai_summary = ?
            WHERE ticket_id = ?
        """, (category, sentiment, ai_summary, ticket_id))
        conn.commit()
    finally:
        conn.close()


def resolve_ticket(ticket_id: str):
    """Mark a ticket as resolved with current timestamp."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE tickets
            SET status = 'resolved', resolved_at = ?
            WHERE ticket_id = ?
        """, (datetime.now(timezone.utc).isoformat(), ticket_id))
        conn.commit()
    finally:
        conn.close()


def get_all_tickets():
    """Return all tickets ordered by creation date descending."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tickets ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_tickets_by_status(status: str):
    """Return tickets filtered by status."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC", (status,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_ticket_stats():
    """Return aggregate stats used by the dashboard."""
    conn = get_connection()
    try:
        stats = {}

        stats["total"] = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        stats["open"] = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'").fetchone()[0]
        stats["resolved"] = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'resolved'").fetchone()[0]

        # Category breakdown
        rows = conn.execute("""
            SELECT category, COUNT(*) as count
            FROM tickets
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """).fetchall()
        stats["by_category"] = {r["category"]: r["count"] for r in rows}

        # Priority breakdown
        rows = conn.execute("""
            SELECT priority, COUNT(*) as count
            FROM tickets
            GROUP BY priority
        """).fetchall()
        stats["by_priority"] = {r["priority"]: r["count"] for r in rows}

        # Sentiment breakdown
        rows = conn.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM tickets
            WHERE sentiment IS NOT NULL
            GROUP BY sentiment
        """).fetchall()
        stats["by_sentiment"] = {r["sentiment"]: r["count"] for r in rows}

        return stats
    finally:
        conn.close()


# ── API health log queries ──────────────────────────────────────────────────

def insert_api_log(log: dict):
    """Insert an API health log entry."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO api_health_logs
                (timestamp, endpoint, status_code, latency_ms, success, error_type, ticket_id)
            VALUES
                (:timestamp, :endpoint, :status_code, :latency_ms, :success, :error_type, :ticket_id)
        """, log)
        conn.commit()
    finally:
        conn.close()


def get_api_logs(limit: int = 200):
    """Return recent API health logs."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM api_health_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_all_data():
    """Delete all tickets and API health logs. Returns counts of deleted rows."""
    conn = get_connection()
    try:
        tickets_deleted = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        logs_deleted = conn.execute(
            "SELECT COUNT(*) FROM api_health_logs"
        ).fetchone()[0]
        conn.execute("DELETE FROM tickets")
        conn.execute("DELETE FROM api_health_logs")
        conn.commit()
        return {"tickets": tickets_deleted, "logs": logs_deleted}
    finally:
        conn.close()


def get_api_health_stats():
    """Return aggregate API health stats."""
    conn = get_connection()
    try:
        stats = {}

        total = conn.execute("SELECT COUNT(*) FROM api_health_logs").fetchone()[0]
        success = conn.execute("SELECT COUNT(*) FROM api_health_logs WHERE success = 1").fetchone()[0]
        stats["total_calls"] = total
        stats["success_rate"] = round((success / total * 100), 1) if total > 0 else 0

        avg_latency = conn.execute(
            "SELECT AVG(latency_ms) FROM api_health_logs WHERE success = 1"
        ).fetchone()[0]
        stats["avg_latency_ms"] = round(avg_latency, 1) if avg_latency else 0

        # Error type breakdown
        rows = conn.execute("""
            SELECT error_type, COUNT(*) as count
            FROM api_health_logs
            WHERE success = 0 AND error_type IS NOT NULL
            GROUP BY error_type
            ORDER BY count DESC
        """).fetchall()
        stats["errors_by_type"] = {r["error_type"]: r["count"] for r in rows}

        return stats
    finally:
        conn.close()
