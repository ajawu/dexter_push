# CareSync dev tasks. Run `just` to list.
python := ".venv/bin/python"

default:
    @just --list

# Capture one transcript: extract, repair/confirm, enqueue. e.g. `just capture pflegedoc transcripts/partial.txt`
capture provider transcript:
    {{python}} -m caresync.cli {{provider}} {{transcript}}

# Start the flaky mock provider (FastAPI) on http://127.0.0.1:8000
serve:
    {{python}} -m uvicorn mock_provider.main:app --host 127.0.0.1 --port 8000

# Create the outbox table in the configured SQLite DB (applies storage.py's DDL)
init-db:
    {{python}} -c "import sqlite3; from caresync.config import load_settings; from caresync.storage import _DDL; p = load_settings().db_path; c = sqlite3.connect(p); c.executescript(_DDL); c.commit(); c.close(); print('outbox ready at', p)"
