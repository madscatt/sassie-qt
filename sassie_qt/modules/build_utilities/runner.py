"""Local runner for the SASSIE build_utilities module."""

from __future__ import annotations

from pathlib import Path

import sassie.build.build_utilities.build_utilities as build_utilities
import sassie.interface.build_utilities.build_utilities_filter as build_filter

from sassie_qt.modules.base import (
    SassieModuleRunner,
    require_existing_file,
    require_value,
    safe_output_filename,
    safe_output_filenames,
)


CONSTRAINT_OPTION_BY_CODE = {
    "c1": "heavy",
    "c2": "protein",
    "c3": "nucleic",
    "c4": "backbone",
    "c5": "solute",
}
CONSTRAINT_FIELD_BY_CODE = {"c1": "occupancy", "c2": "beta"}
FIELD_BY_CODE = {
    "c1": "record",
    "c2": "index",
    "c3": "name",
    "c4": "altloc",
    "c5": "resname",
    "c6": "chain",
    "c7": "resid",
    "c8": "icode",
    "c9": "xcoor",
    "c10": "ycoor",
    "c11": "zcoor",
    "c12": "occupancy",
    "c13": "beta",
    "c14": "segname",
    "c15": "element",
    "c16": "charge",
}
ORDER_BY_CODE = {
    "c1": "xyz",
    "c2": "xzy",
    "c3": "yxz",
    "c4": "yzx",
    "c5": "zxy",
    "c6": "zyx",
}
PMI_EIGENVECTOR_BY_CODE = {"c1": "0", "c2": "1", "c3": "2"}
ALIGNMENT_AXIS_BY_CODE = {"c1": "x", "c2": "y", "c3": "z", "c4": "user_vector_2"}
FASTA_MOLTYPE_BY_CODE = {"c1": "protein", "c2": "nucleic"}


class BuildUtilitiesRunner(SassieModuleRunner):
    """Run build_utilities from Qt form values."""

    module = "build_utilities"
    variable_types = {
        "run_name": "string",
        "input_pdbfile": "string",
        "pdb_utilities_flag": "boolean",
        "renumber_flag": "boolean",
        "renumber_output_filename": "string",
        "renumber_indices_flag": "boolean",
        "first_index": "int",
        "renumber_resids_flag": "boolean",
        "first_resid": "int",
        "pdb_constraints_flag": "boolean",
        "number_of_constraint_files": "int",
        "constraint_options": "string",
        "constraint_filenames": "string",
        "constraint_fields": "string",
        "constraint_resets": "string",
        "modify_fields_flag": "boolean",
        "modify_fields_output_filename": "string",
        "number_of_fields_to_modify": "int",
        "field_selections": "string",
        "field_options": "string",
        "field_values": "string",
        "split_pdb_flag": "boolean",
        "number_of_split_regions": "int",
        "split_basis_string_array": "string",
        "split_output_filename_array": "string",
        "overlap_check_flag": "boolean",
        "overlap_basis": "string",
        "overlap_cutoff": "float",
        "fasta_export_flag": "boolean",
        "fasta_export_basis_string": "string",
        "fasta_export_output_filename": "string",
        "fasta_export_comment": "string",
        "translation_rotation_flag": "boolean",
        "translation_rotation_output_filename": "string",
        "pre_center_flag": "boolean",
        "translation_array": "float_array",
        "rotation_flag": "boolean",
        "rotation_type": "string",
        "user_vector_1": "string",
        "rotation_axes_order": "string",
        "rotation_theta": "float_array",
        "align_pmi_output_filename": "string",
        "align_pmi_on_cardinal_axes_flag": "boolean",
        "align_pmi_on_axis_flag": "boolean",
        "pmi_eigenvector": "int",
        "alignment_vector_axis": "string",
        "user_vector_2": "string",
        "settle_on_surface_flag": "boolean",
        "surface_plane": "string",
        "invert_along_axis_flag": "boolean",
        "fasta_utilities_flag": "boolean",
        "fasta_output_filename": "string",
        "fasta_input_option": "string",
        "fasta_input_sequence": "string",
        "fasta_input_file": "string",
        "fasta_moltype": "string",
        "seed": "int_array",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        utility_code = form_values.get("build_utilities_listbox", "c1")
        pdb_utilities = utility_code == "c1"
        pdb_choice = form_values.get("pdb_choices_listbox", "c1")
        fasta_choice = form_values.get("fasta_listbox", "c1")
        rotation_code = form_values.get("rotation_axes_listbox", "c1")
        pmi_code = form_values.get("pmi_listbox", "c1")

        variables = self._defaults()
        variables.update(
            {
                "run_name": require_value(form_values, "run_name", "a run name"),
                "pdb_utilities_flag": str(pdb_utilities),
                "fasta_utilities_flag": str(not pdb_utilities),
            }
        )

        if pdb_utilities:
            variables.update(
                {
                    "input_pdbfile": require_existing_file(
                        form_values,
                        "input_pdbfile",
                        "the input PDB file",
                    ),
                    "renumber_flag": str(pdb_choice == "c1"),
                    "pdb_constraints_flag": str(pdb_choice == "c2"),
                    "modify_fields_flag": str(pdb_choice == "c3"),
                    "translation_rotation_flag": str(pdb_choice == "c4"),
                    "align_pmi_on_axis_flag": str(pdb_choice == "c5" and pmi_code == "c1"),
                    "align_pmi_on_cardinal_axes_flag": str(
                        pdb_choice == "c5" and pmi_code == "c2"
                    ),
                    "split_pdb_flag": str(pdb_choice == "c6"),
                    "overlap_check_flag": str(pdb_choice == "c7"),
                    "fasta_export_flag": str(pdb_choice == "c8"),
                    "renumber_output_filename": safe_output_filename(
                        form_values.get("renumber_output_filename", "")
                        or "renumbered.pdb",
                        "renumber output filename",
                    ),
                    "renumber_indices_flag": form_values.get(
                        "renumber_index_checkbox",
                        "false",
                    ),
                    "first_index": form_values.get("first_index", "1"),
                    "renumber_resids_flag": form_values.get(
                        "renumber_resid_checkbox",
                        "false",
                    ),
                    "first_resid": form_values.get("first_resid", "1"),
                    "number_of_constraint_files": form_values.get(
                        "number_of_constraint_files",
                        "1",
                    ),
                    "constraint_options": _map_csv(
                        form_values.get("constraint_listbox", "c1"),
                        CONSTRAINT_OPTION_BY_CODE,
                    ),
                    "constraint_fields": _map_csv(
                        form_values.get("constraint_field_listbox", "c1"),
                        CONSTRAINT_FIELD_BY_CODE,
                    ),
                    "constraint_resets": _checkbox_csv(
                        form_values.get("reset_checkbox", "true")
                    ),
                    "constraint_filenames": safe_output_filenames(
                        form_values.get("constraint_pdb_files", "")
                        or "constrained.pdb",
                        "constraint output filename",
                    ),
                    "modify_fields_output_filename": safe_output_filename(
                        form_values.get("modify_fields_output_filename", "")
                        or "modified_fields.pdb",
                        "modify-fields output filename",
                    ),
                    "number_of_fields_to_modify": form_values.get(
                        "number_of_fields_to_modify",
                        "1",
                    ),
                    "field_selections": form_values.get("field_selections", "index < 10"),
                    "field_options": _map_csv(
                        form_values.get("field_listbox", "c13"),
                        FIELD_BY_CODE,
                    ),
                    "field_values": form_values.get("field_values", "1.00"),
                    "translation_rotation_output_filename": safe_output_filename(
                        form_values.get("translation_rotation_output_filename", "")
                        or "transformed.pdb",
                        "translation/rotation output filename",
                    ),
                    "pre_center_flag": form_values.get("center_checkbox", "false"),
                    "translation_array": ",".join(
                        [
                            form_values.get("delta_x", "0"),
                            form_values.get("delta_y", "0"),
                            form_values.get("delta_z", "0"),
                        ]
                    ),
                    "rotation_flag": str(rotation_code in {"c2", "c3"}),
                    "rotation_type": (
                        "user_vector" if rotation_code == "c3" else "cardinal"
                    ),
                    "rotation_axes_order": ORDER_BY_CODE.get(
                        form_values.get(
                            "rotation_axes_order_2"
                            if rotation_code == "c3"
                            else "rotation_axes_order_1",
                            "c1",
                        ),
                        "xyz",
                    ),
                    "rotation_theta": _rotation_theta(rotation_code, form_values),
                    "user_vector_1": form_values.get("user_vector_1", "0.0, 0.0, 1.0"),
                    "align_pmi_output_filename": safe_output_filename(
                        form_values.get("align_pmi_output_filename", "")
                        or "aligned_pmi.pdb",
                        "PMI alignment output filename",
                    ),
                    "pmi_eigenvector": PMI_EIGENVECTOR_BY_CODE.get(
                        form_values.get("pmi_eigenvector", "c1"),
                        "0",
                    ),
                    "alignment_vector_axis": ALIGNMENT_AXIS_BY_CODE.get(
                        form_values.get("alignment_vector", "c1"),
                        "x",
                    ),
                    "user_vector_2": form_values.get("user_vector_2", "0.0, 0.0, 1.0"),
                    "settle_on_surface_flag": form_values.get(
                        "surface_checkbox",
                        "false",
                    ),
                    "surface_plane": form_values.get("surface_plane_cutoff", "z"),
                    "invert_along_axis_flag": form_values.get(
                        "invert_checkbox",
                        "false",
                    ),
                    "number_of_split_regions": form_values.get(
                        "number_of_split_regions",
                        "1",
                    ),
                    "split_basis_string_array": form_values.get(
                        "split_basis_string_array",
                        "index < 100",
                    ),
                    "split_output_filename_array": safe_output_filenames(
                        form_values.get("split_output_filename_array", "")
                        or "split_region.pdb",
                        "split output filename",
                    ),
                    "overlap_basis": form_values.get("overlap_basis", "heavy"),
                    "overlap_cutoff": form_values.get("overlap_cutoff", "0.8"),
                    "fasta_export_basis_string": form_values.get(
                        "fasta_export_basis_string",
                        "index < 100",
                    ),
                    "fasta_export_output_filename": safe_output_filename(
                        form_values.get("fasta_export_output_filename", "")
                        or "sequence_from_pdb.fasta",
                        "FASTA export output filename",
                    ),
                    "fasta_export_comment": form_values.get(
                        "fasta_export_comment",
                        "selected PDB sequence",
                    ),
                }
            )
        else:
            variables.update(
                {
                    "fasta_output_filename": safe_output_filename(
                        form_values.get("fasta_output_filename", "")
                        or "sequence_from_fasta.pdb",
                        "FASTA output filename",
                    ),
                    "fasta_input_option": (
                        "file" if fasta_choice == "c2" else "sequence"
                    ),
                    "fasta_input_sequence": form_values.get(
                        "fasta_input_sequence",
                        "RRAGMPSCYLK",
                    ),
                    "fasta_input_file": (
                        require_existing_file(
                            form_values,
                            "fasta_input_file",
                            "the FASTA input file",
                        )
                        if fasta_choice == "c2"
                        else form_values.get("fasta_input_file", "")
                    ),
                    "fasta_moltype": FASTA_MOLTYPE_BY_CODE.get(
                        form_values.get("fasta_moltype_listbox", "c1"),
                        "protein",
                    ),
                }
            )

        return variables

    def _defaults(self) -> dict[str, str]:
        return {
            "run_name": "run_0",
            "input_pdbfile": "",
            "pdb_utilities_flag": "true",
            "renumber_flag": "false",
            "renumber_output_filename": "renumbered.pdb",
            "renumber_indices_flag": "false",
            "first_index": "1",
            "renumber_resids_flag": "false",
            "first_resid": "1",
            "pdb_constraints_flag": "false",
            "number_of_constraint_files": "1",
            "constraint_options": "heavy",
            "constraint_filenames": "constrained.pdb",
            "constraint_fields": "beta",
            "constraint_resets": "True",
            "modify_fields_flag": "false",
            "modify_fields_output_filename": "modified_fields.pdb",
            "number_of_fields_to_modify": "1",
            "field_selections": "index < 10",
            "field_options": "beta",
            "field_values": "1.00",
            "split_pdb_flag": "false",
            "number_of_split_regions": "1",
            "split_basis_string_array": "index < 100",
            "split_output_filename_array": "split_region.pdb",
            "overlap_check_flag": "false",
            "overlap_basis": "heavy",
            "overlap_cutoff": "0.8",
            "fasta_export_flag": "false",
            "fasta_export_basis_string": "index < 100",
            "fasta_export_output_filename": "sequence_from_pdb.fasta",
            "fasta_export_comment": "selected PDB sequence",
            "translation_rotation_flag": "false",
            "translation_rotation_output_filename": "transformed.pdb",
            "pre_center_flag": "false",
            "translation_array": "0,0,0",
            "rotation_flag": "false",
            "rotation_type": "cardinal",
            "user_vector_1": "0.0, 0.0, 1.0",
            "rotation_axes_order": "xyz",
            "rotation_theta": "0,0,0",
            "align_pmi_output_filename": "aligned_pmi.pdb",
            "align_pmi_on_cardinal_axes_flag": "false",
            "align_pmi_on_axis_flag": "false",
            "pmi_eigenvector": "0",
            "alignment_vector_axis": "x",
            "user_vector_2": "0.0, 0.0, 1.0",
            "settle_on_surface_flag": "false",
            "surface_plane": "z",
            "invert_along_axis_flag": "false",
            "fasta_utilities_flag": "false",
            "fasta_output_filename": "sequence_from_fasta.pdb",
            "fasta_input_option": "sequence",
            "fasta_input_sequence": "RRAGMPSCYLK",
            "fasta_input_file": "",
            "fasta_moltype": "protein",
            "seed": "0,123",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = build_filter.check_build_utilities(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return build_utilities.build_utilities()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        names = []
        if variables["pdb_utilities_flag"][0]:
            names = _pdb_output_names(variables)
        else:
            names = [variables["fasta_output_filename"][0]]
        return tuple(run_path / name for name in names)


def _map_csv(value: str, mapping: dict[str, str]) -> str:
    return ",".join(mapping.get(item.strip(), item.strip()) for item in value.split(","))


def _checkbox_csv(value: str) -> str:
    return ",".join(
        "True" if item.strip().lower() == "true" else "False"
        for item in value.split(",")
    )


def _rotation_theta(rotation_code: str, form_values: dict[str, str]) -> str:
    if rotation_code == "c3":
        return ",".join(
            [
                form_values.get("user_vector_theta_x", "0"),
                form_values.get("user_vector_theta_y", "0"),
                form_values.get("user_vector_theta_z", "0"),
            ]
        )
    return ",".join(
        [
            form_values.get("cardinal_theta_x", "0"),
            form_values.get("cardinal_theta_y", "0"),
            form_values.get("cardinal_theta_z", "0"),
        ]
    )


def _pdb_output_names(variables: dict) -> list[str]:
    if variables["renumber_flag"][0]:
        return [variables["renumber_output_filename"][0]]
    if variables["pdb_constraints_flag"][0]:
        return [item.strip() for item in variables["constraint_filenames"][0].split(",")]
    if variables["modify_fields_flag"][0]:
        return [variables["modify_fields_output_filename"][0]]
    if variables["split_pdb_flag"][0]:
        return [
            item.strip()
            for item in variables["split_output_filename_array"][0].split(",")
        ]
    if variables["fasta_export_flag"][0]:
        return [variables["fasta_export_output_filename"][0]]
    if variables["translation_rotation_flag"][0]:
        return [variables["translation_rotation_output_filename"][0]]
    if variables["align_pmi_on_axis_flag"][0] or variables[
        "align_pmi_on_cardinal_axes_flag"
    ][0]:
        return [variables["align_pmi_output_filename"][0]]
    return []
