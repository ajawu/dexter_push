"""The one place clinical bounds live.

Every physiological limit in CareSync is a plain ``Field(ge=..., le=...)`` carried
by one of the named ``Annotated`` types below. Provider schemas import these names;
they never write a bound of their own. The set is closed and hand-reviewed.
"""

from __future__ import annotations

from typing import Annotated, Final, NamedTuple, get_args

from annotated_types import Ge, Le
from pydantic import Field

SystolicPressure = Annotated[int, Field(ge=50, le=300)]
DiastolicPressure = Annotated[int, Field(ge=30, le=200)]
Pulse = Annotated[int, Field(ge=20, le=300)]
BodyTemperature = Annotated[float, Field(ge=30.0, le=45.0)]
Spo2 = Annotated[int, Field(ge=50, le=100)]
RespiratoryRate = Annotated[int, Field(ge=4, le=80)]
BloodGlucose = Annotated[float, Field(ge=20.0, le=800.0)]  # mg/dL
Weight = Annotated[float, Field(ge=20.0, le=400.0)]  # kg

# The closed set, named explicitly. Scanning module globals would be fragile and
# would silently pick up anything later added above; this list is the contract.
_NAMED_TYPES: Final[dict[str, object]] = {
    "SystolicPressure": SystolicPressure,
    "DiastolicPressure": DiastolicPressure,
    "Pulse": Pulse,
    "BodyTemperature": BodyTemperature,
    "Spo2": Spo2,
    "RespiratoryRate": RespiratoryRate,
    "BloodGlucose": BloodGlucose,
    "Weight": Weight,
}


class Bound(NamedTuple):
    """One named type's enforced range, as introspected from its annotation."""
    name: str
    base: str  # "int" | "float"
    ge: float | None
    le: float | None


def describe_bounds() -> list[Bound]:
    """Introspect every named type into a flat, loggable list of its bounds.

    Pure: reads only the annotations declared in this module, performs no I/O.
    """
    bounds: list[Bound] = []
    for name, alias in _NAMED_TYPES.items():
        base, field_info = get_args(alias)
        ge: float | None = None
        le: float | None = None
        for meta in field_info.metadata:
            if isinstance(meta, Ge) and isinstance(meta.ge, (int, float)):
                ge = float(meta.ge)
            elif isinstance(meta, Le) and isinstance(meta.le, (int, float)):
                le = float(meta.le)
        bounds.append(Bound(name=name, base=base.__name__, ge=ge, le=le))
    return bounds
