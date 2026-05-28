"""Local runner for the SASSIE altens module."""

from __future__ import annotations

from pathlib import Path

import sassie.analyze.altens.altens as altens
import sassie.interface.altens.altens_filter as altens_filter

from sassie_qt.modules.analyze_helpers import collect_output_files, optional_file_by_flag
from sassie_qt.modules.base import SassieModuleRunner, require_existing_file
from sassie_qt.modules.contrast_helpers import bool_text, required_run_name


class AltensRunner(SassieModuleRunner):
    """Run altens from Qt form values."""

    module = "altens"
    variable_types = {
        "run_name": "string",
        "rdc_input_file": "string",
        "pdbfile": "string",
        "dcdfile": "string",
        "residue_list_file_flag": "boolean",
        "residue_list_file": "string",
        "use_monte_carlo_flag": "boolean",
        "number_of_monte_carlo_steps": "int",
        "seed": "int_array",
        "plotly_plot_flag": "boolean",
        "bokeh_plot_flag": "boolean",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": required_run_name(form_values),
            "rdc_input_file": require_existing_file(
                form_values,
                "rdc_input_file",
                "an RDC input file",
            ),
            "pdbfile": require_existing_file(form_values, "pdbfile", "a PDB file"),
            "dcdfile": require_existing_file(form_values, "dcdfile", "a trajectory file"),
            "residue_list_file_flag": bool_text(
                form_values.get("residue_list_file_flag", "false"),
            ),
            "residue_list_file": optional_file_by_flag(
                form_values,
                "residue_list_file_flag",
                "residue_list_file",
                "a residue list file",
            ),
            "use_monte_carlo_flag": bool_text(
                form_values.get("use_monte_carlo_flag", "true"),
            ),
            "number_of_monte_carlo_steps": form_values.get(
                "number_of_monte_carlo_steps",
                "25",
            ),
            "seed": form_values.get("seed", "1,123"),
            "plotly_plot_flag": "True",
            "bokeh_plot_flag": "False",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = altens_filter.check_altens(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return altens.altens()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)
