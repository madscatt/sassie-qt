"""Shared helpers for running SASSIE modules from the Qt app."""

from __future__ import annotations

import locale
import multiprocessing
import os
import queue
import re
import shutil
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import sassie.interface.input_filter as input_filter

from sassie_qt.value_helpers import split_repeated


MessageCallback = Callable[[str], None]
ProgressCallback = Callable[[float], None]

_WORKING_DIRECTORY_LOCK = threading.RLock()
_RUN_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class ModuleRunResult:
    """Summary returned by a locally completed SASSIE module run."""

    module: str
    run_path: Path
    output_files: tuple[Path, ...] = ()


class SassieModuleRunner:
    """Base class for local runners that mirror gui_mimic/bin-driver flow."""

    module = ""
    variable_types: dict[str, str] = {}

    def run(
        self,
        project_directory: Path,
        form_values: dict[str, str],
        message_callback: MessageCallback | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> ModuleRunResult:
        message_callback = message_callback or _ignore_message
        progress_callback = progress_callback or _ignore_progress
        recent_messages: list[str] = []

        def record_message(message: str) -> None:
            recent_messages.append(str(message))
            del recent_messages[:-8]
            message_callback(str(message))

        project_directory = project_directory.expanduser().resolve()
        project_directory.mkdir(parents=True, exist_ok=True)

        with serialized_module_run():
            variables = self.prepare_variables(project_directory, form_values)
            self.validate_variables(variables, project_directory)

            run_name_variable = variables.get("run_name") or variables.get("runname")
            if not run_name_variable:
                raise KeyError("run_name")
            run_name = validate_run_name(run_name_variable[0])
            run_path = safe_run_path(project_directory, run_name, self.module)
            if run_path.exists():
                shutil.rmtree(run_path)

            record_message("starting job\n")
            progress_callback(0.01)

            with working_directory(project_directory):
                txt_queue = multiprocessing.JoinableQueue()
                sassie_module = self.create_sassie_module()
                process = multiprocessing.Process(
                    target=sassie_module.main,
                    args=self.sassie_main_args(variables, txt_queue),
                )
                process.start()
                self._drain_queue_while_running(
                    process,
                    txt_queue,
                    record_message,
                    progress_callback,
                )
                process.join(timeout=1.0)
                if process.exitcode not in (0, None):
                    raise RuntimeError(
                        process_failure_message(
                            self.module,
                            process.exitcode,
                            recent_messages,
                        )
                    )

            progress_callback(1.0)
            output_files = tuple(
                path for path in self.output_files(run_path, variables) if path.exists()
            )
            return ModuleRunResult(
                module=self.module,
                run_path=run_path,
                output_files=output_files,
            )

    def prepare_variables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict:
        svariables = {
            key: (value, self.variable_types[key])
            for key, value in self.form_to_svariables(project_directory, form_values).items()
        }
        errors, variables = input_filter.type_check_and_convert(svariables)
        if errors:
            raise ValueError("\n".join(str(error) for error in errors))
        return variables

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        raise NotImplementedError

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        raise NotImplementedError

    def create_sassie_module(self):
        raise NotImplementedError

    def sassie_main_args(
        self,
        variables: dict,
        txt_queue: multiprocessing.JoinableQueue,
    ) -> tuple:
        return (variables, txt_queue)

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        return ()

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
def working_directory(path: Path):
    with _WORKING_DIRECTORY_LOCK:
        previous_directory = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous_directory)


@contextmanager
def serialized_module_run():
    with _WORKING_DIRECTORY_LOCK:
        yield


def require_value(form_values: dict[str, str], field_id: str, label: str) -> str:
    value = form_values.get(field_id, "").strip()
    if not value:
        raise ValueError(f"Enter {label} before running.")
    return value


def require_existing_file(form_values: dict[str, str], field_id: str, label: str) -> str:
    value = require_value(form_values, field_id, label)
    file_path = Path(value).expanduser()
    if file_path.is_dir():
        raise ValueError(f"Choose {label}, not a directory.")
    if not file_path.exists():
        raise ValueError(f"{label} does not exist: {file_path}")
    return str(file_path)


def validate_run_name(run_name: str) -> str:
    value = str(run_name).strip()
    if not value:
        raise ValueError("Enter a run name before running.")
    if not _RUN_NAME_PATTERN.fullmatch(value):
        raise ValueError(
            "Run names may contain only letters, numbers, underscores, and hyphens."
        )
    return value


def safe_run_path(project_directory: Path, run_name: str, module: str) -> Path:
    validated_run_name = validate_run_name(run_name)
    run_path = (project_directory / validated_run_name / module).resolve()
    if not path_is_relative_to(run_path, project_directory):
        raise ValueError("Run path must stay inside the selected project directory.")
    return run_path


def safe_output_filename(value: str, label: str = "output filename") -> str:
    filename = str(value).strip()
    if not filename:
        raise ValueError(f"Enter {label} before running.")
    path = Path(filename).expanduser()
    if path.is_absolute():
        raise ValueError(f"{capitalized_label(label)} must be relative: {filename}")
    if filename.startswith("~"):
        raise ValueError(
            f"{capitalized_label(label)} must not use a home-directory shortcut."
        )
    if any(part in {"", ".", ".."} for part in Path(filename).parts):
        raise ValueError(f"{capitalized_label(label)} must not contain path traversal.")
    return filename


def safe_output_filenames(value: str, label: str = "output filename") -> str:
    filenames = split_repeated(value)
    if not filenames:
        raise ValueError(f"Enter {label} before running.")
    return ",".join(safe_output_filename(item, label) for item in filenames)


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def capitalized_label(label: str) -> str:
    return label[:1].upper() + label[1:]


def split_csv_values(value: str) -> list[str]:
    return split_repeated(value)


def _ignore_message(_message: str) -> None:
    return


def _ignore_progress(_progress: float) -> None:
    return


def process_failure_message(
    module: str,
    exitcode: int | None,
    recent_messages: list[str],
) -> str:
    message = f"{module} exited with status {exitcode}"
    recent_text = "".join(recent_messages).strip()
    if recent_text:
        message += "\n\nRecent run log:\n" + recent_text
    return message
