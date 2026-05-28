"""Local runner for the SASSIE pdbscan module."""

from __future__ import annotations

from pathlib import Path

import sassie.build.pdbscan.pdb_scan as pdb_scan

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
)


class PDBScanRunner(SassieModuleRunner):
    """Run PDBScan from Qt form values."""

    module = "pdbscan"
    variable_types = {
        "runname": "string",
        "pdbfile": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "runname": require_value(form_values, "runname", "a run name"),
            "pdbfile": require_existing_file(
                form_values,
                "pdbfile",
                "the PDB file",
            ),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        return

    def create_sassie_module(self):
        return pdb_scan.PDBScan()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        pdb_name = Path(variables["pdbfile"][0]).stem
        return (
            run_path / f"{pdb_name}.mkd",
            run_path / f"{pdb_name}.html",
        )
