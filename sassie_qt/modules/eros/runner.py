"""Local runner for the SASSIE eros module."""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path

import sassie.analyze.eros.eros as eros
import sassie.interface.eros.eros_filter as eros_filter

from sassie_qt.modules.analyze_helpers import collect_output_files
from sassie_qt.modules.base import SassieModuleRunner, require_existing_file
from sassie_qt.modules.contrast_helpers import required_run_name


class ErosRunner(SassieModuleRunner):
    """Run eros from Qt form values."""

    module = "eros"
    variable_types = {
        "run_name": "string",
        "iq_data_path": "string",
        "goal_iq_data_file": "string",
        "io": "float",
        "seed": "int_array",
        "number_of_files_to_use": "int",
        "number_of_monte_carlo_steps": "int",
        "weight_step_size_fraction": "float",
        "theta": "float",
        "beta": "float",
        "reduced_x2": "int",
        "matplotlib_plot_flag": "boolean",
    }

    def __init__(self) -> None:
        self.iq_data_path = ""

    def prepare_variables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict:
        self.iq_data_path = self._prepare_iq_data_path(project_directory, form_values)
        return super().prepare_variables(project_directory, form_values)

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": required_run_name(form_values),
            "iq_data_path": self.iq_data_path,
            "goal_iq_data_file": require_existing_file(
                form_values,
                "goal_iq_data_file",
                "a target I(q) file",
            ),
            "io": form_values.get("io", "1.0"),
            "seed": form_values.get("seed", "1,123"),
            "number_of_files_to_use": form_values.get("number_of_files_to_use", "5"),
            "number_of_monte_carlo_steps": form_values.get(
                "number_of_monte_carlo_steps",
                "50",
            ),
            "weight_step_size_fraction": form_values.get(
                "weight_step_size_fraction",
                "0.1",
            ),
            "theta": form_values.get("theta", "0.0"),
            "beta": form_values.get("beta", "100.0"),
            "reduced_x2": self._reduced_x2_value(
                form_values.get("reduced_x2_list_box", "c1"),
            ),
            "matplotlib_plot_flag": "False",
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        errors = eros_filter.check_eros(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def create_sassie_module(self):
        return eros.eros()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return collect_output_files(run_path)

    def _prepare_iq_data_path(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> str:
        value = form_values.get("iq_data_archive", "").strip()
        if not value:
            raise ValueError("Choose an I(q) data archive before running.")
        source = Path(value).expanduser()
        if source.is_dir():
            return str(source)
        if not source.exists():
            raise ValueError(f"I(q) data archive does not exist: {source}")
        extract_root = project_directory / "_sassie_qt_inputs" / "eros_iq_profiles"
        if extract_root.exists():
            shutil.rmtree(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)
        with tarfile.open(source) as archive:
            self._extract_archive_safely(archive, extract_root)
        spectra_path = extract_root / "spectra"
        if spectra_path.exists():
            return str(spectra_path)
        return str(extract_root)

    def _reduced_x2_value(self, code: str) -> str:
        return {"c1": "1", "c2": "0", "c3": "2", "c4": "3"}.get(code, "1")

    def _extract_archive_safely(
        self,
        archive: tarfile.TarFile,
        extract_root: Path,
    ) -> None:
        root = extract_root.resolve()
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if root != target and root not in target.parents:
                raise ValueError(f"Archive member escapes extraction path: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"Archive links are not supported: {member.name}")
        archive.extractall(root)
