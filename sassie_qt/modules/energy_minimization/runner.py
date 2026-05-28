"""Local runner for the SASSIE energy_minimization module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.energy_minimization.minimize_filter as minimize_filter
import sassie.simulate.energy_minimization.energy_minimization as energy_module

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.simulate_helpers import (
    default_toppar_file,
    listbox_flag,
    required_file_or_false,
)


MD_MODE_BY_CODE = {"c1": "0", "c2": "1", "c3": "2", "c4": "0"}


class EnergyMinimizationRunner(SassieModuleRunner):
    """Run energy_minimization from Qt form values."""

    module = "energy_minimization"
    variable_types = {
        "runname": "string",
        "infile": "string",
        "pdbfile": "string",
        "outfile": "string",
        "nsteps": "int",
        "resparmfile": "string",
        "psffile": "string",
        "ncpu": "int",
        "keepout": "int",
        "dcdfreq": "int",
        "infiletype": "string",
        "md": "int",
        "mdsteps": "int",
        "dielect": "float",
        "temperature": "float",
        "use_external_input_file": "boolean",
        "external_input_file": "string",
        "velocity_restart_file": "string",
        "extended_system_restart_file": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        md_code = form_values.get("md_list_box", "c1")
        use_external = md_code == "c4"
        additional_files = form_values.get("additional_files", "false").lower() == "true"
        nsteps = form_values.get(
            "nsteps_1" if md_code == "c1" else "nsteps_2" if md_code == "c2" else "nsteps_3",
            "100",
        )
        dcdfreq = form_values.get("dcdfreq", nsteps)
        return {
            "runname": require_value(form_values, "runname", "a run name"),
            "infile": require_existing_file(form_values, "infile", "the input file"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "the reference PDB file"),
            "outfile": require_value(form_values, "outfile", "an output DCD name"),
            "nsteps": nsteps,
            "resparmfile": form_values.get(
                "parmfile",
                default_toppar_file("par_all27_prot_na.inp"),
            ),
            "psffile": require_existing_file(form_values, "psffile", "the PSF file"),
            "ncpu": form_values.get("ncpu", "1"),
            "keepout": listbox_flag(form_values, "keepout_list_box"),
            "dcdfreq": dcdfreq,
            "infiletype": Path(form_values.get("infile", "")).suffix.lstrip(".") or "pdb",
            "md": MD_MODE_BY_CODE.get(md_code, "0"),
            "mdsteps": form_values.get(
                "mdsteps_1" if md_code == "c2" else "mdsteps_2" if md_code == "c3" else "mdsteps_1",
                "20",
            ),
            "dielect": form_values.get(
                "dielect_1" if md_code == "c2" else "dielect_2" if md_code == "c3" else "dielect_1",
                "80",
            ),
            "temperature": form_values.get(
                "temperature_1" if md_code == "c2" else "temperature_2" if md_code == "c3" else "temperature_1",
                "300.0",
            ),
            "use_external_input_file": str(use_external),
            "external_input_file": (
                require_existing_file(
                    form_values,
                    "external_input_file",
                    "the external NAMD input file",
                )
                if use_external
                else ""
            ),
            "velocity_restart_file": (
                required_file_or_false(
                    form_values,
                    "velocity_restart_file",
                    "the velocity restart file",
                )
                if additional_files
                else "False"
            ),
            "extended_system_restart_file": (
                required_file_or_false(
                    form_values,
                    "extended_system_restart_file",
                    "the extended system restart file",
                )
                if additional_files
                else "False"
            ),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = minimize_filter.check_minimize(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return energy_module.energy_minimization()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return (run_path / variables["outfile"][0],)
