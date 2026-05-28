"""Local runner for the SASSIE complex_monte_carlo module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.complex_monte_carlo.complex_filter as complex_filter
import sassie.simulate.complex_monte_carlo.complex_monte_carlo as complex_module

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.simulate_helpers import (
    MOLTYPE_BY_CODE,
    default_toppar_file,
    int_flag,
    map_overlap_basis,
    parse_alignment_range,
    parse_ranges,
    repeated_values,
)


class ComplexMonteCarloRunner(SassieModuleRunner):
    """Run complex_monte_carlo from Qt form values."""

    module = "complex_monte_carlo"
    variable_types = {
        "cflag": "int",
        "confile": "string",
        "dcdfile": "string",
        "directedmc": "float",
        "flpsegname": "string",
        "goback": "int",
        "highrg": "float",
        "lowrg": "float",
        "npsegments": "int",
        "nsegments": "int",
        "parmfilename": "string",
        "path": "string",
        "pdbfile": "string",
        "psffilename": "string",
        "runname": "string",
        "seed": "int_array",
        "segbasis": "string",
        "seghigh": "int_array",
        "seglow": "int_array",
        "temp": "float",
        "trials": "int",
        "zcutoff": "float",
        "zflag": "int",
    }

    def __init__(self) -> None:
        self.psegvariables: list[list[str]] = []

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        pdbfile = Path(require_existing_file(form_values, "pdbfile", "the PDB file"))
        cflag = int_flag(form_values, "cflag_list_box")
        confile = (
            require_existing_file(form_values, "confile", "the constraint file")
            if cflag == "1"
            else ""
        )
        seglow, seghigh = parse_ranges(
            require_value(form_values, "seg_align", "a segment alignment range"),
            inclusive_count=False,
        )
        self.psegvariables = self._build_psegvariables(form_values)
        return {
            "cflag": cflag,
            "confile": confile,
            "dcdfile": require_value(form_values, "dcdfile", "an output DCD name"),
            "directedmc": form_values.get("directedmc", "0"),
            "flpsegname": ",".join(
                repeated_values(form_values, "flpsegname", "VN1")
            ),
            "goback": form_values.get("goback", "20"),
            "highrg": form_values.get("highrg", "300.0"),
            "lowrg": form_values.get("lowrg", "0.0"),
            "npsegments": form_values.get("npsegments", "1"),
            "nsegments": form_values.get("nsegments", "2"),
            "parmfilename": Path(default_toppar_file("par_all27_prot_na.inp")).name,
            "path": str(pdbfile.parent),
            "pdbfile": pdbfile.name,
            "psffilename": "",
            "runname": require_value(form_values, "runname", "a run name"),
            "seed": "0,123",
            "segbasis": map_overlap_basis(form_values),
            "seghigh": seghigh,
            "seglow": seglow,
            "temp": form_values.get("temp", "300.0"),
            "trials": form_values.get("trials", "20"),
            "zcutoff": form_values.get("zcutoff", "0.0"),
            "zflag": int_flag(form_values, "zflag_check_box"),
        }

    def _build_psegvariables(self, form_values: dict[str, str]) -> list[list[str]]:
        moltypes = repeated_values(form_values, "moltype", "c1")
        names = repeated_values(form_values, "flpsegname", "VN1")
        numranges = repeated_values(form_values, "numranges", "1")
        ranges = repeated_values(form_values, "srlow", "40-129")
        angles = repeated_values(form_values, "sith", "30.0")
        rows = []
        for index, name in enumerate(names):
            low, count = parse_ranges(
                ranges[index] if index < len(ranges) else ranges[-1],
                inclusive_count=False,
            )
            rows.append(
                [
                    numranges[index] if index < len(numranges) else numranges[-1],
                    angles[index] if index < len(angles) else angles[-1],
                    low,
                    count,
                    MOLTYPE_BY_CODE.get(
                        moltypes[index] if index < len(moltypes) else moltypes[-1],
                        "protein",
                    ),
                ]
            )
        return rows

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = complex_filter.check_complex(variables, self.psegvariables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return complex_module.complex_monte_carlo()

    def sassie_main_args(self, variables: dict, txt_queue) -> tuple:
        return (variables, self.psegvariables, txt_queue)

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        dcd_file = run_path / variables["dcdfile"][0]
        return (
            dcd_file,
            dcd_file.with_name(dcd_file.name + ".stats"),
        )
