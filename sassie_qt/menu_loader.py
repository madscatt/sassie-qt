"""Load the canonical GenApp menu and module metadata for the Qt prototype."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_GENAPP_ZAZZIE_ROOT = Path.home() / "git_working_copies" / "genapp_zazzie"
DEFAULT_ZAZZIE_ROOT = Path.home() / "git_working_copies" / "zazzie"


@dataclass(frozen=True)
class ModuleMenuItem:
    """A module entry from the canonical menu."""

    id: str
    label: str
    views: tuple[str, ...]


@dataclass(frozen=True)
class MenuGroup:
    """A top-level canonical menu group."""

    id: str
    label: str
    icon_path: Path | None
    modules: tuple[ModuleMenuItem, ...]
    restricted: str | None = None


@dataclass(frozen=True)
class ModuleField:
    """A compact field summary suitable for a stub form preview."""

    id: str
    label: str
    field_type: str
    role: str
    default: Any = None
    values: Any = None
    required: bool = False
    help_text: str = ""


@dataclass(frozen=True)
class ModuleDefinition:
    """Metadata loaded from a GenApp module JSON file."""

    id: str
    label: str
    path: Path
    fields: tuple[ModuleField, ...]


def _strip_hash_comment_lines(text: str) -> str:
    """Remove GenApp menu comment lines before JSON parsing."""

    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _truthy(value: Any) -> bool:
    return str(value).lower() == "true"


def _clean_label(module_id: str) -> str:
    if module_id == "etc":
        return "File Manager"
    return module_id.replace("_", " ").title()


def load_menu(genapp_zazzie_root: Path = DEFAULT_GENAPP_ZAZZIE_ROOT) -> tuple[MenuGroup, ...]:
    """Load top-level menu groups from the GenApp SASSIE menu."""

    menu_path = genapp_zazzie_root / "menu.json"
    menu_data = json.loads(_strip_hash_comment_lines(menu_path.read_text()))
    groups: list[MenuGroup] = []

    for raw_group in menu_data.get("menu", []):
        raw_modules = raw_group.get("modules", [])
        modules = tuple(
            ModuleMenuItem(
                id=raw_module["id"],
                label=raw_module.get("label") or _clean_label(raw_module["id"]),
                views=tuple(raw_module.get("views", ("Input", "Output", "Plots", "OpenGL"))),
            )
            for raw_module in raw_modules
        )
        icon = raw_group.get("icon")
        icon_path = genapp_zazzie_root / icon if icon else None
        group_id = raw_group["id"]
        groups.append(
            MenuGroup(
                id=group_id,
                label=raw_group.get("label") or _clean_label(group_id),
                icon_path=icon_path if icon_path and icon_path.exists() else None,
                modules=modules,
                restricted=raw_group.get("restricted"),
            )
        )

    return tuple(groups)


def load_module_definition(
    module_id: str,
    genapp_zazzie_root: Path = DEFAULT_GENAPP_ZAZZIE_ROOT,
) -> ModuleDefinition | None:
    """Load a module JSON definition if one exists."""

    module_path = genapp_zazzie_root / "modules" / f"{module_id}.json"
    if not module_path.exists():
        return None

    module_data = json.loads(_strip_hash_comment_lines(module_path.read_text()))
    fields: list[ModuleField] = []
    for raw_field in module_data.get("fields", []):
        field_id = raw_field.get("id") or raw_field.get("name") or "(unnamed)"
        fields.append(
            ModuleField(
                id=field_id,
                label=raw_field.get("label") or _clean_label(field_id),
                field_type=raw_field.get("type", "unknown"),
                role=raw_field.get("role", "input"),
                default=raw_field.get("default"),
                values=raw_field.get("values"),
                required=_truthy(raw_field.get("required")),
                help_text=raw_field.get("help", ""),
            )
        )

    return ModuleDefinition(
        id=module_data.get("moduleid") or module_id,
        label=module_data.get("label") or _clean_label(module_id),
        path=module_path,
        fields=tuple(fields),
    )


def find_gui_mimic_path(
    module_id: str,
    zazzie_root: Path = DEFAULT_ZAZZIE_ROOT,
) -> Path | None:
    """Resolve the nearest SASSIE gui_mimic file for a module id."""

    sassie_root = zazzie_root / "src" / "sassie"
    if not sassie_root.exists():
        return None

    exact_name = f"gui_mimic_{module_id}.py"
    exact_matches = sorted(sassie_root.rglob(exact_name))
    if exact_matches:
        return exact_matches[0]

    partial_matches = sorted(
        path
        for path in sassie_root.rglob("gui_mimic*.py")
        if module_id in path.stem
    )
    if partial_matches:
        return partial_matches[0]

    return None
