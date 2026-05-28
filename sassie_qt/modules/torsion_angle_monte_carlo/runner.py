"""Local runner for the SASSIE torsion_angle_monte_carlo module."""

from __future__ import annotations

from pathlib import Path

import sassie.interface.torsion_angle_monte_carlo.torsion_angle_monte_carlo_filter as tamc_filter
import sassie.simulate.torsion_angle_monte_carlo.monte_carlo as tamc_module

from sassie_qt.modules.base import SassieModuleRunner, require_existing_file, require_value
from sassie_qt.modules.simulate_helpers import (
    boolean_flag,
    join_repeated_codes,
    map_overlap_basis,
)


ROTATION_TYPE_BY_CODE = {
    "c1": "protein_backbone_torsion",
    "c2": "single_stranded_nucleic_backbone_torsion",
    "c3": "double_stranded_nucleic_torsion",
    "c4": "isopeptide_bond_torsion",
}
ROTATION_DIRECTION_BY_CODE = {"c1": "forward", "c2": "reverse"}


class TorsionAngleMonteCarloRunner(SassieModuleRunner):
    """Run torsion_angle_monte_carlo from Qt form values."""

    module = "torsion_angle_monte_carlo"
    variable_types = {
        "run_name": "string",
        "dcdfile": "string",
        "pdbfile": "string",
        "psffile": "string",
        "psf_flag": "boolean",
        "max_steps": "int",
        "energy_convergence": "float",
        "step_size": "float",
        "number_of_flexible_regions": "int",
        "basis_string_array": "string_array",
        "delta_theta_array": "float_array",
        "rotation_type_array": "string_array",
        "rotation_direction_array": "string_array",
        "overlap_basis": "string",
        "post_basis_string_array": "string_array",
        "temperature": "float",
        "trial_steps": "int",
        "goback": "int",
        "directed_mc": "float",
        "low_rg_cutoff": "float",
        "high_rg_cutoff": "float",
        "z_flag": "boolean",
        "z_cutoff": "float",
        "constraint_flag": "boolean",
        "constraint_file": "string",
        "use_fast_rotate_dihedral": "boolean",
        "nonbondflag": "int",
        "seed": "int_array",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        constraint_flag = boolean_flag(form_values, "cflag_check_box")
        constraint_file = (
            require_existing_file(form_values, "constraint_file", "the constraint file")
            if constraint_flag == "True"
            else ""
        )
        return {
            "run_name": require_value(form_values, "run_name", "a run name"),
            "dcdfile": require_value(form_values, "dcdfile", "an output DCD name"),
            "pdbfile": require_existing_file(form_values, "pdbfile", "the PDB file"),
            "psffile": require_existing_file(form_values, "psffile", "the PSF file"),
            "psf_flag": "true",
            "max_steps": form_values.get("max_steps", "5000"),
            "energy_convergence": form_values.get("energy_convergence", "1.0"),
            "step_size": form_values.get("step_size", "0.002"),
            "number_of_flexible_regions": form_values.get(
                "number_of_flexible_regions",
                "1",
            ),
            "basis_string_array": form_values.get(
                "basis_string_array",
                "resid >= 3 and resid < 5",
            ),
            "delta_theta_array": form_values.get("delta_theta_array", "30.0"),
            "rotation_type_array": join_repeated_codes(
                form_values,
                "rotation_type_array",
                ROTATION_TYPE_BY_CODE,
                "c1",
            ),
            "rotation_direction_array": join_repeated_codes(
                form_values,
                "rotation_direction_array",
                ROTATION_DIRECTION_BY_CODE,
                "c1",
            ),
            "overlap_basis": map_overlap_basis(form_values),
            "post_basis_string_array": form_values.get(
                "post_basis_string_array",
                "resid>=5 and resid<=10",
            ),
            "temperature": form_values.get("temperature", "300.0"),
            "trial_steps": form_values.get("trial_steps", "100"),
            "goback": form_values.get("goback", "1"),
            "directed_mc": form_values.get("directed_mc", "0"),
            "low_rg_cutoff": form_values.get("low_rg_cutoff", "0.0"),
            "high_rg_cutoff": form_values.get("high_rg_cutoff", "400.0"),
            "z_flag": boolean_flag(form_values, "zflag_check_box"),
            "z_cutoff": form_values.get("z_cutoff", "0.0"),
            "constraint_flag": constraint_flag,
            "constraint_file": constraint_file,
            "use_fast_rotate_dihedral": "false",
            "nonbondflag": "0",
            "seed": "0,123",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = tamc_filter.check_torsion_angle_monte_carlo(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return tamc_module.simulation()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        dcd_file = run_path / variables["dcdfile"][0]
        return (
            dcd_file,
            dcd_file.with_name(dcd_file.name + ".stats"),
            dcd_file.with_name(dcd_file.name + ".all_rg_results_data.txt"),
            dcd_file.with_name(dcd_file.name + ".accepted_rg_results_data.txt"),
        )
