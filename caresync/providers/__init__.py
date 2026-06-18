"""Committed per-provider Pydantic schemas, one module per provider.

Each schema is drafted once by the onboarding CLI from a provider's OpenAPI doc,
then hand-reviewed and committed. Nothing here reads a spec at runtime; the
committed module is the authority the pipeline uses.

``get_provider`` is the one lookup the pipeline goes through: a name resolves to
both schemas a provider needs -- the unbounded twin extraction fills, and the
bounded model the carer-facing validation enforces.
"""

from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel

from caresync.providers.pflegedoc import PflegeDocEntry, PflegeDocEntryRaw


class Provider(NamedTuple):
    raw: type[BaseModel]  # unbounded extraction schema (LLM output_type)
    bounded: type[BaseModel]  # validated pipeline schema (carer confirms)


_PROVIDERS = {"pflegedoc": Provider(PflegeDocEntryRaw, PflegeDocEntry)}


def get_provider(name: str) -> Provider:
    try:
        return _PROVIDERS[name]
    except KeyError:
        known = ", ".join(_PROVIDERS)
        raise ValueError(f"unknown provider {name!r}; known: {known}") from None
