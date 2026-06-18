"""One-shot CLI: a transcript file in, a confirmed provider entry out.

A thin terminal adapter over the capture core -- read a file, extract it, and hand the
draft to ``session.capture`` with a carer backed by stdin/stdout. The repair prompts
and the confirm step run on stderr; only the confirmed JSON goes to stdout.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

from caresync.config import load_settings
from caresync.extraction import Extractor
from caresync.providers import get_provider
from caresync.session import capture
from caresync.storage import enqueue


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: python -m caresync.cli <provider> <transcript-file>", file=sys.stderr)
        return 2

    try:
        provider = get_provider(args[0])
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    # Load and process transcript
    settings = load_settings()
    transcript = Path(args[1]).read_text(encoding="utf-8")
    entry = Extractor(settings).extract(transcript, provider.raw)
    result = capture(entry, provider.bounded)
    if isinstance(result, str):
        print(result, file=sys.stderr)
        return 1

    # Commit validated data
    confirmed_by = getpass.getuser()
    row_id = enqueue(args[0], result, confirmed_by)
    print(result.model_dump_json(indent=2))
    error = f"Already in outbox, confirmed by {confirmed_by}" if row_id is None else (f"Enqueued {row_id}, confirmed by {confirmed_by}")
    print(error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
