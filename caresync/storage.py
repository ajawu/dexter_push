"""The only durable state in CareSync: the ``outbox`` table.

A confirmed, carer-ratified entry is written here. The row, stamped with ``confirmed_by``, is the audit record. A
stable ``dedupe_key`` with a ``UNIQUE`` constraint makes re-confirming the identical
entry a no-op instead of a duplicate.
"""

from __future__ import annotations

import hashlib
import sqlite3
import unicodedata

from pydantic import BaseModel

from caresync.config import load_settings

SETTINGS = load_settings()


_DDL = """
CREATE TABLE IF NOT EXISTS outbox (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dedupe_key   TEXT NOT NULL UNIQUE,
    provider     TEXT NOT NULL,
    payload      TEXT NOT NULL,
    confirmed_by TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def enqueue(provider: str, entry: BaseModel, confirmed_by: str) -> int | None:
    """
        Write one confirmed entry to the outbox. Return its row id, or ``None`` if present.
    """
    payload = entry.model_dump_json()
    normalized_payload = unicodedata.normalize("NFC", payload).casefold()
    key = hashlib.sha256(f"{provider}\0{normalized_payload}".encode()).hexdigest()

    conn = sqlite3.connect(SETTINGS.db_path)
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO outbox (dedupe_key, provider, payload, confirmed_by) "
            "VALUES (?, ?, ?, ?)",
            (key, provider, payload, confirmed_by),
        )
        conn.commit()
        return cur.lastrowid if cur.rowcount == 1 else None
    finally:
        conn.close()
