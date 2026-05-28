"""Local runner for the SASSIE openmm module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.openmm.openmm_filter as openmm_filter
import sassie.simulate.openmm.openmm_driver as openmm_module

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
    safe_output_filename,
)
from sassie_qt.modules.simulate_helpers import (
    default_openmm_parameter_files,
    listbox_flag,
)


MD_MODE_BY_CODE = {"c1": "0", "c2": "1", "c3": "2"}


class OpenMMRunner(SassieModuleRunner):
    """Run openmm from Qt form values."""

    module = "openmm"
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
        "platform": "string",
        "gpu_device": "string",
        "precision": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        md_code = form_values.get("md_list_box", "c1")
        return {
            "runname": require_value(form_values, "runname", "a run name"),
            "infile": require_existing_file(form_values, "infile", "the input file"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "the reference PDB file"),
            "outfile": safe_output_filename(
                require_value(form_values, "outfile", "an output DCD name"),
                "OpenMM output DCD name",
            ),
            "nsteps": form_values.get("nsteps", "20"),
            "resparmfile": form_values.get("parmfile") or default_openmm_parameter_files(),
            "psffile": require_existing_file(form_values, "psffile", "the PSF file"),
            "ncpu": form_values.get("ncpu", "1"),
            "keepout": listbox_flag(form_values, "keepout_list_box"),
            "dcdfreq": form_values.get("dcdfreq", "20"),
            "infiletype": Path(form_values.get("infile", "")).suffix.lstrip(".") or "pdb",
            "md": MD_MODE_BY_CODE.get(md_code, "0"),
            "mdsteps": form_values.get(
                "mdsteps_1" if md_code == "c2" else "mdsteps_2",
                "20",
            ),
            "dielect": form_values.get(
                "dielect_1" if md_code == "c2" else "dielect_2",
                "80",
            ),
            "temperature": form_values.get(
                "temperature_1" if md_code == "c2" else "temperature_2",
                "300.0",
            ),
            "platform": form_values.get("platform", "CPU"),
            "gpu_device": form_values.get("gpu_device", ""),
            "precision": form_values.get("precision", "mixed"),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = openmm_filter.check_openmm(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return openmm_module.openmm()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return (run_path / variables["outfile"][0],)
