"""Local runner for the SASSIE contrast_calculator module."""

from __future__ import annotations

from pathlib import Path

import sassie.contrast.contrast_calculator.contrast_calculator as contrast_calculator
import sassie.interface.contrast_calculator.contrast_calculator_filter as contrast_filter
import sassie.interface.input_filter as input_filter

from sassie_qt.modules.base import SassieModuleRunner, require_value
from sassie_qt.modules.contrast_helpers import (
    listbox_bool,
    project_path_text,
    repeated_files,
    repeated_or_default,
    required_run_name,
)


MOLECULE_TYPE_BY_CODE = {"c1": "dna", "c2": "rna", "c3": "protein"}


class ContrastCalculatorRunner(SassieModuleRunner):
    """Run contrast_calculator from Qt form values."""

    module = "contrast_calculator"
    variable_types = {
        "run_name": "string",
        "path": "string",
        "output_file_name": "string",
        "number_of_input_files": "int",
        "solute_concentration": "float",
        "d2o_step": "int",
        "number_of_solvent_components": "int",
        "protein_exchange_fraction": "float",
        "nucleic_acid_exchange_fraction": "float",
        "number_of_additional_solute_components": "int",
    }

    def __init__(self) -> None:
        self.ivariables: list[list[str]] = []
        self.solvvariables: list[list[str]] = []
        self.chemvariables: list[list[str]] = []

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": required_run_name(form_values),
            "path": project_path_text(project_directory),
            "output_file_name": require_value(
                form_values,
                "output_file_name",
                "an output filename prefix",
            ),
            "number_of_input_files": form_values.get("number_of_input_files", "0"),
            "solute_concentration": form_values.get("solute_concentration", "1.0"),
            "d2o_step": form_values.get("d2o_step", "5"),
            "number_of_solvent_components": form_values.get(
                "number_of_solvent_components",
                "0",
            ),
            "protein_exchange_fraction": form_values.get(
                "protein_exchange_fraction",
                "0.95",
            ),
            "nucleic_acid_exchange_fraction": form_values.get(
                "nucleic_acid_exchange_fraction",
                "1.0",
            ),
            "number_of_additional_solute_components": form_values.get(
                "number_of_additional_solute_components",
                "0",
            ),
        }

    def prepare_variables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict:
        variables = super().prepare_variables(project_directory, form_values)
        self.ivariables = self._input_file_variables(form_values, variables)
        self.solvvariables = self._solvent_variables(form_values, variables)
        self.chemvariables = self._additional_solute_variables(form_values, variables)
        return variables

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = []
        errors.extend(
            contrast_filter.check_number_of_input_files(
                variables["number_of_input_files"][0],
            )
        )
        errors.extend(
            contrast_filter.check_number_of_solvent_components(
                variables["number_of_solvent_components"][0],
            )
        )
        errors.extend(
            contrast_filter.check_number_of_additional_solute_components(
                variables["number_of_additional_solute_components"][0],
            )
        )
        if not errors:
            errors.extend(contrast_filter.check_contrast(variables))
        if not errors and self.ivariables:
            errors.extend(contrast_filter.check_ivariables(project_path_text(project_directory), self.ivariables))
        if not errors and self.solvvariables:
            errors.extend(contrast_filter.check_solvvariables(self.solvvariables))
        if not errors and self.chemvariables:
            errors.extend(contrast_filter.check_chemvariables(self.chemvariables))
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return contrast_calculator.contrast_calculator()

    def sassie_main_args(self, variables: dict, txt_queue) -> tuple:
        return (
            variables,
            self.ivariables,
            self.solvvariables,
            self.chemvariables,
            txt_queue,
        )

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        prefix = Path(variables["output_file_name"][0]).stem
        return (
            run_path / f"{prefix}_general.txt",
            run_path / f"{prefix}_sld.txt",
            run_path / f"{prefix}_contrast.txt",
            run_path / f"{prefix}_izero.txt",
            run_path / f"{prefix}_general.txt.json",
        )

    def _input_file_variables(
        self,
        form_values: dict[str, str],
        variables: dict,
    ) -> list[list[str]]:
        count = variables["number_of_input_files"][0]
        if count <= 0:
            return []
        input_file_names = repeated_files(
            form_values,
            "input_file_names",
            count,
            "input file",
        )
        number_of_units = repeated_or_default(
            form_values,
            "number_of_units",
            count,
            "1",
        )
        fraction_deuterated = repeated_or_default(
            form_values,
            "fraction_deuterated",
            count,
            "0.0",
        )
        molecule_types = [
            MOLECULE_TYPE_BY_CODE.get(item, item)
            for item in repeated_or_default(
                form_values,
                "molecule_type",
                count,
                "c3",
            )
        ]
        is_fasta = [
            "1" if listbox_bool(item, true_code="c2") == "True" else "0"
            for item in repeated_or_default(form_values, "is_fasta", count, "c2")
        ]
        return [
            [
                input_file_names[index],
                number_of_units[index],
                fraction_deuterated[index],
                molecule_types[index],
                is_fasta[index],
            ]
            for index in range(count)
        ]

    def _solvent_variables(
        self,
        form_values: dict[str, str],
        variables: dict,
    ) -> list[list[str]]:
        count = variables["number_of_solvent_components"][0]
        if count <= 0:
            return []
        formulas = repeated_or_default(
            form_values,
            "solvent_component_formula",
            count,
            "NaCl",
        )
        errors, converted_formulas = input_filter.check_and_convert_formula(formulas)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))
        concentrations = repeated_or_default(
            form_values,
            "solvent_component_concentration",
            count,
            "0.15",
        )
        mass_densities = repeated_or_default(
            form_values,
            "solvent_component_mass_density",
            count,
            "2.16",
        )
        return [
            [converted_formulas[index], concentrations[index], mass_densities[index]]
            for index in range(count)
        ]

    def _additional_solute_variables(
        self,
        form_values: dict[str, str],
        variables: dict,
    ) -> list[list[str]]:
        count = variables["number_of_additional_solute_components"][0]
        if count <= 0:
            return []
        formulas = repeated_or_default(
            form_values,
            "additional_solute_formula",
            count,
            "(C42H82NO8P)130",
        )
        errors, converted_formulas = input_filter.check_and_convert_formula(formulas)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))
        exchangeable_hydrogens = repeated_or_default(
            form_values,
            "number_of_exchangeable_hydrogens",
            count,
            "0",
        )
        exchange_fractions = repeated_or_default(
            form_values,
            "fraction_of_exchangeable_hydrogens",
            count,
            "0.0",
        )
        mass_densities = repeated_or_default(
            form_values,
            "additional_solute_mass_density",
            count,
            "1.0",
        )
        return [
            [
                converted_formulas[index],
                exchangeable_hydrogens[index],
                exchange_fractions[index],
                mass_densities[index],
            ]
            for index in range(count)
        ]
