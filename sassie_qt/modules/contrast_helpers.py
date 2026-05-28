"""Shared helpers for local Contrast module runners."""

from __future__ import annotations

from pathlib import Path

from sassie_qt.modules.base import require_existing_file, require_value
from sassie_qt.value_helpers import bool_text, listbox_bool, split_repeated


def repeated_or_default(
    form_values: dict[str, str],
    field_id: str,
    count: int,
    default: str,
) -> list[str]:
    values = split_repeated(form_values.get(field_id, ""))
    if not values:
        values = [default]
    if len(values) >= count:
        return values[:count]
    return values + [values[-1] if values else default] * (count - len(values))


def repeated_files(
    form_values: dict[str, str],
    field_id: str,
    count: int,
    label: str,
) -> list[str]:
    values = split_repeated(form_values.get(field_id, ""))
    if len(values) < count:
        raise ValueError(f"Choose {count} {label}.")
    files = []
    for index, value in enumerate(values[:count], start=1):
        file_path = Path(value).expanduser()
        if file_path.is_dir():
            raise ValueError(f"Choose {label} {index}, not a directory.")
        if not file_path.exists():
            raise ValueError(f"{label} {index} does not exist: {file_path}")
        files.append(str(file_path))
    return files


def require_file_list_or_empty(
    form_values: dict[str, str],
    field_id: str,
    count: int,
    label: str,
) -> list[str]:
    if count <= 0:
        return []
    return repeated_files(form_values, field_id, count, label)


def project_path_text(project_directory: Path) -> str:
    return str(project_directory.expanduser().resolve()) + "/"


def optional_existing_file(
    form_values: dict[str, str],
    field_id: str,
    label: str,
) -> str:
    value = form_values.get(field_id, "").strip()
    if not value:
        return ""
    return require_existing_file(form_values, field_id, label)


def required_run_name(form_values: dict[str, str]) -> str:
    return require_value(form_values, "run_name", "a run name")
