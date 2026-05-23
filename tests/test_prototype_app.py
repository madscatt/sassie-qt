import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QProgressBar

from sassie_qt.menu_loader import (
    DEFAULT_GENAPP_ZAZZIE_ROOT,
    DEFAULT_ZAZZIE_ROOT,
    load_menu,
)
from sassie_qt.prototype_app import SassieQtPrototype, configure_qt_plugin_paths


FIXTURE_DATA = (
    "/Users/curtisj/git_working_copies/genapp_zazzie/bin/local_data_for_testing/"
    "sans_data.sub"
)


def test_data_interpolation_page_exposes_bound_inputs_and_outputs():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    assert set(page.input_rows) == {
        "run_name",
        "data_file_name",
        "output_file_name",
        "izero",
        "izero_error",
        "delta_q",
        "maximum_points",
    }
    assert {"progress_output", "lineplot"} <= set(page.output_rows)
    assert "progress_html" not in page.output_rows
    assert page.run_log_text is not None
    page.input_rows["data_file_name"].set_value(FIXTURE_DATA)
    assert page._collect_data_interpolation_inputs().run_name == "run_0"
    app.processEvents()


def test_data_interpolation_uses_app_project_directory(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    window.set_project_directory(tmp_path)

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    page.input_rows["data_file_name"].set_value(FIXTURE_DATA)
    assert page._collect_data_interpolation_inputs().run_directory == tmp_path.resolve()
    assert window.project_directory_edit.text() == str(tmp_path.resolve())
    app.processEvents()


def test_file_inputs_copy_selected_files_into_project_directory(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )
    project_directory = tmp_path / "project"
    source_file = tmp_path / "source" / "sans_data.sub"
    source_file.parent.mkdir()
    source_file.write_text(Path(FIXTURE_DATA).read_text())

    window.set_project_directory(project_directory)

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    project_file = page.input_rows["data_file_name"]._copy_file_to_project_directory(
        source_file
    )

    assert project_file == project_directory / source_file.name
    assert project_file.exists()
    assert project_file.read_text() == source_file.read_text()
    page.input_rows["data_file_name"].set_value(str(project_file))
    assert page._collect_data_interpolation_inputs().data_file_name == project_file
    app.processEvents()


def test_sections_start_on_first_module_without_overview_tab():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    assert window.module_tabs.tabText(0) == "Align"
    assert "Overview" not in [
        window.module_tabs.tabText(index)
        for index in range(window.module_tabs.count())
    ]
    app.processEvents()


def test_progress_percentage_is_embedded_in_progress_bar():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    progress_bar = page.output_rows["progress_output"].value_widget
    assert isinstance(progress_bar, QProgressBar)
    page._set_progress(0.42)
    assert progress_bar.value() == 42
    assert progress_bar.text() == "42%"
    app.processEvents()


def test_data_interpolation_page_rejects_empty_data_file():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    page.input_rows["data_file_name"].reset_value()
    with pytest.raises(ValueError, match="Choose an experimental data file"):
        page._collect_data_interpolation_inputs()
    app.processEvents()
