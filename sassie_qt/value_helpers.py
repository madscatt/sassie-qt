"""Small value-normalization helpers shared by UI state and runners."""

from __future__ import annotations

from typing import Any


TRUE_TEXT_VALUES = frozenset({"1", "true", "yes", "on"})


def truthy(value: Any) -> bool:
    """Return whether a GenApp/Qt form value should be treated as enabled."""

    return str(value).strip().lower() in TRUE_TEXT_VALUES


def bool_text(value: Any) -> str:
    """Return SASSIE's expected Python-style boolean text."""

    return str(truthy(value))


def listbox_bool(value: str, true_code: str = "c1") -> str:
    """Return Python-style boolean text for a GenApp listbox code."""

    return str(str(value) == true_code)


def field_value_to_text(value: Any, list_separator: str = ",") -> str:
    """Convert a GenApp JSON field value to editable text."""

    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return list_separator.join(str(item) for item in value)
    return str(value)


def split_repeated(value: Any) -> list[str]:
    """Split a comma-delimited repeated field value, trimming empty cells."""

    return [item.strip() for item in str(value).split(",") if item.strip()]


def nested_values(value: Any) -> list[list[str]]:
    """Split semicolon rows containing comma-delimited cells."""

    return [
        [cell.strip() for cell in row.split(",")]
        for row in str(value).split(";")
        if row.strip()
    ]
