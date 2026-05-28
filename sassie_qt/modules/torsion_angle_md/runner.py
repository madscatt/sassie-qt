"""Local runner for the SASSIE torsion_angle_md module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.torsion_angle_md.torsion_angle_md_filter as tamd_filter
import sassie.simulate.torsion_angle_md.torsion_angle_md as tamd_module
import sassie.util.sassie_config as sassie_config

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.simulate_helpers import (
    MOLTYPE_BY_CODE,
    default_toppar_file,
    parse_ranges,
    repeated_values,
)


class TorsionAngleMDRunner(SassieModuleRunner):
    """Run torsion_angle_md from Qt form values."""

    module = "torsion_angle_md"
    variable_types = {
        "runname": "string",
        "infile": "string",
        "pdbfile": "string",
        "outfile": "string",
        "nsteps": "int",
        "topfile": "string",
        "parmfile": "string",
        "keepout": "int",
        "dcdfreq": "int",
        "charmmexe": "string",
        "temperature": "float",
        "rgforce": "float",
        "rgvalue": "float",
        "dna_segnames": "string",
        "number_flexible_segments": "int",
        "pretamd_min_steps": "string",
        "poll_frequency": "float",
        "path": "string",
    }

    def __init__(self) -> None:
        self.psegvariables: list[list[str]] = []

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        self.psegvariables = self._build_psegvariables(form_values)
        dna_segnames = ",".join(
            row[0] for row in self.psegvariables if row[4] == "dna"
        )
        nsteps = form_values.get("nsteps", "10")
        dcdfreq = form_values.get("dcdfreq", nsteps)
        return {
            "runname": require_value(form_values, "runname", "a run name"),
            "infile": require_existing_file(form_values, "infile", "the input file"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "the reference PDB file"),
            "outfile": require_value(form_values, "outfile", "an output DCD name"),
            "nsteps": nsteps,
            "topfile": form_values.get("topfiles") or default_toppar_file("top_all27_prot_na.inp"),
            "parmfile": form_values.get("paramfiles") or default_toppar_file("par_all27_prot_na.inp"),
            "keepout": "1" if form_values.get("trajectory_check_box", "false").lower() == "true" else "0",
            "dcdfreq": dcdfreq,
            "charmmexe": getattr(sassie_config, "__charmm_executable__", "charmm"),
            "temperature": form_values.get("temperature", "300.0"),
            "rgforce": form_values.get("rgforce", "0"),
            "rgvalue": form_values.get("rgvalue", "0"),
            "dna_segnames": dna_segnames,
            "number_flexible_segments": form_values.get("number_flexible_segments", "1"),
            "pretamd_min_steps": form_values.get("pretamd_min_steps", "10"),
            "poll_frequency": form_values.get("poll_frequency", "10"),
            "path": "",
        }

    def _build_psegvariables(self, form_values: dict[str, str]) -> list[list[str]]:
        names = repeated_values(form_values, "all_flexible_segnames", "MA")
        numranges = repeated_values(form_values, "all_snumranges", "1")
        ranges = repeated_values(form_values, "residue_ranges", "114-134")
        moltypes = repeated_values(form_values, "all_moltype", "c1")
        rows = []
        for index, name in enumerate(names):
            low, count = parse_ranges(
                ranges[index] if index < len(ranges) else ranges[-1],
                inclusive_count=False,
            )
            rows.append(
                [
                    name,
                    numranges[index] if index < len(numranges) else numranges[-1],
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
        errors = tamd_filter.check_torsion_angle_md(variables, self.psegvariables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return tamd_module.torsion_angle_md()

    def sassie_main_args(self, variables: dict, txt_queue) -> tuple:
        return (variables, self.psegvariables, txt_queue)

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return (run_path / variables["outfile"][0],)
