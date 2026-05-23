import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton

from sassie_qt.menu_loader import (
    DEFAULT_GENAPP_ZAZZIE_ROOT,
    DEFAULT_ZAZZIE_ROOT,
    load_menu,
)
from sassie_qt.plotting.data_interpolation_plot import build_data_interpolation_figure
from sassie_qt.prototype_app import (
    DataInterpolationPlotWidget,
    SassieQtPrototype,
    configure_qt_plugin_paths,
    default_project_directory,
)


FIXTURE_DATA = (
    "/Users/curtisj/git_working_copies/genapp_zazzie/bin/local_data_for_testing/"
    "sans_data.sub"
)


def test_default_project_directory_matches_sassie_web_name(tmp_path):
    assert default_project_directory(tmp_path) == (
        tmp_path / "no_project_specified"
    ).resolve()


def test_app_creates_default_project_directory(tmp_path, monkeypatch):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    monkeypatch.chdir(tmp_path)

    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    expected_project_directory = tmp_path / "no_project_specified"
    assert window.project_directory == expected_project_directory.resolve()
    assert expected_project_directory.is_dir()
    assert window.project_directory_edit.text() == str(
        expected_project_directory.resolve()
    )
    app.processEvents()


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
    assert "progress_output" in page.output_rows
    assert "lineplot" not in page.output_rows
    assert "lineplot" in page.plot_widgets
    assert "progress_html" not in page.output_rows
    assert page.run_log_text is not None
    assert page.run_log_text.objectName() == "runLogText"
    assert page.run_log_text.document().documentMargin() == 4
    assert page.run_log_text.minimumHeight() == 340
    run_name_row = page.input_rows["run_name"]
    assert "results will be placed" in run_name_row.toolTip()
    assert "\nNote that only alphanumeric" in run_name_row.value_widget.toolTip()
    data_file_row = page.input_rows["data_file_name"]
    assert data_file_row.toolTip() == "data file should have three columns: q, I(q), and error"
    assert data_file_row.value_widget.toolTip() == data_file_row.toolTip()
    assert data_file_row.findChild(QPushButton, "fieldHelpButton") is None
    browse_button = next(
        button
        for button in data_file_row.findChildren(QPushButton)
        if button.text() == "Browse"
    )
    assert browse_button is not None
    assert browse_button.toolTip() == data_file_row.toolTip()
    assert [
        page.view_tabs.tabText(index)
        for index in range(page.view_tabs.count())
    ] == ["Input", "Output", "Plots"]
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

    project_directory = tmp_path / "created_project"
    window.set_project_directory(project_directory)

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    page.input_rows["data_file_name"].set_value(FIXTURE_DATA)
    assert (
        page._collect_data_interpolation_inputs().run_directory
        == project_directory.resolve()
    )
    assert project_directory.is_dir()
    assert window.project_directory_edit.text() == str(project_directory.resolve())
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
    project_directory.mkdir()
    source_file.parent.mkdir()
    source_file.write_text(Path(FIXTURE_DATA).read_text())

    window.set_project_directory(project_directory)

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    row = page.input_rows["data_file_name"]
    assert row._file_dialog_start_directory() == str(project_directory.resolve())

    project_file = page.input_rows["data_file_name"]._copy_file_to_project_directory(
        source_file
    )

    assert project_file == project_directory / source_file.name
    assert project_file.exists()
    assert project_file.read_text() == source_file.read_text()
    row.file_source_directory_recorder(source_file)
    row.set_value(str(project_file))
    assert row._file_dialog_start_directory(row.value()) == str(
        source_file.parent.resolve()
    )
    assert page._collect_data_interpolation_inputs().data_file_name == project_file
    app.processEvents()


def test_remembered_file_directory_survives_module_tab_rebuild(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )
    project_directory = tmp_path / "project"
    remembered_directory = tmp_path / "source"
    project_directory.mkdir()
    remembered_directory.mkdir()
    source_file = remembered_directory / "sans_data.sub"
    source_file.write_text(Path(FIXTURE_DATA).read_text())

    window.set_project_directory(project_directory)

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    page.input_rows["data_file_name"].file_source_directory_recorder(source_file)

    window.category_list.setCurrentRow(1)
    window.category_list.setCurrentRow(0)

    rebuilt_page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            rebuilt_page = window.module_tabs.widget(index)
            break

    assert rebuilt_page is not None
    assert rebuilt_page.input_rows["data_file_name"]._file_dialog_start_directory() == (
        str(remembered_directory.resolve())
    )
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


def test_data_interpolation_plotly_figure_loads_in_plots_tab(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )
    plot_data_file = tmp_path / "sans_data.json"
    plot_data_file.write_text(
        """
        {
          "q": [0.0, 0.02],
          "iq": [0.04, 0.03],
          "iq_error": [0.001, 0.0015],
          "original_q": [0.0, 0.02],
          "original_iq": [0.04, 0.03],
          "original_iq_error": [0.001, 0.0015],
          "signal_to_noise_cutoff_value": 0.02
        }
        """
    )

    page = None
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == "Data Interpolation":
            page = window.module_tabs.widget(index)
            break

    assert page is not None
    figure = build_data_interpolation_figure(plot_data_file)
    assert figure["data"][0]["name"] == "original data"
    assert figure["layout"]["title"]["text"] == "Data Interpolation Plot"

    page._set_data_interpolation_plot(plot_data_file)
    assert page.plot_widgets["lineplot"].plot_data_file == plot_data_file
    assert page.plot_widgets["lineplot"].plot_data["q"] == [0.0, 0.02]
    page._show_plots_tab()
    assert page.view_tabs.tabText(page.view_tabs.currentIndex()) == "Plots"
    app.processEvents()


def test_native_plot_widget_exports_plotly_html(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    plot_data_file = tmp_path / "sans_data.json"
    plot_data_file.write_text(
        """
        {
          "q": [0.0, 0.02],
          "iq": [0.04, 0.03],
          "iq_error": [0.001, 0.0015],
          "original_q": [0.0, 0.02],
          "original_iq": [0.04, 0.03],
          "original_iq_error": [0.001, 0.0015],
          "signal_to_noise_cutoff_value": 0.02
        }
        """
    )
    widget = DataInterpolationPlotWidget()

    assert widget.maximumHeight() == 455
    assert not widget.export_plotly_button.isEnabled()
    assert not widget.save_png_button.isEnabled()
    assert not widget.reset_view_button.isEnabled()
    assert widget.plot_data is None
    assert widget.pan_button.isChecked()
    assert not widget.box_zoom_button.isChecked()
    assert widget.plot_help_box.findChild(QLabel, "plotHelpText") is not None
    assert "Box Zoom" in widget.plot_help_box.findChild(
        QLabel,
        "plotHelpText",
    ).text()

    widget.set_box_zoom_mode()
    assert widget.box_zoom_button.isChecked()
    assert not widget.pan_button.isChecked()
    widget.set_pan_mode()
    assert widget.pan_button.isChecked()
    assert not widget.box_zoom_button.isChecked()

    widget.set_plot_data(plot_data_file)
    assert widget.plot_data["q"] == [0.0, 0.02]
    assert widget.canvas.plot_data["q"] == [0.0, 0.02]
    bottom_axis = widget.canvas.plot_item.getAxis("bottom")
    assert bottom_axis.labelText == "q (1/Å)"
    assert bottom_axis.autoSIPrefix is False
    assert bottom_axis.style["maxTextLevel"] == 0
    assert bottom_axis.style["tickTextWidth"] == 70
    tick_values = [
        -1.30103,
        -1.22185,
        -1.1549,
        -1.09691,
        -1.04576,
        -1.0,
        -0.69897,
    ]
    assert bottom_axis.tickStrings(tick_values, 1, 0.01) == [
        "0.05",
        "",
        "",
        "",
        "",
        "0.1",
        "0.2",
    ]
    assert widget.export_plotly_button.isEnabled()
    assert widget.save_png_button.isEnabled()
    assert widget.reset_view_button.isEnabled()

    html_file = widget.export_plotly_html(show_message=False)
    assert html_file == tmp_path / "sans_data_plotly.html"
    assert html_file.exists()
    assert "Plotly.newPlot" in html_file.read_text()
    app.processEvents()


def test_native_plot_widget_saves_png(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    plot_data_file = tmp_path / "sans_data.json"
    plot_data_file.write_text(
        """
        {
          "q": [0.01, 0.02, 0.04],
          "iq": [0.04, 0.03, 0.01],
          "iq_error": [0.001, 0.0015, 0.002],
          "original_q": [0.01, 0.02, 0.04],
          "original_iq": [0.041, 0.029, 0.011],
          "original_iq_error": [0.001, 0.0015, 0.002],
          "signal_to_noise_cutoff_value": 0.03
        }
        """
    )
    widget = DataInterpolationPlotWidget()
    widget.resize(900, 520)
    widget.show()
    widget.set_plot_data(plot_data_file)
    app.processEvents()

    png_file = widget.save_png(show_dialog=False)

    assert png_file == tmp_path / "sans_data_plot.png"
    assert png_file.exists()
    assert png_file.stat().st_size > 0
    app.processEvents()


def test_native_plot_clips_nonpositive_error_bars_without_tiny_log_range(tmp_path):
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    plot_data_file = tmp_path / "sans_data.json"
    plot_data_file.write_text(
        """
        {
          "q": [0.01, 0.02, 0.04],
          "iq": [0.04, 0.003, 0.001],
          "iq_error": [0.001, 0.0015, 0.01],
          "original_q": [0.01, 0.02, 0.04],
          "original_iq": [0.041, 0.0029, 0.0011],
          "original_iq_error": [0.001, 0.0015, 0.01],
          "signal_to_noise_cutoff_value": 0.03
        }
        """
    )
    widget = DataInterpolationPlotWidget()
    widget.set_plot_data(plot_data_file)

    assert widget.canvas.default_view_range is not None
    _x_range, y_range = widget.canvas.default_view_range
    assert y_range[0] > -10
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
