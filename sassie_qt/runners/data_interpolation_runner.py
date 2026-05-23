"""Local runner for the SASSIE data_interpolation module."""

from __future__ import annotations

import locale
import multiprocessing
import os
import queue
import shutil
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import sassie.interface.data_interpolation.data_interpolation_filter as data_interpolation_filter
import sassie.interface.input_filter as input_filter
import sassie.tools.data_interpolation.data_interpolation as data_interpolation


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
    """Run data_interpolation in the style of gui_mimic/bin-driver locally."""

    module = "data_interpolation"

    def run(
        self,
        inputs: DataInterpolationInput,
        message_callback: MessageCallback | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> DataInterpolationResult:
        message_callback = message_callback or _ignore_message
        progress_callback = progress_callback or _ignore_progress

        self.validate_desktop_inputs(inputs)
        variables = self.prepare_variables(inputs)
        self.validate_variables(variables)

        run_directory = inputs.run_directory.expanduser().resolve()
        run_directory.mkdir(parents=True, exist_ok=True)
        run_name = variables["run_name"][0]
        run_path = run_directory / run_name / self.module
        if run_path.exists():
            shutil.rmtree(run_path)

        message_callback("starting job\n")
        progress_callback(0.01)

        with _working_directory(run_directory):
            txt_queue = multiprocessing.JoinableQueue()
            data_interpolation_object = data_interpolation.data_interpolation()
            process = multiprocessing.Process(
                target=data_interpolation_object.main,
                args=(variables, txt_queue),
            )
            process.start()
            self._drain_queue_while_running(
                process,
                txt_queue,
                message_callback,
                progress_callback,
            )
            process.join(timeout=1.0)
            if process.exitcode not in (0, None):
                raise RuntimeError(
                    f"data_interpolation exited with status {process.exitcode}"
                )

        progress_callback(1.0)
        return DataInterpolationResult(
            run_path=run_path,
            output_file=run_path / inputs.output_file_name,
            signal_to_noise_output_file=run_path / f"stn_{inputs.output_file_name}",
            plot_json_file=run_path / f"{inputs.output_file_name[:-3]}json",
        )

    def validate_desktop_inputs(self, inputs: DataInterpolationInput) -> None:
        """Catch local desktop path mistakes before SASSIE filters run."""

        if not str(inputs.run_directory).strip():
            raise ValueError("Choose a run directory before running.")
        if not inputs.run_name.strip():
            raise ValueError("Enter a run name before running.")
        if not str(inputs.data_file_name).strip():
            raise ValueError("Choose an experimental data file before running.")
        if not inputs.output_file_name.strip():
            raise ValueError("Enter an output file name before running.")

        data_file_path = inputs.data_file_name.expanduser()
        if data_file_path.is_dir():
            raise ValueError("Choose an experimental data file, not a directory.")
        if not data_file_path.exists():
            raise ValueError(f"Experimental data file does not exist: {data_file_path}")

    def prepare_variables(self, inputs: DataInterpolationInput) -> dict:
        """Build SASSIE typed variables, matching gui_mimic conventions."""

        svariables = {
            "run_name": (inputs.run_name, "string"),
            "data_file_name": (str(inputs.data_file_name.expanduser()), "string"),
            "output_file_name": (inputs.output_file_name, "string"),
            "izero": (inputs.izero, "float"),
            "izero_error": (inputs.izero_error, "float"),
            "delta_q": (inputs.delta_q, "float"),
            "maximum_points": (inputs.maximum_points, "int"),
        }

        errors, variables = input_filter.type_check_and_convert(svariables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))
        return variables

    def validate_variables(self, variables: dict) -> None:
        """Run the module-specific SASSIE input filter."""

        errors = data_interpolation_filter.check_data_interpolation(variables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))

    def _drain_queue_while_running(
        self,
        process: multiprocessing.Process,
        txt_queue: multiprocessing.JoinableQueue,
        message_callback: MessageCallback,
        progress_callback: ProgressCallback,
    ) -> None:
        while process.is_alive():
            self._drain_available_messages(txt_queue, message_callback, progress_callback)
            time.sleep(0.1)

        process.join(timeout=1.0)
        self._drain_available_messages(txt_queue, message_callback, progress_callback)
        drain_deadline = time.time() + 1.0
        while time.time() < drain_deadline:
            if not self._drain_available_messages(
                txt_queue,
                message_callback,
                progress_callback,
            ):
                break
            time.sleep(0.05)

    def _drain_available_messages(
        self,
        txt_queue: multiprocessing.JoinableQueue,
        message_callback: MessageCallback,
        progress_callback: ProgressCallback,
    ) -> bool:
        drained_message = False
        while True:
            try:
                message = txt_queue.get_nowait()
            except queue.Empty:
                break
            drained_message = True
            self._handle_queue_message(message, message_callback, progress_callback)
        return drained_message

    def _handle_queue_message(
        self,
        message: str,
        message_callback: MessageCallback,
        progress_callback: ProgressCallback,
    ) -> None:
        text_split = str(message).split()
        if text_split and text_split[0] == "STATUS":
            progress_callback(locale.atof(text_split[1]))
        else:
            message_callback(str(message))


@contextmanager
def _working_directory(path: Path):
    previous_directory = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous_directory)


def _ignore_message(_message: str) -> None:
    return


def _ignore_progress(_progress: float) -> None:
    return
