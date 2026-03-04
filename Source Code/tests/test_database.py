"""
Tests for database.py — CRUD operations, stats aggregation, index creation.
All tests use an isolated temp DB via the conftest.py `isolated_db` fixture.
"""

import database as db
import ticket_generator as tg


def _make_ticket(**overrides):
    """Generate a ticket with optional field overrides."""
    ticket = tg.generate_ticket()
    ticket.update(overrides)
    return ticket


class TestInitDb:
    """Tests for init_db() schema creation."""

    def test_tables_exist(self):
        conn = db.get_connection()
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            names = {r["name"] for r in tables}
            assert "tickets" in names
            assert "api_health_logs" in names
        finally:
            conn.close()

    def test_indexes_exist(self):
        conn = db.get_connection()
        try:
            indexes = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ).fetchall()
            names = {r["name"] for r in indexes}
            expected = {
                "idx_tickets_status", "idx_tickets_priority",
                "idx_tickets_created_at", "idx_tickets_category",
                "idx_api_logs_success", "idx_api_logs_timestamp",
            }
            assert expected.issubset(names), f"Missing indexes: {expected - names}"
        finally:
            conn.close()

    def test_idempotent(self):
        """Calling init_db() twice should not raise."""
        db.init_db()
        db.init_db()


class TestInsertTicket:
    """Tests for insert_ticket()."""

    def test_insert_and_retrieve(self):
        ticket = _make_ticket()
        db.insert_ticket(ticket)
        all_tickets = db.get_all_tickets()
        assert len(all_tickets) == 1
        assert all_tickets[0]["ticket_id"] == ticket["ticket_id"]

    def test_duplicate_ignored(self):
        ticket = _make_ticket()
        db.insert_ticket(ticket)
        db.insert_ticket(ticket)  # same ticket_id
        assert len(db.get_all_tickets()) == 1

    def test_multiple_inserts(self):
        for _ in range(5):
            db.insert_ticket(_make_ticket())
        assert len(db.get_all_tickets()) == 5


class TestUpdateTicketAiFields:
    """Tests for update_ticket_ai_fields()."""

    def test_updates_category_sentiment_summary(self):
        ticket = _make_ticket()
        db.insert_ticket(ticket)
        db.update_ticket_ai_fields(
            ticket["ticket_id"], "billing", "negative", "Customer charged twice."
        )
        rows = db.get_all_tickets()
        assert rows[0]["category"] == "billing"
        assert rows[0]["sentiment"] == "negative"
        assert rows[0]["ai_summary"] == "Customer charged twice."


class TestResolveTicket:
    """Tests for resolve_ticket()."""

    def test_marks_resolved_with_timestamp(self):
        ticket = _make_ticket(status="open")
        db.insert_ticket(ticket)
        db.resolve_ticket(ticket["ticket_id"])
        rows = db.get_all_tickets()
        assert rows[0]["status"] == "resolved"
        assert rows[0]["resolved_at"] is not None


class TestGetTicketsByStatus:
    """Tests for get_tickets_by_status()."""

    def test_filters_by_status(self):
        db.insert_ticket(_make_ticket(status="open"))
        db.insert_ticket(_make_ticket(status="open"))
        db.insert_ticket(_make_ticket(status="resolved"))
        open_tickets = db.get_tickets_by_status("open")
        assert len(open_tickets) == 2
        assert all(t["status"] == "open" for t in open_tickets)


class TestGetTicketStats:
    """Tests for get_ticket_stats()."""

    def test_empty_db(self):
        stats = db.get_ticket_stats()
        assert stats["total"] == 0
        assert stats["open"] == 0
        assert stats["resolved"] == 0

    def test_counts_correct(self):
        db.insert_ticket(_make_ticket(status="open"))
        db.insert_ticket(_make_ticket(status="open"))
        db.insert_ticket(_make_ticket(status="resolved"))
        stats = db.get_ticket_stats()
        assert stats["total"] == 3
        assert stats["open"] == 2
        assert stats["resolved"] == 1

    def test_priority_breakdown(self):
        db.insert_ticket(_make_ticket(priority="critical"))
        db.insert_ticket(_make_ticket(priority="critical"))
        db.insert_ticket(_make_ticket(priority="low"))
        stats = db.get_ticket_stats()
        assert stats["by_priority"]["critical"] == 2
        assert stats["by_priority"]["low"] == 1


class TestApiLogs:
    """Tests for insert_api_log() and get_api_logs()."""

    def _sample_log(self, **overrides):
        log = {
            "timestamp": "2026-03-01T12:00:00",
            "endpoint": "/v1/chat/completions",
            "status_code": 200,
            "latency_ms": 850.0,
            "success": 1,
            "error_type": None,
            "ticket_id": "TKT-00000001",
        }
        log.update(overrides)
        return log

    def test_insert_and_retrieve(self):
        db.insert_api_log(self._sample_log())
        logs = db.get_api_logs()
        assert len(logs) == 1
        assert logs[0]["status_code"] == 200

    def test_limit(self):
        for i in range(10):
            db.insert_api_log(self._sample_log(ticket_id=f"TKT-{i:08d}"))
        logs = db.get_api_logs(limit=3)
        assert len(logs) == 3


class TestApiHealthStats:
    """Tests for get_api_health_stats()."""

    def _sample_log(self, **overrides):
        log = {
            "timestamp": "2026-03-01T12:00:00",
            "endpoint": "/v1/chat/completions",
            "status_code": 200,
            "latency_ms": 800.0,
            "success": 1,
            "error_type": None,
            "ticket_id": "TKT-00000001",
        }
        log.update(overrides)
        return log

    def test_empty_db(self):
        stats = db.get_api_health_stats()
        assert stats["total_calls"] == 0
        assert stats["success_rate"] == 0

    def test_success_rate(self):
        for _ in range(9):
            db.insert_api_log(self._sample_log())
        db.insert_api_log(self._sample_log(
            success=0, status_code=429, error_type="rate_limit"
        ))
        stats = db.get_api_health_stats()
        assert stats["total_calls"] == 10
        assert stats["success_rate"] == 90.0

    def test_error_type_breakdown(self):
        db.insert_api_log(self._sample_log(
            success=0, status_code=429, error_type="rate_limit"
        ))
        db.insert_api_log(self._sample_log(
            success=0, status_code=500, error_type="server_error"
        ))
        db.insert_api_log(self._sample_log(
            success=0, status_code=500, error_type="server_error"
        ))
        stats = db.get_api_health_stats()
        assert stats["errors_by_type"]["rate_limit"] == 1
        assert stats["errors_by_type"]["server_error"] == 2
