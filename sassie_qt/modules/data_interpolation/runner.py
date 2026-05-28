"""Local runner for the SASSIE data_interpolation module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.data_interpolation.data_interpolation_filter as data_interpolation_filter
import sassie.tools.data_interpolation.data_interpolation as data_interpolation

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
    safe_output_filename,
)


class DataInterpolationRunner(SassieModuleRunner):
    """Run data_interpolation through the common local module-runner path."""

    module = "data_interpolation"
    variable_types = {
        "run_name": "string",
        "data_file_name": "string",
        "output_file_name": "string",
        "izero": "float",
        "izero_error": "float",
        "delta_q": "float",
        "maximum_points": "int",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": require_value(form_values, "run_name", "a run name"),
            "data_file_name": require_existing_file(
                form_values,
                "data_file_name",
                "an experimental data file",
            ),
            "output_file_name": safe_output_filename(
                require_value(
                    form_values,
                    "output_file_name",
                    "an output file name",
                ),
                "output file name",
            ),
            "izero": require_value(form_values, "izero", "I(0)"),
            "izero_error": require_value(form_values, "izero_error", "I(0) error"),
            "delta_q": require_value(form_values, "delta_q", "delta q"),
            "maximum_points": require_value(
                form_values,
                "maximum_points",
                "maximum points",
            ),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = data_interpolation_filter.check_data_interpolation(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return data_interpolation.data_interpolation()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        output_file_name = variables["output_file_name"][0]
        return (
            run_path / output_file_name,
            run_path / f"stn_{output_file_name}",
            run_path / f"{output_file_name[:-3]}json",
        )
