"""Local runner for the SASSIE multi_component_analysis module."""

from __future__ import annotations

from pathlib import Path

import sassie.contrast.multi_component_analysis.multi_component_analysis as mca
import sassie.interface.multi_component_analysis.multi_component_analysis_filter as mca_filter

from sassie_qt.modules.base import SassieModuleRunner, require_value
from sassie_qt.modules.contrast_helpers import (
    bool_text,
    listbox_bool,
    repeated_files,
    repeated_or_default,
    required_run_name,
)


class MultiComponentAnalysisRunner(SassieModuleRunner):
    """Run multi_component_analysis from Qt form values."""

    module = "multi_component_analysis"
    variable_types = {
        "run_name": "string",
        "path": "string",
        "output_file_name": "string",
        "match_point_flag": "boolean",
        "stoichiometry_flag": "boolean",
        "stuhrmann_parallel_axis_flag": "boolean",
        "decomposition_flag": "boolean",
        "read_from_contrast_calculator_output_file": "boolean",
        "number_of_contrast_points": "int",
        "fraction_d2o": "float_array",
        "initial_match_point_guess_flag": "boolean",
        "initial_match_point_guess": "float",
        "concentration": "float_array",
        "concentration_error": "float_array",
        "izero": "float_array",
        "izero_error": "float_array",
        "initial_guess_stuhrmann": "float_array",
        "number_of_components": "int",
        "component_name": "string_array",
        "partial_specific_volume": "float_array",
        "molecular_weight": "float_array",
        "delta_rho": "nested_float_array",
        "radius_of_gyration": "float_array",
        "radius_of_gyration_error": "float_array",
        "data_file_name": "file_name_array",
        "q_rg_limit_guinier": "float",
        "starting_data_point_guinier": "int_array",
        "initial_points_to_use_guinier": "int_array",
        "refine_scale_factor_flag": "boolean",
        "verbose_output_flag": "boolean",
        "initial_guess_guinier": "float_array",
        "signal_to_noise_amplitude": "float_array",
        "random_seed": "int",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        method_code = form_values.get("multi_component_analysis_listbox", "c1")
        variables = {
            "run_name": required_run_name(form_values),
            "path": str(project_directory.expanduser().resolve()),
            "output_file_name": require_value(
                form_values,
                "output_file_name",
                "an output file name",
            ),
            "match_point_flag": str(method_code == "c1"),
            "stuhrmann_parallel_axis_flag": str(method_code == "c2"),
            "decomposition_flag": str(method_code == "c3"),
            "stoichiometry_flag": str(method_code == "c4"),
            "read_from_contrast_calculator_output_file": "false",
            "random_seed": form_values.get("random_seed", "123456"),
        }
        if method_code == "c2":
            variables.update(self._stuhrmann_values(form_values))
        elif method_code == "c3":
            variables.update(self._decomposition_values(form_values))
        elif method_code == "c4":
            variables.update(self._stoichiometry_values(form_values))
        else:
            variables.update(self._match_point_values(form_values))
        return variables

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = mca_filter.check_multi_component_analysis(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return mca.multi_component_analysis()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        if variables["match_point_flag"][0]:
            method_path = run_path / "match_point"
        elif variables["stuhrmann_parallel_axis_flag"][0]:
            method_path = run_path / "stuhrmann_parallel_axis"
        elif variables["decomposition_flag"][0]:
            method_path = run_path / "decomposition"
        else:
            method_path = run_path / "stoichiometry"
        return tuple(sorted(path for path in method_path.iterdir())) if method_path.exists() else ()

    def _match_point_values(self, form_values: dict[str, str]) -> dict[str, str]:
        count = int(form_values.get("number_of_contrast_points_match_point", "4"))
        values = {
            "number_of_contrast_points": str(count),
            "fraction_d2o": ",".join(
                repeated_or_default(
                    form_values,
                    "fraction_d2o_match_point",
                    count,
                    "0.0",
                )
            ),
            "concentration": ",".join(
                repeated_or_default(
                    form_values,
                    "concentration_match_point",
                    count,
                    "7.7",
                )
            ),
            "concentration_error": ",".join(
                repeated_or_default(
                    form_values,
                    "concentration_error_match_point",
                    count,
                    "0.4",
                )
            ),
            "izero": ",".join(
                repeated_or_default(form_values, "izero_match_point", count, "0.85")
            ),
            "izero_error": ",".join(
                repeated_or_default(
                    form_values,
                    "izero_error_match_point",
                    count,
                    "0.01",
                )
            ),
            "initial_match_point_guess_flag": bool_text(
                form_values.get("initial_match_point_guess_flag", "false")
            ),
        }
        if values["initial_match_point_guess_flag"] == "True":
            values["initial_match_point_guess"] = form_values.get(
                "initial_match_point_guess",
                "0.5",
            )
        return values

    def _stuhrmann_values(self, form_values: dict[str, str]) -> dict[str, str]:
        contrast_count = int(
            form_values.get("number_of_contrast_points_stuhrmann", "4")
        )
        component_count = int(form_values.get("number_of_components_stuhrmann", "2"))
        return {
            "number_of_contrast_points": str(contrast_count),
            "fraction_d2o": ",".join(
                repeated_or_default(
                    form_values,
                    "fraction_d2o_stuhrmann",
                    contrast_count,
                    "0.0",
                )
            ),
            "radius_of_gyration": ",".join(
                repeated_or_default(
                    form_values,
                    "radius_of_gyration",
                    contrast_count,
                    "25.45",
                )
            ),
            "radius_of_gyration_error": ",".join(
                repeated_or_default(
                    form_values,
                    "radius_of_gyration_error",
                    contrast_count,
                    "0.07",
                )
            ),
            "initial_guess_stuhrmann": form_values.get(
                "initial_stuhrmann_guess",
                "1.0, 1.0, 1.0",
            ),
            "number_of_components": str(component_count),
            "component_name": ",".join(
                repeated_or_default(
                    form_values,
                    "component_name_stuhrmann",
                    component_count,
                    "component",
                )
            ),
            "partial_specific_volume": ",".join(
                repeated_or_default(
                    form_values,
                    "partial_specific_volume_stuhrmann",
                    component_count,
                    "0.73",
                )
            ),
            "molecular_weight": ",".join(
                repeated_or_default(
                    form_values,
                    "molecular_weight_stuhrmann",
                    component_count,
                    "14.3",
                )
            ),
            "delta_rho": form_values.get(
                "delta_rho_sturhmann",
                "2.551,5.104;1.383,3.928;-2.415,0.109;-3.292,-0.773",
            ),
        }

    def _decomposition_values(self, form_values: dict[str, str]) -> dict[str, str]:
        contrast_count = int(
            form_values.get("number_of_contrast_points_decomposition", "4")
        )
        component_count = int(form_values.get("number_of_components_decomposition", "2"))
        data_files = repeated_files(
            form_values,
            "data_file_name_decomposition",
            contrast_count,
            "decomposition data file",
        )
        return {
            "number_of_contrast_points": str(contrast_count),
            "fraction_d2o": ",".join(
                repeated_or_default(
                    form_values,
                    "fraction_d2o_decomposition",
                    contrast_count,
                    "0.0",
                )
            ),
            "data_file_name": data_files,
            "concentration": ",".join(
                repeated_or_default(
                    form_values,
                    "concentration_decomposition",
                    contrast_count,
                    "7.7",
                )
            ),
            "concentration_error": ",".join(
                repeated_or_default(
                    form_values,
                    "concentration_error_decomposition",
                    contrast_count,
                    "0.4",
                )
            ),
            "number_of_components": str(component_count),
            "component_name": ",".join(
                repeated_or_default(
                    form_values,
                    "component_name_decomposition",
                    component_count,
                    "component",
                )
            ),
            "q_rg_limit_guinier": form_values.get("q_rg_limit_guinier", "1.3"),
            "starting_data_point_guinier": ",".join(
                repeated_or_default(
                    form_values,
                    "starting_data_point_guinier",
                    contrast_count,
                    "1",
                )
            ),
            "initial_points_to_use_guinier": ",".join(
                repeated_or_default(
                    form_values,
                    "initial_points_to_use_guinier",
                    contrast_count,
                    "6",
                )
            ),
            "refine_scale_factor_flag": listbox_bool(
                form_values.get("refine_scale_factor_flag", "c1")
            ),
            "verbose_output_flag": bool_text(
                form_values.get("verbose_output_flag", "false")
            ),
            "initial_guess_guinier": form_values.get(
                "initial_guess_guinier",
                "1.0, 1.0",
            ),
            "signal_to_noise_amplitude": form_values.get(
                "signal_to_noise_amplitude",
                "50.0, 50.0, 50.0, 50.0",
            ),
            "partial_specific_volume": ",".join(
                repeated_or_default(
                    form_values,
                    "partial_specific_volume_decomposition",
                    component_count,
                    "0.73",
                )
            ),
            "molecular_weight": ",".join(
                repeated_or_default(
                    form_values,
                    "molecular_weight_decomposition",
                    component_count,
                    "14.3",
                )
            ),
            "delta_rho": form_values.get(
                "delta_rho_decomposition",
                "2.551,5.104;1.383,3.928;-2.415,0.109;-3.292,-0.773",
            ),
        }

    def _stoichiometry_values(self, form_values: dict[str, str]) -> dict[str, str]:
        contrast_count = int(
            form_values.get("number_of_contrast_points_stoichiometry", "3")
        )
        component_count = int(form_values.get("number_of_components_stoichiometry", "2"))
        return {
            "number_of_contrast_points": str(contrast_count),
            "fraction_d2o": ",".join(
                repeated_or_default(
                    form_values,
                    "fraction_d2o_stoichiometry",
                    contrast_count,
                    "0.99",
                )
            ),
            "concentration": ",".join(
                repeated_or_default(
                    form_values,
                    "concentration_stoichiometry",
                    contrast_count,
                    "3.1",
                )
            ),
            "concentration_error": ",".join(
                repeated_or_default(
                    form_values,
                    "concentration_error_stoichiometry",
                    contrast_count,
                    "0.18",
                )
            ),
            "izero": ",".join(
                repeated_or_default(
                    form_values,
                    "izero_stoichiometry",
                    contrast_count,
                    "8.1",
                )
            ),
            "izero_error": ",".join(
                repeated_or_default(
                    form_values,
                    "izero_error_stoichiometry",
                    contrast_count,
                    "0.2",
                )
            ),
            "number_of_components": str(component_count),
            "component_name": ",".join(
                repeated_or_default(
                    form_values,
                    "component_name_stoichiometry",
                    component_count,
                    "component",
                )
            ),
            "partial_specific_volume": ",".join(
                repeated_or_default(
                    form_values,
                    "partial_specific_volume_stoichiometry",
                    component_count,
                    "0.745",
                )
            ),
            "delta_rho": form_values.get(
                "delta_rho_stoichiometry",
                "-3.2,-5.7;1.6,0.26;0.031,-1.74",
            ),
        }
