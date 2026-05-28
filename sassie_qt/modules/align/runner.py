"""Local runner for the SASSIE align module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.align.align_filter as align_filter
import sassie.tools.align.align as align

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
)


class AlignRunner(SassieModuleRunner):
    """Run align in the style of gui_mimic_align, without GenApp overhead."""

    module = "align"
    variable_types = {
        "run_name": "string",
        "path": "string",
        "pdbmol1": "string",
        "pdbmol2": "string",
        "infile": "string",
        "ofile": "string",
        "basis1": "string",
        "basis2": "string",
        "lowres1": "int",
        "lowres2": "int",
        "highres1": "int",
        "highres2": "int",
        "ebasis1": "string",
        "ebasis2": "string",
        "zflag": "boolean",
        "zcutoff": "float",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": require_value(form_values, "runname", "a run name"),
            # align.py concatenates path + filename; absolute filenames need an empty path.
            "path": "",
            "pdbmol1": require_existing_file(
                form_values,
                "pdbmol1",
                "the molecule 1 reference PDB file",
            ),
            "pdbmol2": require_existing_file(
                form_values,
                "pdbmol2",
                "the molecule 2 reference PDB file",
            ),
            "infile": require_existing_file(
                form_values,
                "infile",
                "the coordinates to align",
            ),
            "ofile": require_value(form_values, "ofile", "an output file name"),
            "basis1": require_value(form_values, "basis1", "molecule 1 basis"),
            "basis2": require_value(form_values, "basis2", "molecule 2 basis"),
            "lowres1": require_value(form_values, "lowres1", "molecule 1 low residue"),
            "lowres2": require_value(form_values, "lowres2", "molecule 2 low residue"),
            "highres1": require_value(form_values, "highres1", "molecule 1 high residue"),
            "highres2": require_value(form_values, "highres2", "molecule 2 high residue"),
            "ebasis1": form_values.get("ebasis1", "None").strip() or "None",
            "ebasis2": form_values.get("ebasis2", "None").strip() or "None",
            "zflag": form_values.get("zflag_check_box", "false"),
            "zcutoff": form_values.get("zcutoff", "0.0").strip() or "0.0",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        # no_file_check avoids align_filter joining a path prefix onto absolute desktop paths.
        errors = align_filter.check_align(variables, no_file_check="true")
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return align.align()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        output_file = run_path / variables["ofile"][0]
        return (output_file, output_file.with_name(output_file.name + ".minmax"))
