"""Local runner for the SASSIE prody module."""

from __future__ import annotations

from pathlib import Path

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value


class ProdyRunner(SassieModuleRunner):
    """Run prody from Qt form values."""

    module = "prody"
    variable_types = {
        "run_name": "string",
        "pdbfile": "string",
        "number_modes": "int",
        "number_conformations_samp": "int",
        "number_steps_traverse": "int",
        "rmsd_conformations_samp": "float",
        "rmsd_traverse": "float",
        "advanced_usage": "int",
        "advanced_usage_cmd": "string",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        advanced_usage = (
            "1" if form_values.get("advanced_input", "false").lower() == "true" else "0"
        )
        return {
            "run_name": require_value(form_values, "run_name", "a run name"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "the PDB file"),
            "number_modes": form_values.get("number_modes", "5"),
            "number_conformations_samp": form_values.get(
                "number_conformations_samp",
                "50",
            ),
            "number_steps_traverse": form_values.get(
                "number_steps_traverse",
                "10",
            ),
            "rmsd_conformations_samp": form_values.get(
                "rmsd_conformations_samp",
                "1.0",
            ),
            "rmsd_traverse": form_values.get("rmsd_traverse", "1.5"),
            "advanced_usage": advanced_usage,
            "advanced_usage_cmd": form_values.get("advanced_usage_cmd", " "),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        import sassie.interface.prody.prody_filter as prody_filter

        errors = prody_filter.check_prody(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        try:
            import sassie.simulate.prody.prody_anm as prody_module
        except ModuleNotFoundError as error:
            if error.name == "prody":
                raise RuntimeError(
                    "ProDy is not installed in this Python environment. "
                    "Install prody before running this module."
                ) from error
            raise
        return prody_module.prody_anm()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return (
            run_path / "prody_anm_extended.pdb",
            run_path / "prody_anm_traverse.dcd",
            run_path / "prody_anm_samples.dcd",
        )
