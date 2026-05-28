"""Local runner for the SASSIE chi_square_filter module."""

from __future__ import annotations

from pathlib import Path

import sassie.analyze.chi_square_filter.chi_square_filter as chi_square_filter
import sassie.interface.chi_square_filter.chi_square_filter_filter as chi_filter

from sassie_qt.modules.analyze_helpers import collect_output_files
from sassie_qt.modules.base import SassieModuleRunner
from sassie_qt.modules.contrast_helpers import (
    bool_text,
    repeated_files,
    repeated_or_default,
    required_run_name,
    split_repeated,
)


class ChiSquareFilterRunner(SassieModuleRunner):
    """Run chi_square_filter from Qt form values."""

    module = "chi_square_filter"
    variable_types = {
        "run_name": "string",
        "saspaths": "string",
        "sasintfiles": "file_name_array",
        "io": "float_array",
        "number_of_weight_files": "nested_int_array",
        "basis_string": "nested_string_array",
        "weight_file_names": "nested_string_array",
        "sastype": "int",
        "reduced_x2": "int",
        "number_of_contrast_points": "int",
        "fraction_d2o": "float_array",
        "path": "string",
        "global_weight_file_flag": "boolean",
    }

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str | list[str]]:
        contrast_count = int(form_values.get("number_of_contrast_points", "1"))
        return {
            "run_name": required_run_name(form_values),
            "saspaths": ",".join(self._required_paths(form_values, contrast_count)),
            "sasintfiles": repeated_files(
                form_values,
                "sasintfiles",
                contrast_count,
                "interpolated data file",
            ),
            "io": ",".join(repeated_or_default(form_values, "io", contrast_count, "1.0")),
            "number_of_weight_files": self._nested_weight_counts(
                form_values,
                contrast_count,
            ),
            "basis_string": self._nested_text(form_values, "basis_string", contrast_count),
            "weight_file_names": self._nested_text(
                form_values,
                "weight_file_names",
                contrast_count,
            ),
            "sastype": self._sastype_value(form_values.get("sastype_list_box", "c0")),
            "reduced_x2": self._reduced_x2_value(
                form_values.get("reduced_x2_list_box", "c1"),
            ),
            "number_of_contrast_points": str(contrast_count),
            "fraction_d2o": ",".join(
                repeated_or_default(form_values, "fraction_d2o", contrast_count, "0.0"),
            ),
            "path": str(project_directory.expanduser().resolve()) + "/",
            "global_weight_file_flag": bool_text(
                form_values.get("global_weight_file_flag", "false"),
            ),
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = chi_filter.check_chi_square_filter(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return chi_square_filter.chi_square_filter()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)

    def _required_paths(
        self,
        form_values: dict[str, str],
        count: int,
    ) -> list[str]:
        values = split_repeated(form_values.get("saspaths", ""))
        if len(values) < count:
            raise ValueError(f"Choose {count} SAS data paths.")
        paths = []
        for index, value in enumerate(values[:count], start=1):
            path = Path(value).expanduser()
            if not path.exists():
                raise ValueError(f"SAS data path {index} does not exist: {path}")
            if not path.is_dir():
                raise ValueError(f"SAS data path {index} is not a directory: {path}")
            paths.append(str(path))
        return paths

    def _nested_weight_counts(
        self,
        form_values: dict[str, str],
        contrast_count: int,
    ) -> str:
        raw_value = form_values.get("number_of_weight_files", "").strip()
        if ";" in raw_value:
            return raw_value
        values = repeated_or_default(
            form_values,
            "number_of_weight_files",
            contrast_count,
            "0",
        )
        return ";".join(values)

    def _nested_text(
        self,
        form_values: dict[str, str],
        field_id: str,
        contrast_count: int,
    ) -> str:
        raw_value = form_values.get(field_id, "").strip()
        if ";" in raw_value:
            return raw_value
        if not raw_value:
            return ";".join("" for _ in range(contrast_count))
        return raw_value

    def _sastype_value(self, code: str) -> str:
        return {"c0": "0", "c1": "1", "c2": "2", "c3": "3"}.get(code, "0")

    def _reduced_x2_value(self, code: str) -> str:
        return {"c1": "1", "c2": "0", "c3": "2", "c4": "3"}.get(code, "1")
