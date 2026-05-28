"""Local runner for the SASSIE contrast_variation_analysis module."""

from __future__ import annotations

from pathlib import Path

import sassie.contrast.contrast_variation_analysis.contrast_variation_analysis as cva
import sassie.interface.contrast_variation_analysis.contrast_variation_analysis_filter as cva_filter

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file
from sassie_qt.modules.contrast_helpers import (
    bool_text,
    optional_existing_file,
    repeated_files,
    repeated_or_default,
    required_run_name,
)


class ContrastVariationAnalysisRunner(SassieModuleRunner):
    """Run contrast_variation_analysis from Qt form values."""

    module = "contrast_variation_analysis"
    variable_types = {
        "run_name": "string",
        "sascalc_hdf5_file": "string",
        "contrast_points_file": "string",
        "experimental_data_files": "file_name_array",
        "experimental_sources": "string",
        "d2o_percentages": "float_array",
        "intensity_mode": "string",
        "scale_mode": "string",
        "contrast_weights": "float_array",
        "fit_ensemble_flag": "boolean",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict:
        count = int(form_values.get("number_of_contrast_points", "2"))
        contrast_points_file = optional_existing_file(
            form_values,
            "contrast_points_file",
            "the contrast-point table",
        )
        experimental_data_files = []
        if not contrast_points_file:
            experimental_data_files = repeated_files(
                form_values,
                "experimental_data_files",
                count,
                "experimental data file",
            )
        return {
            "run_name": required_run_name(form_values),
            "sascalc_hdf5_file": require_existing_file(
                form_values,
                "sascalc_hdf5_file",
                "the SasCalc HDF5 file",
            ),
            "contrast_points_file": contrast_points_file,
            "experimental_data_files": experimental_data_files,
            "experimental_sources": ",".join(
                repeated_or_default(
                    form_values,
                    "experimental_sources",
                    count,
                    "neutron",
                )
            ),
            "d2o_percentages": ",".join(
                repeated_or_default(form_values, "d2o_percentages", count, "0.0")
            ),
            "intensity_mode": form_values.get("intensity_mode", "normalized"),
            "scale_mode": form_values.get("scale_mode", "none"),
            "contrast_weights": ",".join(
                repeated_or_default(form_values, "contrast_weights", count, "1.0")
            ),
            "fit_ensemble_flag": bool_text(
                form_values.get("fit_ensemble_flag", "false")
            ),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = cva_filter.check_contrast_variation_analysis(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return cva.contrast_variation_analysis()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        names = [
            "cva_global_scores.txt",
            "cva_per_contrast_scores.txt",
            "cva_best_profiles.txt",
            "cva_fit_warnings.txt",
            "cva_fit_summary.json",
            "cva_report.txt",
            "cva_plotly.json",
        ]
        if variables.get("fit_ensemble_flag", (False, "boolean"))[0]:
            names.extend(["cva_ensemble_weights.txt", "cva_ensemble_profiles.txt"])
        return tuple(run_path / name for name in names)
