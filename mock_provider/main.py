"""A deliberately unreliable stand-in for an external care-documentation provider.

One POST endpoint that accepts a PflegeDoc entry and fails most of the time -- roughly
one request in three is accepted, the rest return a random 5xx. It exists so the
delivery path (retries, idempotency) has something hostile to talk to.
"""

from __future__ import annotations

import random

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class PflegeDocEntry(BaseModel):
    """The provider's own contract -- intentionally a separate copy from caresync's."""

    bewohner_name: str
    blutdruck_systolisch: int | None = None
    blutdruck_diastolisch: int | None = None
    koerpertemperatur: float | None = None
    spo2: int | None = None
    puls: int | None = None
    notiz: str | None = None


app = FastAPI(title="Mock PflegeDoc provider")


@app.post("/entries")
def create_entry(entry: PflegeDocEntry) -> dict[str, str]:
    if random.random() < 1 / 3:
        return {"status": "accepted", "bewohner_name": entry.bewohner_name}
    raise HTTPException(
        status_code=random.choice([500, 502, 503, 504]),
        detail="upstream provider error (simulated)",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
