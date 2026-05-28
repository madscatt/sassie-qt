"""Local runner for the SASSIE bayesian_ensemble_estimator module."""

from __future__ import annotations

from pathlib import Path

import sassie.analyze.bayesian_ensemble_estimator.bayesian_ensemble_estimator as bees
import sassie.interface.bayesian_ensemble_estimator.bayesian_ensemble_estimator_filter as bees_filter

from sassie_qt.modules.analyze_helpers import collect_output_files
from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.contrast_helpers import bool_text


class BayesianEnsembleEstimatorRunner(SassieModuleRunner):
    """Run bayesian_ensemble_estimator from Qt form values."""

    module = "bayesian_ensemble_estimator"
    variable_types = {
        "runname": "string",
        "sas_data": "string",
        "theoretical_profiles_zip": "string",
        "posterior_burn": "int",
        "max_iterations": "int",
        "number_of_MCs": "int",
        "nproc": "int",
        "d_max": "float",
        "auxiliary_data": "string",
        "use_all": "boolean",
        "use_bic": "boolean",
        "sigma": "float",
        "zeroing_threshold": "float",
        "random_seed": "int",
        "walk_one": "boolean",
        "every": "boolean",
        "shansamp": "boolean",
        "plot_backend": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        has_auxiliary_data = (
            bool_text(form_values.get("use_auxiliary_data_checkbox", "false")) == "True"
        )
        return {
            "runname": require_value(form_values, "runname", "a run name"),
            "sas_data": require_existing_file(form_values, "sas_data", "a SAS data file"),
            "theoretical_profiles_zip": require_existing_file(
                form_values,
                "theoretical_profiles_zip",
                "a theoretical profiles zip file",
            ),
            "posterior_burn": form_values.get("posterior_burn", "1"),
            "max_iterations": form_values.get("max_iterations", "10"),
            "number_of_MCs": form_values.get("number_of_MCs", "1"),
            "nproc": form_values.get("nproc", "1"),
            "d_max": form_values.get("d_max", "83.6"),
            "auxiliary_data": (
                require_existing_file(form_values, "auxiliary_data", "an auxiliary data file")
                if has_auxiliary_data
                else ""
            ),
            "use_all": bool_text(form_values.get("use_all_checkbox", "false")),
            "use_bic": bool_text(form_values.get("ic_list_box", "c1") == "c1"),
            "sigma": form_values.get("sigma", "0.10"),
            "zeroing_threshold": form_values.get("zeroing_threshold", "0.00"),
            "random_seed": form_values.get("random_seed", "12345"),
            "walk_one": bool_text(form_values.get("walk_one", "false")),
            "every": bool_text(form_values.get("every_checkbox", "false")),
            "shansamp": bool_text(form_values.get("use_shansamp_checkbox", "true")),
            "plot_backend": "data",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = bees_filter.check_bayesian_ensemble_estimator(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return bees.ensemble_routine()

    def sassie_main_args(self, variables: dict, txt_queue) -> tuple:
        return (variables, txt_queue, {})

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)
