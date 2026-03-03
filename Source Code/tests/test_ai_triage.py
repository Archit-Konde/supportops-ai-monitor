"""
Tests for ai_triage.py — simulation mode output structure, error distribution,
sentiment mapping, and integration with the database layer.
"""

import database as db
import ticket_generator as tg
import ai_triage


def _make_ticket(**overrides):
    """Generate a ticket with optional field overrides."""
    ticket = tg.generate_ticket()
    ticket.update(overrides)
    return ticket


class TestSimulateTriage:
    """Tests for _simulate_triage() — the simulation fallback."""

    def test_success_returns_result_and_log(self, monkeypatch):
        """Force success (random > 0.10) and verify output structure."""
        monkeypatch.setattr("random.random", lambda: 0.5)
        ticket = _make_ticket(category="api", priority="critical")
        result, log = ai_triage._simulate_triage(ticket)

        assert result is not None
        assert "category" in result
        assert "sentiment" in result
        assert "summary" in result

        assert log["status_code"] == 200
        assert log["success"] == 1
        assert log["error_type"] is None
        assert log["ticket_id"] == ticket["ticket_id"]

    def test_success_preserves_category(self, monkeypatch):
        """Simulation should use the generator's ground-truth category."""
        monkeypatch.setattr("random.random", lambda: 0.5)
        ticket = _make_ticket(category="billing")
        result, _ = ai_triage._simulate_triage(ticket)
        assert result["category"] == "billing"

    def test_sentiment_maps_from_priority(self, monkeypatch):
        """Sentiment is derived from priority in simulation mode."""
        monkeypatch.setattr("random.random", lambda: 0.5)

        critical_ticket = _make_ticket(priority="critical")
        result, _ = ai_triage._simulate_triage(critical_ticket)
        assert result["sentiment"] == "negative"

        low_ticket = _make_ticket(priority="low")
        result, _ = ai_triage._simulate_triage(low_ticket)
        assert result["sentiment"] == "positive"

        medium_ticket = _make_ticket(priority="medium")
        result, _ = ai_triage._simulate_triage(medium_ticket)
        assert result["sentiment"] == "neutral"

    def test_summary_contains_subject(self, monkeypatch):
        monkeypatch.setattr("random.random", lambda: 0.5)
        ticket = _make_ticket(subject="API returning 500 errors")
        result, _ = ai_triage._simulate_triage(ticket)
        assert "api returning 500 errors" in result["summary"].lower()

    def test_rate_limit_error(self, monkeypatch):
        """random < 0.04 triggers a rate_limit error."""
        monkeypatch.setattr("random.random", lambda: 0.02)
        ticket = _make_ticket()
        result, log = ai_triage._simulate_triage(ticket)

        assert result is None
        assert log["status_code"] == 429
        assert log["success"] == 0
        assert log["error_type"] == "rate_limit"

    def test_server_error(self, monkeypatch):
        """0.04 <= random < 0.07 triggers a server_error."""
        monkeypatch.setattr("random.random", lambda: 0.05)
        ticket = _make_ticket()
        result, log = ai_triage._simulate_triage(ticket)

        assert result is None
        assert log["status_code"] == 500
        assert log["error_type"] == "server_error"

    def test_timeout_error(self, monkeypatch):
        """0.07 <= random < 0.10 triggers a timeout."""
        monkeypatch.setattr("random.random", lambda: 0.08)
        ticket = _make_ticket()
        result, log = ai_triage._simulate_triage(ticket)

        assert result is None
        assert log["status_code"] == 408
        assert log["error_type"] == "timeout"

    def test_latency_is_positive(self, monkeypatch):
        monkeypatch.setattr("random.random", lambda: 0.5)
        ticket = _make_ticket()
        _, log = ai_triage._simulate_triage(ticket)
        assert log["latency_ms"] > 0


class TestTriageTicketIntegration:
    """
    Tests for triage_ticket() — the main entry point.
    Runs in simulation mode (no OPENAI_API_KEY set) and verifies
    DB writes (api_health_logs + ticket AI fields).
    """

    def test_success_updates_db(self, monkeypatch):
        """On success, ticket AI fields and api_health_logs should be written."""
        monkeypatch.setattr("random.random", lambda: 0.5)

        ticket = _make_ticket(category="safety", priority="high")
        db.insert_ticket(ticket)

        result = ai_triage.triage_ticket(ticket)
        assert result is not None

        # Check ticket was updated in DB
        rows = db.get_all_tickets()
        updated = next(r for r in rows if r["ticket_id"] == ticket["ticket_id"])
        assert updated["category"] == "safety"
        assert updated["sentiment"] == "negative"  # high → negative
        assert updated["ai_summary"] is not None

        # Check API log was written
        logs = db.get_api_logs()
        assert len(logs) == 1
        assert logs[0]["success"] == 1

    def test_failure_still_logs(self, monkeypatch):
        """On API failure, an error log should still be written but ticket not updated."""
        monkeypatch.setattr("random.random", lambda: 0.02)  # rate_limit

        ticket = _make_ticket()
        db.insert_ticket(ticket)

        result = ai_triage.triage_ticket(ticket)
        assert result is None

        # API log should exist
        logs = db.get_api_logs()
        assert len(logs) == 1
        assert logs[0]["success"] == 0
        assert logs[0]["error_type"] == "rate_limit"

        # Ticket AI fields should remain null
        rows = db.get_all_tickets()
        updated = next(r for r in rows if r["ticket_id"] == ticket["ticket_id"])
        assert updated["ai_summary"] is None


class TestTriageBatch:
    """Tests for triage_batch()."""

    def test_batch_returns_stats(self, monkeypatch):
        monkeypatch.setattr("random.random", lambda: 0.5)  # always succeed

        tickets = [_make_ticket() for _ in range(5)]
        for t in tickets:
            db.insert_ticket(t)

        stats = ai_triage.triage_batch(tickets)
        assert stats["total"] == 5
        assert stats["success"] == 5
        assert stats["failed"] == 0

    def test_batch_with_callback(self, monkeypatch):
        monkeypatch.setattr("random.random", lambda: 0.5)

        tickets = [_make_ticket() for _ in range(3)]
        for t in tickets:
            db.insert_ticket(t)

        progress = []
        ai_triage.triage_batch(tickets, progress_callback=lambda i, n: progress.append((i, n)))
        assert progress == [(1, 3), (2, 3), (3, 3)]
