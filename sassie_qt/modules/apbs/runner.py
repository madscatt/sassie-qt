"""Local runner for the SASSIE apbs module."""

from __future__ import annotations

from pathlib import Path

import sassie.analyze.apbs.apbs as apbs
import sassie.interface.apbs.apbs_filter as apbs_filter

from sassie_qt.modules.analyze_helpers import collect_output_files
from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value


class ApbsRunner(SassieModuleRunner):
    """Run apbs from Qt form values."""

    module = "apbs"
    variable_types = {
        "runname": "string",
        "infile": "string",
        "pdbfile": "string",
        "ph": "float",
        "temperature": "float",
        "ion_charge": "float",
        "ion_conc": "float",
        "ion_radius": "float",
        "manual_flag": "int",
        "manual_file": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "runname": require_value(form_values, "runname", "a run name"),
            "infile": require_existing_file(form_values, "infile", "an input file"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "a PDB file"),
            "ph": form_values.get("ph", "5.5"),
            "temperature": form_values.get("temp", form_values.get("temperature", "300.0")),
            "ion_charge": form_values.get("ion_charge", "1.0"),
            "ion_conc": form_values.get("ion_conc", "0.15"),
            "ion_radius": form_values.get("ion_radius", "1.62"),
            "manual_flag": form_values.get("manual_flag", "0"),
            "manual_file": form_values.get("manual_file", "test_input_file.txt"),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = apbs_filter.check_apbs(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return apbs.apbs()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)
