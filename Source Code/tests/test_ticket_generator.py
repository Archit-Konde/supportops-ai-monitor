"""
Tests for ticket_generator.py — schema validation, field presence, batch generation.
"""

import ticket_generator as tg


REQUIRED_FIELDS = {
    "ticket_id", "created_at", "customer", "subject",
    "body", "priority", "status", "category",
}

VALID_CATEGORIES = {"api", "billing", "account", "safety", "other"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_STATUSES = {"open", "in_progress", "resolved"}


class TestGenerateTicket:
    """Tests for generate_ticket()."""

    def test_returns_dict(self):
        ticket = tg.generate_ticket()
        assert isinstance(ticket, dict)

    def test_has_all_required_fields(self):
        ticket = tg.generate_ticket()
        assert REQUIRED_FIELDS.issubset(ticket.keys()), (
            f"Missing fields: {REQUIRED_FIELDS - ticket.keys()}"
        )

    def test_ticket_id_format(self):
        ticket = tg.generate_ticket()
        assert ticket["ticket_id"].startswith("TKT-")
        assert len(ticket["ticket_id"]) == 12  # TKT- + 8 hex chars

    def test_category_is_valid(self):
        ticket = tg.generate_ticket()
        assert ticket["category"] in VALID_CATEGORIES

    def test_priority_is_valid(self):
        ticket = tg.generate_ticket()
        assert ticket["priority"] in VALID_PRIORITIES

    def test_status_is_valid(self):
        ticket = tg.generate_ticket()
        assert ticket["status"] in VALID_STATUSES

    def test_created_at_is_iso_format(self):
        from datetime import datetime
        ticket = tg.generate_ticket()
        # Should not raise ValueError
        datetime.fromisoformat(ticket["created_at"])

    def test_customer_is_nonempty_string(self):
        ticket = tg.generate_ticket()
        assert isinstance(ticket["customer"], str) and len(ticket["customer"]) > 0

    def test_subject_and_body_are_nonempty(self):
        ticket = tg.generate_ticket()
        assert len(ticket["subject"]) > 0
        assert len(ticket["body"]) > 0


class TestGenerateBatch:
    """Tests for generate_batch()."""

    def test_returns_correct_count(self):
        tickets = tg.generate_batch(n=10)
        assert len(tickets) == 10

    def test_batch_of_zero(self):
        tickets = tg.generate_batch(n=0)
        assert tickets == []

    def test_ticket_ids_are_unique(self):
        tickets = tg.generate_batch(n=50)
        ids = [t["ticket_id"] for t in tickets]
        assert len(ids) == len(set(ids)), "Duplicate ticket IDs found"

    def test_all_categories_represented_in_large_batch(self):
        """500 tickets across 5 categories: P(missing any one) < 2e-44. Deterministically safe."""
        tickets = tg.generate_batch(n=500)
        categories = {t["category"] for t in tickets}
        assert categories == VALID_CATEGORIES


class TestTemplates:
    """Tests for TICKET_TEMPLATES structure."""

    def test_all_categories_have_templates(self):
        assert set(tg.TICKET_TEMPLATES.keys()) == VALID_CATEGORIES

    def test_templates_have_required_keys(self):
        for category, templates in tg.TICKET_TEMPLATES.items():
            for i, tmpl in enumerate(templates):
                assert "subject" in tmpl, f"Template {i} in '{category}' missing 'subject'"
                assert "body" in tmpl, f"Template {i} in '{category}' missing 'body'"
                assert "priority" in tmpl, f"Template {i} in '{category}' missing 'priority'"

    def test_template_priorities_are_valid(self):
        for category, templates in tg.TICKET_TEMPLATES.items():
            for tmpl in templates:
                assert tmpl["priority"] in VALID_PRIORITIES, (
                    f"Invalid priority '{tmpl['priority']}' in category '{category}'"
                )


class TestSaveLoad:
    """Tests for JSON save/load round-trip."""

    def test_round_trip(self, tmp_path):
        tickets = tg.generate_batch(n=5)
        filepath = str(tmp_path / "tickets.json")
        tg.save_tickets_to_json(tickets, filepath)
        loaded = tg.load_tickets_from_json(filepath)
        assert len(loaded) == 5
        assert loaded[0]["ticket_id"] == tickets[0]["ticket_id"]
