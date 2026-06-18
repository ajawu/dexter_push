"""outbox is the only table; enqueue round-trips and dedupes.

Offline -- ``enqueue`` self-connects to ``db_path`` from settings, so each test points
``DB_PATH`` at a temp file and inspects it with a direct connection.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from caresync.providers.pflegedoc import PflegeDocEntry
from caresync.storage import enqueue


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> sqlite3.Connection:
    """Point enqueue at a temp DB and hand back a read connection to the same file."""
    path = tmp_path / "outbox.db"
    monkeypatch.setenv("DB_PATH", str(path))
    enqueue("pflegedoc", _entry(), "seed")  # creates the file + table
    return sqlite3.connect(path)


def _entry(**overrides: object) -> PflegeDocEntry:
    return PflegeDocEntry(bewohner_name="Frau Schneider", puls=72, **overrides)


def test_only_the_outbox_table_exists(db: sqlite3.Connection) -> None:
    names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert names == {"outbox"}


def test_enqueue_round_trips(db: sqlite3.Connection) -> None:
    row_id = enqueue("pflegedoc", _entry(spo2=97), "tester")
    assert row_id is not None

    provider, payload, confirmed_by = db.execute(
        "SELECT provider, payload, confirmed_by FROM outbox WHERE id = ?", (row_id,)
    ).fetchone()
    assert provider == "pflegedoc"
    assert confirmed_by == "tester"
    assert json.loads(payload)["spo2"] == 97


def test_enqueue_dedupes_identical_entries(db: sqlite3.Connection) -> None:
    # The fixture already seeded _entry(); a second identical write is ignored.
    assert enqueue("pflegedoc", _entry(), "other") is None
    assert enqueue("pflegedoc", _entry(spo2=97), "tester") is not None  # differs -> inserts

    (count,) = db.execute("SELECT count(*) FROM outbox").fetchone()
    assert count == 2
