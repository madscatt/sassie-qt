"""Local runner for the SASSIE pdbrx module."""

from __future__ import annotations

from pathlib import Path

import sassie.build.pdbrx.pdb_rx as pdb_rx

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
)


class PDBRxRunner(SassieModuleRunner):
    """Run PDBRx from Qt form values."""

    module = "pdbrx"
    variable_types = {
        "runname": "string",
        "pdbfile": "string",
        "topfile": "string",
        "defaults": "boolean",
        "user_interface": "string",
        "gui": "string",
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
                "the input PDB file",
            ),
            "topfile": require_existing_file(
                form_values,
                "topfile",
                "the CHARMM topology file",
            ),
            "defaults": form_values.get("defaults", "true"),
            "user_interface": "terminal",
            "gui": "terminal",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        return

    def create_sassie_module(self):
        return pdb_rx.PDBRx()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        prefix = f"{Path(variables['pdbfile'][0]).stem}_charmm"
        return (
            run_path / f"{prefix}.pdb",
            run_path / f"{prefix}.psf",
            run_path / f"{prefix}_xplor.psf",
            run_path / "psfgen_pdbrx.in",
        )
