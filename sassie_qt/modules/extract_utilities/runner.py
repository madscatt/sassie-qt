"""Local runner for the SASSIE extract_utilities module."""

from __future__ import annotations

import json
from pathlib import Path

import sassie.interface.extract_utilities.extract_utilities_filter as extract_filter
import sassie.tools.extract_utilities.extract_utilities as extract_utilities

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
)
from sassie_qt.value_helpers import split_repeated, truthy


OPTION_BY_CODE = {
    "c1": "single_frame",
    "c2": "range",
    "c3": "text_file",
    "c4": "weight_file",
    "c5": "sampling_frequency",
    "c6": "all",
    "c7": "voxel_occupancy",
    "c8": "sascalc_guided_voxel_occupancy",
}
SAS_TYPE_BY_CODE = {"c1": "0", "c2": "1", "c3": "2", "c4": "3"}


class ExtractUtilitiesRunner(SassieModuleRunner):
    """Run extract_utilities locally from Qt form values."""

    module = "extract_utilities"
    variable_types = {
        "run_name": "string",
        "pdb_filename": "string",
        "trajectory_filename": "string",
        "option": "string",
        "local_value": "string",
        "output_filename": "string",
        "extract_trajectory": "boolean",
        "extract_sas": "boolean",
        "path": "string",
        "sas_type": "int",
        "sas_paths": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        run_name = require_value(form_values, "runname", "a run name")
        extract_trajectory = truthy(form_values.get("trajectory_checkbox", "false"))
        extract_sas = truthy(form_values.get("sas_checkbox", "false"))
        option_code = form_values.get("option_list_box", "c1")
        option = OPTION_BY_CODE.get(option_code, option_code)

        pdb_filename = ""
        trajectory_filename = ""
        output_filename = form_values.get("output_filename", "").strip()
        if extract_trajectory:
            pdb_filename = require_existing_file(
                form_values,
                "pdb_filename",
                "the reference PDB file",
            )
            trajectory_filename = require_existing_file(
                form_values,
                "trajectory_filename",
                "the trajectory file",
            )
            output_filename = require_value(
                form_values,
                "output_filename",
                "an output file name",
            )

        sas_paths = form_values.get("sas_paths", "").strip()
        if extract_sas:
            sas_paths = require_value(form_values, "sas_paths", "SAS data path(s)")

        return {
            "run_name": run_name,
            "pdb_filename": pdb_filename,
            "trajectory_filename": trajectory_filename,
            "option": option,
            "local_value": self._local_value(
                project_directory,
                run_name,
                option_code,
                form_values,
            ),
            "output_filename": output_filename or "extracted.dcd",
            "extract_trajectory": str(extract_trajectory),
            "extract_sas": str(extract_sas),
            "path": str(project_directory),
            "sas_type": SAS_TYPE_BY_CODE.get(
                form_values.get("sas_type_list_box", "c1"),
                "0",
            ),
            "sas_paths": sas_paths,
        }

    def _local_value(
        self,
        project_directory: Path,
        run_name: str,
        option_code: str,
        form_values: dict[str, str],
    ) -> str:
        if option_code == "c1":
            return require_value(form_values, "local_value_c1", "a frame number")
        if option_code == "c2":
            return require_value(form_values, "local_value_c2", "a frame range")
        if option_code == "c3":
            return require_existing_file(
                form_values,
                "local_value_c3",
                "a text file with frame numbers",
            )
        if option_code == "c4":
            return require_existing_file(
                form_values,
                "local_value_c4",
                "a weight file",
            )
        if option_code == "c5":
            return require_value(form_values, "sampling_frequency", "a sampling frequency")
        if option_code in {"c7", "c8"}:
            return str(
                self._write_voxel_occupancy_config(
                    project_directory,
                    run_name,
                    option_code,
                    form_values,
                )
            )
        return "0"

    def _write_voxel_occupancy_config(
        self,
        project_directory: Path,
        run_name: str,
        option_code: str,
        form_values: dict[str, str],
    ) -> Path:
        suffix = option_code
        domain_names = split_repeated(form_values.get(f"voxel_domain_name_{suffix}", ""))
        domain_bases = split_repeated(form_values.get(f"voxel_domain_basis_{suffix}", ""))
        domains = [
            {"name": name, "basis": domain_bases[index] if index < len(domain_bases) else "all"}
            for index, name in enumerate(domain_names)
        ]
        config = {
            "domains": domains,
            "cluster_domain_names": split_repeated(
                form_values.get(f"voxel_cluster_domain_names_{suffix}", "")
            ),
            "anchor_name": form_values.get(f"voxel_anchor_name_{suffix}", "").strip() or None,
            "voxel_size": form_values.get(f"voxel_size_{suffix}", "15.0"),
            "policy": form_values.get(f"voxel_policy_{suffix}", "hybrid"),
            "representative_policy": form_values.get(
                f"voxel_representative_policy_{suffix}",
                "nearest_center",
            ),
            "cap": _optional_int_text(form_values.get(f"voxel_cap_{suffix}", "")),
            "frame_stride": form_values.get(f"voxel_frame_stride_{suffix}", "1"),
            "frame_limit": _optional_int_text(
                form_values.get(f"voxel_frame_limit_{suffix}", "")
            ),
            "summary_filename": form_values.get(
                f"voxel_summary_filename_{suffix}",
                "voxel_occupancy_summary.json",
            ),
        }
        if suffix == "c8":
            config["sascalc_profile_paths"] = split_repeated(
                form_values.get("sascalc_profile_paths_c8", "")
            )

        project_directory.mkdir(parents=True, exist_ok=True)
        config_file = project_directory / f"{run_name}_{self.module}_{suffix}.json"
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return config_file

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = extract_filter.check_extract_utilities(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return extract_utilities.extract_utilities()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        output_files = []
        if variables["extract_trajectory"][0]:
            output_files.append(run_path / variables["output_filename"][0])
        return tuple(output_files)


def _optional_int_text(value: str):
    value = str(value).strip()
    return int(value) if value else None
