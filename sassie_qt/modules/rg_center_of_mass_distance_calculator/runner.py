"""Local runner for the SASSIE Rg center-of-mass distance calculator."""

from __future__ import annotations

from pathlib import Path

import sassie.contrast.rg_center_of_mass_distance_calculator.rg_center_of_mass_distance_calculator as rgcmd
import sassie.interface.rg_center_of_mass_distance_calculator.rg_center_of_mass_distance_calculator_filter as rgcmd_filter

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
)
from sassie_qt.modules.contrast_helpers import (
    project_path_text,
    repeated_or_default,
    required_run_name,
)


class RgCenterOfMassDistanceCalculatorRunner(SassieModuleRunner):
    """Run rg_center_of_mass_distance_calculator from Qt form values."""

    module = "rg_center_of_mass_distance_calculator"
    variable_types = {
        "run_name": "string",
        "pdb_file_name": "string",
        "trajectory_file_name": "string",
        "number_of_components": "int",
        "component_name": "string_array",
        "basis_string": "string_array",
        "number_of_weight_files": "int",
        "weight_file_names": "string_array",
        "weight_basis_string": "string_array",
        "path": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        component_count = int(form_values.get("number_of_components", "2"))
        return {
            "run_name": required_run_name(form_values),
            "pdb_file_name": require_existing_file(
                form_values,
                "pdb_file_name",
                "the reference PDB file",
            ),
            "trajectory_file_name": require_existing_file(
                form_values,
                "trajectory_file_name",
                "the trajectory file",
            ),
            "number_of_components": str(component_count),
            "component_name": ",".join(
                repeated_or_default(
                    form_values,
                    "component_name",
                    component_count,
                    "component",
                )
            ),
            "basis_string": ",".join(
                repeated_or_default(
                    form_values,
                    "basis_string",
                    component_count,
                    "segname SEG1",
                )
            ),
            "number_of_weight_files": form_values.get(
                "number_of_weight_files",
                "0",
            ),
            "weight_file_names": form_values.get("weight_file_names", ""),
            "weight_basis_string": form_values.get("weight_basis_string", ""),
            "path": project_path_text(project_directory),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = rgcmd_filter.check_rg_center_of_mass_distance_calculator(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return rgcmd.rg_center_of_mass_distance_calculator()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        trajectory_name = Path(variables["trajectory_file_name"][0]).name
        suffix = "dcd" if trajectory_name.lower().endswith(".dcd") else "pdb"
        output_name = f"{Path(trajectory_name).stem}_rgdist_{suffix}.txt"
        return (run_path / output_name,)
