"""
Shared fixtures for the SupportOps AI Monitor test suite.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """
    Redirect database.DB_PATH to a temporary directory for every test.
    Ensures no test pollutes the real DB and tests are fully isolated.
    """
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("database.DB_PATH", db_path)

    import database as db
    db.init_db()

    return db_path


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Remove time.sleep in triage to keep tests fast."""
    monkeypatch.setattr("time.sleep", lambda _: None)
