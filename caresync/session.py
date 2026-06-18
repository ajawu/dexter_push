from __future__ import annotations

import sys

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo


def capture(entry: BaseModel, bounded: type[BaseModel]) -> BaseModel | str:
    """Validate, repair, and confirm one draft. Return the confirmed entry or why not."""
    updates: dict[str, object] = {}
    for field_name, field in bounded.model_fields.items():
        field_adapter = TypeAdapter(field.annotation)
        value = getattr(entry, field_name)

        if value is not None and _validate(field_adapter, value):
            continue

        question = _question(field, field_name, value, field.is_required())
        prompt = question
        while answer := input(prompt).strip() != "":
            try:
                updates[field_name] = field_adapter.validate_python(answer)
                break
            except ValidationError as exc:
                prompt = f"{question} (rejected: {exc.errors()[0]['msg']})"
        else:
            if field.is_required() and value == "":
                return f"{field_name} is a required field and cannot be skipped"

    final = bounded.model_validate({**entry.model_dump(), **updates})
    print(final.model_dump_json(indent=2), file=sys.stderr)
    confirm = input("Confirm? [y/N] ").strip().lower().startswith("y")
    if not confirm:
        return "Carer declined at confirmation"
    return final


def _validate(adapter: TypeAdapter[object], value: object) -> bool:
    """Whether ``value`` passes the field's bound -- the in-range test, without raising."""
    try:
        adapter.validate_python(value)
        return True
    except ValidationError:
        return False


def _question(field: FieldInfo, name: str, value: object, is_required: bool) -> str:
    """The repair prompt for a field: a skippable fill if null, a correction if impossible."""
    label = field.title or name
    if value is None:
        return f"{label} [Required]: " if is_required else f"{label} [leave blank to skip]: "
    return f"{label} is {value!r}, outside the allowed range -- correct it: "
