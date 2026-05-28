"""Helpers shared by local Simulate module runners."""

from __future__ import annotations

from pathlib import Path

import sassie.util.sassie_config as sassie_config

from sassie_qt.modules.base import require_existing_file, require_value
from sassie_qt.value_helpers import split_repeated, truthy


OVERLAP_BASIS_BY_CODE = {
    "c1": "heavy",
    "c2": "all",
    "c3": "backbone",
}
MOLTYPE_BY_CODE = {
    "c1": "protein",
    "c2": "rna",
    "c3": "dna",
}


def boolean_flag(form_values: dict[str, str], field_id: str) -> str:
    return str(truthy(form_values.get(field_id, "false")))


def int_flag(form_values: dict[str, str], field_id: str) -> str:
    return "1" if truthy(form_values.get(field_id, "false")) else "0"


def listbox_flag(form_values: dict[str, str], field_id: str) -> str:
    return "1" if form_values.get(field_id, "c1") == "c2" else "0"


def required_file_or_false(
    form_values: dict[str, str],
    field_id: str,
    label: str,
) -> str:
    value = form_values.get(field_id, "").strip()
    if not value or value.lower() == "false":
        return "False"
    return require_existing_file(form_values, field_id, label)


def default_toppar_file(name: str) -> str:
    return str(Path(sassie_config.__bin_path__) / "toppar" / name)


def default_openmm_parameter_files() -> str:
    names = [
        "top_all36_prot.rtf",
        "par_all36m_prot.prm",
        "top_all36_na.rtf",
        "par_all36_na.prm",
        "top_all36_lipid.rtf",
        "par_all36_lipid.prm",
        "top_all36_carb.rtf",
        "par_all36_carb.prm",
        "top_all36_cgenff.rtf",
        "par_all36_cgenff.prm",
        "toppar_water_ions.str",
    ]
    return ",".join(default_toppar_file(name) for name in names)


def map_overlap_basis(form_values: dict[str, str], custom_default: str = "CA") -> str:
    code = form_values.get("overlap_list_box", "c1")
    if code == "c4":
        return require_value(form_values, "basis", "an overlap basis")
    return OVERLAP_BASIS_BY_CODE.get(code, custom_default)


def overlap_cutoff(form_values: dict[str, str]) -> str:
    code = form_values.get("overlap_list_box", "c1")
    if code == "c3":
        return "1.0"
    if code == "c4":
        return form_values.get("cutoff", "3.0")
    return "0.8"


def parse_ranges(value: str, inclusive_count: bool) -> tuple[str, str]:
    starts = []
    counts = []
    for item in split_repeated(value):
        low_text, separator, high_text = item.partition("-")
        low = int(low_text.strip())
        high = int(high_text.strip()) if separator else low
        starts.append(str(low))
        counts.append(str(high - low + (1 if inclusive_count else 0)))
    return ",".join(starts), ",".join(counts)


def parse_alignment_range(value: str) -> tuple[str, str]:
    low_text, separator, high_text = value.partition("-")
    return low_text.strip(), high_text.strip() if separator else low_text.strip()


def repeated_values(form_values: dict[str, str], field_id: str, default: str) -> list[str]:
    values = split_repeated(form_values.get(field_id, default))
    return values or [default]


def join_repeated_codes(
    form_values: dict[str, str],
    field_id: str,
    mapping: dict[str, str],
    default: str,
) -> str:
    return ",".join(
        mapping.get(item, item)
        for item in repeated_values(form_values, field_id, default)
    )
