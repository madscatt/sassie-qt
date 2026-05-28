"""Local runner for the SASSIE density_plot module."""

from __future__ import annotations

from pathlib import Path

import sassie.analyze.density_plot.density_plot as density_plot
import sassie.interface.density_plot.density_plot_filter as density_plot_filter

from sassie_qt.modules.analyze_helpers import collect_output_files, listbox_number
from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.contrast_helpers import (
    project_path_text,
    repeated_or_default,
    required_run_name,
    split_repeated,
)


class DensityPlotRunner(SassieModuleRunner):
    """Run density_plot from Qt form values."""

    module = "density_plot"
    variable_types = {
        "run_name": "string",
        "path": "string",
        "dcdfile": "string",
        "pdbfile": "string",
        "ofile": "string",
        "nsegments": "int",
        "xlength": "float",
        "ylength": "float",
        "zlength": "float",
        "gridsp": "float",
        "equalweights": "int",
        "weightsfile": "string",
        "save_occupancy": "string",
    }

    def __init__(self) -> None:
        self.segvariables: list[list[str]] = []

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        xlength, ylength, zlength = self._box_lengths(form_values)
        uses_weight_file = str(form_values.get("weight_flag_check_box", "")).lower() == "true"
        return {
            "run_name": required_run_name(form_values),
            "path": project_path_text(project_directory),
            "dcdfile": require_existing_file(form_values, "dcdfile", "a trajectory file"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "a PDB file"),
            "ofile": require_value(form_values, "ofile", "an output file prefix"),
            "nsegments": form_values.get("nsegments", "1"),
            "xlength": xlength,
            "ylength": ylength,
            "zlength": zlength,
            "gridsp": form_values.get("gridsp", "5.0"),
            "equalweights": "0" if uses_weight_file else "1",
            "weightsfile": (
                require_existing_file(form_values, "weightsfile", "a weights file")
                if uses_weight_file
                else form_values.get("weightsfile", "")
            ),
            "save_occupancy": (
                "Y"
                if listbox_number(form_values.get("save_occupancy_list_box", "c1")) == "2"
                else "N"
            ),
        }

    def prepare_variables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict:
        variables = super().prepare_variables(project_directory, form_values)
        self.segvariables = self._segment_variables(form_values, variables["nsegments"][0])
        return variables

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = density_plot_filter.check_density_plot(variables, self.segvariables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return density_plot.density_plot()

    def sassie_main_args(self, variables: dict, txt_queue) -> tuple:
        return (variables, self.segvariables, txt_queue)

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)

    def _box_lengths(self, form_values: dict[str, str]) -> tuple[str, str, str]:
        values = split_repeated(form_values.get("box_lengths", "100,100,100"))
        if len(values) != 3:
            raise ValueError("Enter three box lengths separated by commas.")
        return values[0], values[1], values[2]

    def _segment_variables(
        self,
        form_values: dict[str, str],
        count: int,
    ) -> list[list[str]]:
        segment_names = repeated_or_default(form_values, "sname", count, "GAG")
        number_of_regions = repeated_or_default(form_values, "nregions", count, "1")
        regions = repeated_or_default(form_values, "residue_regions", count, "6-123")
        bases = repeated_or_default(form_values, "sbasis", count, "CA")
        segvariables = []
        for index in range(count):
            low, high = self._region_bounds(regions[index])
            segvariables.append(
                [
                    number_of_regions[index],
                    low,
                    high,
                    bases[index],
                    segment_names[index],
                ]
            )
        return segvariables

    def _region_bounds(self, value: str) -> tuple[str, str]:
        lows: list[str] = []
        highs: list[str] = []
        for item in split_repeated(value):
            if "-" not in item:
                raise ValueError("Residue regions must use low-high ranges.")
            low, high = [part.strip() for part in item.split("-", 1)]
            lows.append(low)
            highs.append(high)
        return ",".join(lows), ",".join(highs)
