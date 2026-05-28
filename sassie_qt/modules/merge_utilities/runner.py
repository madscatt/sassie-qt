"""Local runner for the SASSIE merge_utilities module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.merge_utilities.merge_utilities_filter as merge_filter
import sassie.tools.merge_utilities.merge_utilities as merge_utilities

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
    safe_output_filename,
)
from sassie_qt.value_helpers import split_repeated, truthy


SAS_TYPE_BY_CODE = {"c1": "0", "c2": "1", "c3": "2", "c4": "3"}
MERGE_TYPE_BY_CODE = {"c1": "0", "c2": "1", "c3": "2"}


class MergeUtilitiesRunner(SassieModuleRunner):
    """Run merge_utilities locally from Qt form values."""

    module = "merge_utilities"
    variable_types = {
        "run_name": "string",
        "pdb_file": "string",
        "trajectory_names": "string",
        "output_filename": "string",
        "number_of_runs": "int",
        "local_value": "string",
        "merge_option": "int",
        "merge_type_option": "int",
        "sas_type": "int",
        "sas_paths": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        merge_trajectory = truthy(form_values.get("trajectory_checkbox", "false"))
        merge_sas = truthy(form_values.get("sas_checkbox", "false"))
        if merge_trajectory and merge_sas:
            merge_option = "0"
        elif merge_sas:
            merge_option = "1"
        elif merge_trajectory:
            merge_option = "2"
        else:
            raise ValueError("Choose merge trajectories, merge SAS, or both before running.")

        number_of_runs = require_value(
            form_values,
            "number_of_runs_to_merge",
            "the number of runs to merge",
        )
        pdb_file = ""
        trajectory_names = ""
        output_filename = safe_output_filename(
            form_values.get("output_filename", "").strip() or "merged.dcd",
            "merged trajectory output filename",
        )
        if merge_trajectory:
            pdb_file = require_existing_file(
                form_values,
                "pdb_file",
                "the reference PDB file",
            )
            trajectory_names = _require_existing_file_list(
                form_values,
                "trajectory_names",
                "trajectory file",
            )
            output_filename = safe_output_filename(
                require_value(
                    form_values,
                    "output_filename",
                    "an output file name",
                ),
                "merged trajectory output filename",
            )

        sas_paths = form_values.get("sas_paths", "").strip()
        if merge_sas:
            sas_paths = require_value(form_values, "sas_paths", "SAS data path(s)")

        merge_type_option = MERGE_TYPE_BY_CODE.get(
            form_values.get("merge_option_list_box", "c1"),
            "0",
        )
        return {
            "run_name": require_value(form_values, "runname", "a run name"),
            "pdb_file": pdb_file,
            "trajectory_names": trajectory_names,
            "output_filename": output_filename,
            "number_of_runs": number_of_runs,
            "local_value": self._local_value(merge_type_option, form_values),
            "merge_option": merge_option,
            "merge_type_option": merge_type_option,
            "sas_type": SAS_TYPE_BY_CODE.get(
                form_values.get("sas_type_list_box", "c1"),
                "0",
            ),
            "sas_paths": sas_paths,
        }

    def _local_value(
        self,
        merge_type_option: str,
        form_values: dict[str, str],
    ) -> str:
        if merge_type_option == "1":
            return _require_existing_file_list(
                form_values,
                "weight_files",
                "weight file",
            )
        if merge_type_option == "2":
            return require_value(
                form_values,
                "sampling_frequency",
                "a sampling frequency",
            )
        return "0"

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = merge_filter.check_merge_utilities(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return merge_utilities.merge_utilities()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        if variables["merge_option"][0] in (0, 2):
            return (run_path / variables["output_filename"][0],)
        return ()


def _require_existing_file_list(
    form_values: dict[str, str],
    field_id: str,
    label: str,
) -> str:
    values = split_repeated(require_value(form_values, field_id, label))
    if not values:
        raise ValueError(f"Choose at least one {label} before running.")
    for value in values:
        file_path = Path(value).expanduser()
        if file_path.is_dir():
            raise ValueError(f"Choose a {label}, not a directory: {file_path}")
        if not file_path.exists():
            raise ValueError(f"{label.capitalize()} does not exist: {file_path}")
    return ",".join(values)
