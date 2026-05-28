"""Local runner for the SASSIE monomer_monte_carlo module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.monomer_monte_carlo.monomer_monte_carlo_filter as monomer_filter
import sassie.simulate.monomer_monte_carlo.monomer_monte_carlo as monomer_module

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.simulate_helpers import (
    MOLTYPE_BY_CODE,
    default_toppar_file,
    int_flag,
    map_overlap_basis,
    overlap_cutoff,
    parse_alignment_range,
    parse_ranges,
)


class MonomerMonteCarloRunner(SassieModuleRunner):
    """Run monomer_monte_carlo from Qt form values."""

    module = "monomer_monte_carlo"
    variable_types = {
        "run_name": "string",
        "dcdfile": "string",
        "moltype": "string",
        "path": "string",
        "pdbfile": "string",
        "trials": "int",
        "goback": "int",
        "temp": "float",
        "numranges": "int",
        "dtheta": "float_array",
        "reslow": "int_array",
        "numcont": "int_array",
        "lowres1": "int",
        "highres1": "int",
        "basis": "string",
        "cutoff": "float",
        "lowrg": "float",
        "highrg": "float",
        "zflag": "int",
        "zcutoff": "float",
        "cflag": "int",
        "confile": "string",
        "directedmc": "float",
        "nonbondflag": "int",
        "nonbondscale": "float",
        "psffilepath": "string",
        "psffilename": "string",
        "parmfilepath": "string",
        "parmfilename": "string",
        "plotflag": "int",
        "seed": "int_array",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        reslow, numcont = parse_ranges(
            require_value(form_values, "reslow", "flexible residue ranges"),
            inclusive_count=True,
        )
        lowres1, highres1 = parse_alignment_range(
            require_value(form_values, "residue_alignment", "an alignment range")
        )
        pdbfile = Path(require_existing_file(form_values, "pdbfile", "the PDB file"))
        cflag = int_flag(form_values, "cflag_check_box")
        confile = (
            require_existing_file(form_values, "confile", "the constraint file")
            if cflag == "1"
            else ""
        )
        parmfile = Path(default_toppar_file("par_all27_prot_na.inp"))
        return {
            "run_name": require_value(form_values, "runname", "a run name"),
            "dcdfile": require_value(form_values, "dcdfile", "an output DCD name"),
            "moltype": MOLTYPE_BY_CODE.get(
                form_values.get("moltype_list_box", "c1"),
                "protein",
            ),
            "path": str(pdbfile.parent),
            "pdbfile": pdbfile.name,
            "trials": form_values.get("trials", "100"),
            "goback": form_values.get("goback", "20"),
            "temp": form_values.get("temp", "300.0"),
            "numranges": form_values.get("numranges", "1"),
            "dtheta": form_values.get("dtheta", "30.0"),
            "reslow": reslow,
            "numcont": numcont,
            "lowres1": lowres1,
            "highres1": highres1,
            "basis": map_overlap_basis(form_values),
            "cutoff": overlap_cutoff(form_values),
            "lowrg": form_values.get("lowrg", "0.0"),
            "highrg": form_values.get("highrg", "300.0"),
            "zflag": int_flag(form_values, "zflag_check_box"),
            "zcutoff": form_values.get("zcutoff", "0.0"),
            "cflag": cflag,
            "confile": confile,
            "directedmc": form_values.get("directedmc", "0"),
            "nonbondflag": "0",
            "nonbondscale": "1.0",
            "psffilepath": "",
            "psffilename": "",
            "parmfilepath": str(parmfile.parent),
            "parmfilename": parmfile.name,
            "plotflag": "0",
            "seed": "0,123",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = monomer_filter.check_protein(variables, eflag=0, monflag=1)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return monomer_module.monomer_monte_carlo()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        dcd_file = run_path / variables["dcdfile"][0]
        return (
            dcd_file,
            dcd_file.with_name(dcd_file.name + ".stats"),
        )
