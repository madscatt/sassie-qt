"""Compatibility facade for the SASSIE data_interpolation runner.

The implementation lives in ``sassie_qt.modules.data_interpolation.runner`` so
the Qt app and direct tests use the same validation and run path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sassie_qt.modules.base import (
    ModuleRunResult,
    process_failure_message,
)
from sassie_qt.modules.data_interpolation.runner import (
    DataInterpolationRunner as ModuleDataInterpolationRunner,
)


MessageCallback = Callable[[str], None]
ProgressCallback = Callable[[float], None]


@dataclass(frozen=True)
class DataInterpolationInput:
    """Desktop inputs needed to run SASSIE data_interpolation."""

    run_directory: Path
    run_name: str
    data_file_name: Path
    output_file_name: str
    izero: str
    izero_error: str
    delta_q: str
    maximum_points: str


@dataclass(frozen=True)
class DataInterpolationResult:
    """Files produced by a completed data_interpolation run."""

    run_path: Path
    output_file: Path
    signal_to_noise_output_file: Path
    plot_json_file: Path


class DataInterpolationRunner:
    """Legacy dataclass-input adapter around the common module runner."""

    module = "data_interpolation"

    def __init__(self) -> None:
        self._runner = ModuleDataInterpolationRunner()

    def run(
        self,
        inputs: DataInterpolationInput,
        message_callback: MessageCallback | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> DataInterpolationResult:
        result = self._runner.run(
            inputs.run_directory,
            _input_to_form_values(inputs),
            message_callback=message_callback,
            progress_callback=progress_callback,
        )
        return _result_from_module_result(result, inputs.output_file_name)

    def prepare_variables(self, inputs: DataInterpolationInput) -> dict:
        return self._runner.prepare_variables(
            inputs.run_directory,
            _input_to_form_values(inputs),
        )

    def validate_variables(self, variables: dict) -> None:
        self._runner.validate_variables(variables, Path.cwd())


def _input_to_form_values(inputs: DataInterpolationInput) -> dict[str, str]:
    return {
        "run_name": inputs.run_name,
        "data_file_name": str(inputs.data_file_name),
        "output_file_name": inputs.output_file_name,
        "izero": inputs.izero,
        "izero_error": inputs.izero_error,
        "delta_q": inputs.delta_q,
        "maximum_points": inputs.maximum_points,
    }


def _result_from_module_result(
    result: ModuleRunResult,
    output_file_name: str,
) -> DataInterpolationResult:
    return DataInterpolationResult(
        run_path=result.run_path,
        output_file=result.run_path / output_file_name,
        signal_to_noise_output_file=result.run_path / f"stn_{output_file_name}",
        plot_json_file=result.run_path / f"{output_file_name[:-3]}json",
    )


def _process_failure_message(exitcode: int | None, recent_messages: list[str]) -> str:
    return process_failure_message("data_interpolation", exitcode, recent_messages)
