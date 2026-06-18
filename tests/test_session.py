"""capture: skip nulls, fill nulls, repair impossible values, confirm, abandon.

Offline -- a scripted carer stands in for the human, no model and no real stdin.
"""

from __future__ import annotations

from collections.abc import Callable

from caresync.providers.pflegedoc import PflegeDocEntry, PflegeDocEntryRaw
from caresync.session import Abandoned, capture

_YES: Callable[[object], bool] = lambda _entry: True
_NO: Callable[[object], bool] = lambda _entry: False


def _scripted(answers: list[str | None]) -> Callable[[str], str | None]:
    """An ``ask`` that returns canned answers in order, ignoring the prompt."""
    it = iter(answers)
    return lambda _prompt: next(it)


def _draft(**overrides: object) -> PflegeDocEntryRaw:
    return PflegeDocEntryRaw(bewohner_name="Herr Bauer", **overrides)


def test_null_skipped_stays_null() -> None:
    result = capture(_draft(), PflegeDocEntry, _scripted([None] * 6), _YES)
    assert isinstance(result, PflegeDocEntry)
    assert result.puls is None and result.spo2 is None


def test_null_filled_and_invalid_reasked() -> None:
    # Field order: systolic, diastolic, temperature, spo2, puls, notiz.
    answers = [None, None, None, "150", "97", "72", None]  # spo2 150 rejected, then 97
    result = capture(_draft(), PflegeDocEntry, _scripted(answers), _YES)
    assert isinstance(result, PflegeDocEntry)
    assert result.spo2 == 97
    assert result.puls == 72


def test_impossible_value_repaired() -> None:
    # Field order reaches the impossible temperature after the two null BP fields.
    answers = [None, None, "37.0", None, None, None]  # systolic, diastolic, temp, ...
    result = capture(_draft(koerpertemperatur=8.0), PflegeDocEntry, _scripted(answers), _YES)
    assert isinstance(result, PflegeDocEntry)
    assert result.koerpertemperatur == 37.0


def test_impossible_value_skipped_is_abandoned() -> None:
    # Skip the two null BP fields, then skip the impossible temperature -> abandoned.
    answers = [None, None, None]  # systolic, diastolic, temp (skipped)
    result = capture(_draft(koerpertemperatur=8.0), PflegeDocEntry, _scripted(answers), _YES)
    assert result == Abandoned("koerpertemperatur: 8.0 out of range, not corrected")


def test_declined_confirmation_is_abandoned() -> None:
    result = capture(_draft(), PflegeDocEntry, _scripted([None] * 6), _NO)
    assert result == Abandoned("carer declined at confirmation")
