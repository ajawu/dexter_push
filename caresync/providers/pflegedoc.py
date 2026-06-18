from __future__ import annotations

from pydantic import BaseModel, Field

from caresync.providers.medical_fields import (
    BodyTemperature,
    DiastolicPressure,
    Pulse,
    Spo2,
    SystolicPressure,
)


class PflegeDocEntryRaw(BaseModel):
    """PflegeDoc's structural shape -- plain types, no clinical bounds.

    The extractor's ``output_type``. Impossible readings pass through it so the
    bounded validation in ``session.py`` can route them to the carer for repair.
    """
    bewohner_name: str = Field(..., title="Bewohnername")
    blutdruck_systolisch: int | None = Field(
        default=None, title="Blutdruck systolisch (mmHg)"
    )
    blutdruck_diastolisch: int | None = Field(
        default=None, title="Blutdruck diastolisch (mmHg)"
    )
    koerpertemperatur: float | None = Field(default=None, title="Körpertemperatur (°C)")
    spo2: int | None = Field(default=None, title="Sauerstoffsättigung (%)")
    puls: int | None = Field(default=None, title="Puls (Schläge/min)")
    notiz: str | None = Field(default=None, title="Notiz")


class PflegeDocEntry(PflegeDocEntryRaw):
    """The bounded overlay: vitals narrowed to their named physiological types.

    Validated only in ``session.py``. Each override re-states its ``title`` -- an
    override replaces the field's whole ``FieldInfo``, so omitting the title would
    drop the German label the repair loop shows the carer. ``bewohner_name`` and
    ``notiz`` are inherited from the base unchanged.
    """

    blutdruck_systolisch: SystolicPressure | None = Field(
        default=None, title="Blutdruck systolisch (mmHg)"
    )
    blutdruck_diastolisch: DiastolicPressure | None = Field(
        default=None, title="Blutdruck diastolisch (mmHg)"
    )
    koerpertemperatur: BodyTemperature | None = Field(
        default=None, title="Körpertemperatur (°C)"
    )
    spo2: Spo2 | None = Field(default=None, title="Sauerstoffsättigung (%)")
    puls: Pulse | None = Field(default=None, title="Puls (Schläge/min)")
