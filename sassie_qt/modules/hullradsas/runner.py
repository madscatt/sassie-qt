"""Local runner for the SASSIE hullradsas module."""

from __future__ import annotations

from pathlib import Path

import sassie.analyze.hullradsas.hullradsas as hullradsas
import sassie.interface.hullradsas.hullradsas_filter as hullradsas_filter

from sassie_qt.modules.analyze_helpers import collect_output_files
from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.contrast_helpers import required_run_name


class HullRadSasRunner(SassieModuleRunner):
    """Run hullradsas from Qt form values."""

    module = "hullradsas"
    variable_types = {
        "run_name": "string",
        "pdbfile": "string",
        "infile": "string",
        "ofile": "string",
        "timeseries_file": "string",
        "stats_file": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": required_run_name(form_values),
            "pdbfile": require_existing_file(form_values, "pdbfile", "a PDB file"),
            "infile": require_existing_file(form_values, "infile", "an input file"),
            "ofile": require_value(form_values, "ofile", "an output file"),
            "timeseries_file": require_value(
                form_values,
                "timeseries_file",
                "a time-series output file",
            ),
            "stats_file": require_value(form_values, "stats_file", "a stats output file"),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = hullradsas_filter.check_hullradsas(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return hullradsas.hullradsas()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)
