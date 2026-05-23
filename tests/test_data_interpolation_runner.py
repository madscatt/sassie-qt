from pathlib import Path

import pytest

from sassie_qt.runners.data_interpolation_runner import (
    DataInterpolationInput,
    DataInterpolationRunner,
    _process_failure_message,
)


FIXTURE_DATA = Path(
    "/Users/curtisj/git_working_copies/genapp_zazzie/bin/local_data_for_testing/sans_data.sub"
)


def test_prepare_variables_converts_gui_values(tmp_path):
    runner = DataInterpolationRunner()

    variables = runner.prepare_variables(
        DataInterpolationInput(
            run_directory=tmp_path,
            run_name="run_0",
            data_file_name=FIXTURE_DATA,
            output_file_name="sans_data.dat",
            izero="0.04",
            izero_error="0.001",
            delta_q="0.02",
            maximum_points="16",
        )
    )

    assert variables["run_name"][0] == "run_0"
    assert variables["izero"][0] == 0.04
    assert variables["maximum_points"][0] == 16


def test_data_interpolation_runner_writes_outputs(tmp_path):
    messages = []
    progress = []

    result = DataInterpolationRunner().run(
        DataInterpolationInput(
            run_directory=tmp_path,
            run_name="run_0",
            data_file_name=FIXTURE_DATA,
            output_file_name="sans_data.dat",
            izero="0.04",
            izero_error="0.001",
            delta_q="0.02",
            maximum_points="16",
        ),
        message_callback=messages.append,
        progress_callback=progress.append,
    )

    assert result.output_file.exists()
    assert result.signal_to_noise_output_file.exists()
    assert result.plot_json_file.exists()
    assert progress[-1] == 1.0
    assert any("DATA INTERPOLATION IS DONE" in message for message in messages)


def test_data_interpolation_runner_rejects_empty_data_file(tmp_path):
    with pytest.raises(ValueError, match="Choose an experimental data file"):
        DataInterpolationRunner().run(
            DataInterpolationInput(
                run_directory=tmp_path,
                run_name="run_0",
                data_file_name=Path(""),
                output_file_name="sans_data.dat",
                izero="0.04",
                izero_error="0.001",
                delta_q="0.02",
                maximum_points="16",
            )
        )


def test_process_failure_message_includes_recent_log_lines():
    message = _process_failure_message(1, ["starting job\n", "last useful line\n"])

    assert "data_interpolation exited with status 1" in message
    assert "Recent run log:" in message
    assert "last useful line" in message
