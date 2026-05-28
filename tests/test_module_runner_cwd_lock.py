from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from sassie_qt.modules.base import SassieModuleRunner
from sassie_qt.modules.base import serialized_module_run
from sassie_qt.modules.data_interpolation.runner import (
    DataInterpolationRunner as ModuleDataInterpolationRunner,
)
from sassie_qt.runners.data_interpolation_runner import DataInterpolationInput
from sassie_qt.runners.data_interpolation_runner import DataInterpolationRunner


class _NoOpSassieModule:
    def main(self, variables, txt_queue):
        txt_queue.put("STATUS 1.0\n")


class _WriteMarkerSassieModule:
    def main(self, variables, txt_queue):
        run_name = variables["run_name"][0]
        label = variables["label"][0]
        output_directory = Path.cwd() / run_name / "output_collection_probe"
        output_directory.mkdir(parents=True, exist_ok=True)
        (output_directory / "marker.txt").write_text(label)
        txt_queue.put("STATUS 1.0\n")


@dataclass
class _CwdProbeState:
    barrier: threading.Barrier
    lock: threading.Lock = field(default_factory=threading.Lock)
    active_sections: int = 0
    entered_directories: list[Path] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


class _CwdProbeRunner(SassieModuleRunner):
    module = "cwd_probe"
    variable_types = {"run_name": "string"}

    def __init__(self, state: _CwdProbeState):
        self.state = state

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {"run_name": form_values["run_name"]}

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        return None

    def create_sassie_module(self):
        return _NoOpSassieModule()

    def sassie_main_args(self, variables: dict, txt_queue):
        current_directory = Path.cwd()
        with self.state.lock:
            self.state.active_sections += 1
            self.state.entered_directories.append(current_directory)
            if self.state.active_sections != 1:
                self.state.failures.append("cwd critical sections overlapped")

        try:
            time.sleep(0.2)
            if Path.cwd() != current_directory:
                self.state.failures.append(
                    f"cwd changed during run setup: {current_directory} -> {Path.cwd()}"
                )
        finally:
            with self.state.lock:
                self.state.active_sections -= 1

        return super().sassie_main_args(variables, txt_queue)


@dataclass
class _OutputCollectionProbeState:
    output_started: threading.Event = field(default_factory=threading.Event)
    output_can_finish: threading.Event = field(default_factory=threading.Event)
    failures: list[str] = field(default_factory=list)


class _OutputCollectionProbeRunner(SassieModuleRunner):
    module = "output_collection_probe"
    variable_types = {"run_name": "string", "label": "string"}

    def __init__(self, state: _OutputCollectionProbeState):
        self.state = state

    def form_to_svariables(
        self,
        project_directory: Path,
        form_values: dict[str, str],
    ) -> dict[str, str]:
        return {
            "run_name": form_values["run_name"],
            "label": form_values["label"],
        }

    def validate_variables(self, variables: dict, project_directory: Path) -> None:
        return None

    def create_sassie_module(self):
        return _WriteMarkerSassieModule()

    def output_files(self, run_path: Path, variables: dict) -> tuple[Path, ...]:
        expected_label = variables["label"][0]
        marker = run_path / "marker.txt"
        if expected_label == "first":
            self.state.output_started.set()
            self.state.output_can_finish.wait(timeout=5)
        if not marker.exists():
            self.state.failures.append("run output disappeared during output collection")
        elif marker.read_text() != expected_label:
            self.state.failures.append("run output was replaced during output collection")
        return (marker,)


def test_module_runs_serialize_process_wide_cwd_changes(tmp_path):
    original_directory = Path.cwd()
    project_a = tmp_path / "project_a"
    project_b = tmp_path / "project_b"
    state = _CwdProbeState(barrier=threading.Barrier(2))
    errors: list[BaseException] = []

    def run_probe(project_directory: Path) -> None:
        try:
            state.barrier.wait(timeout=5)
            _CwdProbeRunner(state).run(project_directory, {"run_name": "run_0"})
        except BaseException as error:
            errors.append(error)

    threads = [
        threading.Thread(target=run_probe, args=(project_a,)),
        threading.Thread(target=run_probe, args=(project_b,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert not any(thread.is_alive() for thread in threads)
    assert errors == []
    assert state.failures == []
    assert set(state.entered_directories) == {project_a.resolve(), project_b.resolve()}
    assert Path.cwd() == original_directory


def test_duplicate_run_cleanup_waits_for_output_collection(tmp_path):
    state = _OutputCollectionProbeState()
    project_directory = tmp_path / "project"
    errors: list[BaseException] = []

    def run_probe(label: str) -> None:
        try:
            _OutputCollectionProbeRunner(state).run(
                project_directory,
                {"run_name": "run_0", "label": label},
            )
        except BaseException as error:
            errors.append(error)

    first_thread = threading.Thread(target=run_probe, args=("first",))
    first_thread.start()
    assert state.output_started.wait(timeout=5)

    second_thread = threading.Thread(target=run_probe, args=("second",))
    second_thread.start()
    time.sleep(0.2)
    state.output_can_finish.set()

    first_thread.join(timeout=10)
    second_thread.join(timeout=10)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert errors == []
    assert state.failures == []


def test_data_interpolation_runner_uses_shared_run_lock(tmp_path, monkeypatch):
    input_file = tmp_path / "input.dat"
    input_file.write_text("0.01 1.0 0.1\n0.02 0.9 0.1\n")
    messages: list[str] = []
    lock_entered = threading.Event()
    release_lock = threading.Event()
    errors: list[BaseException] = []

    monkeypatch.setattr(
        ModuleDataInterpolationRunner,
        "validate_variables",
        lambda self, variables, project_directory: None,
    )
    monkeypatch.setattr(
        ModuleDataInterpolationRunner,
        "create_sassie_module",
        lambda self: _NoOpSassieModule(),
    )

    inputs = DataInterpolationInput(
        run_directory=tmp_path / "project",
        run_name="run_0",
        data_file_name=input_file,
        output_file_name="output.dat",
        izero="1.0",
        izero_error="0.1",
        delta_q="0.01",
        maximum_points="3",
    )

    def hold_shared_lock() -> None:
        with serialized_module_run():
            lock_entered.set()
            release_lock.wait(timeout=5)

    def run_data_interpolation() -> None:
        try:
            DataInterpolationRunner().run(inputs, message_callback=messages.append)
        except BaseException as error:
            errors.append(error)

    lock_thread = threading.Thread(target=hold_shared_lock)
    lock_thread.start()
    assert lock_entered.wait(timeout=5)

    runner_thread = threading.Thread(target=run_data_interpolation)
    runner_thread.start()
    time.sleep(0.2)

    assert runner_thread.is_alive()
    assert messages == []

    release_lock.set()
    lock_thread.join(timeout=10)
    runner_thread.join(timeout=10)

    assert not lock_thread.is_alive()
    assert not runner_thread.is_alive()
    assert errors == []
    assert messages == ["starting job\n"]
