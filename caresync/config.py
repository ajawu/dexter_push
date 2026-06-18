"""Typed runtime settings, read once from the environment at startup.

Secrets never live in code, and clinical bounds never live here -- those belong
in ``medical_fields.py``. This module carries only operational config: which
model to call, where to reach it, how hard the dispatcher retries, and where the
SQLite file lives.
"""

from __future__ import annotations

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Operational settings sourced from the environment (and ``.env`` if present)."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    llm_model: str | None = Field(
        default=None,
        description='PydanticAI model id, e.g. "anthropic:claude-sonnet-4-6".',
    )
    llm_base_url: str | None = Field(
        default=None,
        description="Optional OpenAI-compatible base URL for a local model.",
    )
    max_dispatch_attempts: int = Field(
        default=6,
        ge=1,
        description="Dispatcher retry budget before an outbox row is dead-lettered.",
    )
    db_path: str = Field(
        default="caresync.db",
        description="Path to the SQLite database file.",
    )

    def api_key_for(self, provider: str) -> str | None:
        """Return the ``<PROVIDER>_API_KEY`` env var for a provider name, if set."""
        return os.environ.get(f"{provider.upper()}_API_KEY")


def load_settings() -> Settings:
    """Load settings from the environment. The single entry point for config."""
    return Settings()
