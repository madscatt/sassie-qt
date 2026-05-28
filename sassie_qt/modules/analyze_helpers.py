"""Shared helpers for local Analyze module runners."""

from __future__ import annotations

from pathlib import Path

from sassie_qt.modules.base import require_existing_file, require_value
from sassie_qt.value_helpers import bool_text, split_repeated


def collect_output_files(run_path: Path) -> tuple[Path, ...]:
    if not run_path.exists():
        return ()
    return tuple(sorted(path for path in run_path.rglob("*") if path.is_file()))


def listbox_index(value: str, first_code: int = 1, default: int = 1) -> str:
    if value.startswith("c") and value[1:].isdigit():
        return str(int(value[1:]) - first_code)
    return str(default)


def listbox_number(value: str, default: int = 1) -> str:
    if value.startswith("c") and value[1:].isdigit():
        return str(int(value[1:]))
    return str(default)


def optional_file_by_flag(
    form_values: dict[str, str],
    flag_id: str,
    file_id: str,
    label: str,
) -> str:
    if bool_text(form_values.get(flag_id, "false")) != "True":
        return form_values.get(file_id, "").strip()
    return require_existing_file(form_values, file_id, label)


def required_run_name_or_runname(
    form_values: dict[str, str],
    field_id: str = "run_name",
) -> str:
    return require_value(form_values, field_id, "a run name")


def repeated_text_or_empty(form_values: dict[str, str], field_id: str) -> str:
    return ",".join(split_repeated(form_values.get(field_id, "")))
