import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QPushButton

from sassie_qt.menu_loader import (
    DEFAULT_GENAPP_ZAZZIE_ROOT,
    DEFAULT_ZAZZIE_ROOT,
    ModuleField,
    load_menu,
)
from sassie_qt.module_registry import MODULE_RUNNER_FACTORIES
from sassie_qt.modules.data_interpolation.runner import DataInterpolationRunner
from sassie_qt.plotting.data_interpolation_plot import build_data_interpolation_figure
from sassie_qt.prototype_app import (
    DataInterpolationPlotWidget,
    JsonIntegerPairRepeatingFieldRows,
    JsonRepeatingFieldRows,
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
    assert page._collect_form_values()["run_name"] == "run_0"
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
    assert page.project_directory == project_directory.resolve()
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
    assert page._collect_form_values()["data_file_name"] == str(project_file)
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

    _select_category(window, "Build")
    _select_category(window, "Tools")

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
    with pytest.raises(ValueError, match="experimental data file"):
        DataInterpolationRunner().prepare_variables(
            page.project_directory,
            page._collect_form_values(),
        )
    app.processEvents()


def test_extract_utilities_uses_real_repeaters():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    page = _module_page(window, "Extract Utilities")
    assert page is not None

    assert page.input_rows["pdb_filename"].isHidden()
    page.input_rows["trajectory_checkbox"].value_widget.setChecked(True)
    app.processEvents()
    assert not page.input_rows["pdb_filename"].isHidden()

    _set_combo_value(page.input_rows["option_list_box"].value_widget, "c4")
    app.processEvents()
    assert not page.input_rows["local_value_c4"].isHidden()
    assert page.input_rows["local_value_c1"].isHidden()

    page.input_rows["sas_checkbox"].value_widget.setChecked(True)
    page.input_rows["number_of_sas_paths"].set_value("3")
    app.processEvents()
    sas_paths = page.input_rows["sas_paths"]
    assert isinstance(sas_paths, JsonRepeatingFieldRows)
    assert len(sas_paths.rows) == 3
    assert "sas_paths" in page._collect_form_values()


def test_merge_utilities_syncs_integer_repeaters():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    page = _module_page(window, "Merge Utilities")
    assert page is not None

    page.input_rows["trajectory_checkbox"].value_widget.setChecked(True)
    page.input_rows["number_of_runs_to_merge"].set_value("4")
    app.processEvents()

    trajectory_names = page.input_rows["trajectory_names"]
    assert isinstance(trajectory_names, JsonRepeatingFieldRows)
    assert len(trajectory_names.rows) == 4
    assert page.input_rows["number_of_trajectories"].isHidden()


def test_build_utilities_uses_real_repeaters():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    _select_category(window, "Build")
    page = _module_page(window, "Build Utilities")
    assert page is not None

    assert not page.input_rows["input_pdbfile"].isHidden()
    assert page.input_rows["fasta_output_filename"].isHidden()

    _set_combo_value(page.input_rows["pdb_choices_listbox"].value_widget, "c2")
    page.input_rows["number_of_constraint_files"].set_value("3")
    app.processEvents()
    constraint_options = page.input_rows["constraint_listbox"]
    constraint_filenames = page.input_rows["constraint_pdb_files"]
    assert isinstance(constraint_options, JsonRepeatingFieldRows)
    assert isinstance(constraint_filenames, JsonRepeatingFieldRows)
    assert len(constraint_options.rows) == 3
    assert len(constraint_filenames.rows) == 3

    _set_combo_value(page.input_rows["build_utilities_listbox"].value_widget, "c2")
    app.processEvents()
    assert page.input_rows["input_pdbfile"].isHidden()
    assert not page.input_rows["fasta_output_filename"].isHidden()
    assert not page.input_rows["fasta_input_sequence"].isHidden()
    assert page.input_rows["fasta_input_file"].isHidden()

    _set_combo_value(page.input_rows["fasta_listbox"].value_widget, "c2")
    app.processEvents()
    assert page.input_rows["fasta_input_sequence"].isHidden()
    assert not page.input_rows["fasta_input_file"].isHidden()


def test_simulate_modules_are_registered_and_use_repeaters():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    expected_runner_ids = {
        "torsion_angle_monte_carlo",
        "monomer_monte_carlo",
        "complex_monte_carlo",
        "energy_minimization",
        "openmm",
        "torsion_angle_md",
        "prody",
    }
    assert expected_runner_ids <= set(MODULE_RUNNER_FACTORIES)

    _select_category(window, "Simulate")
    simulate_tab_labels = {
        window.module_tabs.tabText(index)
        for index in range(window.module_tabs.count())
    }
    assert {
        "Torsion Angle Monte Carlo",
        "Monomer Monte Carlo",
        "Complex Monte Carlo",
        "Energy Minimization",
        "OpenMM",
        "Torsion Angle MD",
        "Prody",
    } <= simulate_tab_labels

    page = _module_page(window, "Torsion Angle Monte Carlo")
    assert page is not None
    page.input_rows["number_of_flexible_regions"].set_value("2")
    app.processEvents()
    assert isinstance(page.input_rows["basis_string_array"], JsonRepeatingFieldRows)
    assert len(page.input_rows["basis_string_array"].rows) == 2

    page = _module_page(window, "Energy Minimization")
    assert page is not None
    assert not page.input_rows["nsteps_1"].isHidden()
    assert page.input_rows["mdsteps_1"].isHidden()
    _set_combo_value(page.input_rows["md_list_box"].value_widget, "c2")
    app.processEvents()
    assert page.input_rows["nsteps_1"].isHidden()
    assert not page.input_rows["mdsteps_1"].isHidden()


def test_contrast_modules_are_registered_and_use_integer_pair_repeaters():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    window = SassieQtPrototype(
        load_menu(DEFAULT_GENAPP_ZAZZIE_ROOT),
        DEFAULT_GENAPP_ZAZZIE_ROOT,
        DEFAULT_ZAZZIE_ROOT,
    )

    expected_runner_ids = {
        "contrast_calculator",
        "multi_component_analysis",
        "contrast_variation_analysis",
        "rg_center_of_mass_distance_calculator",
    }
    assert expected_runner_ids <= set(MODULE_RUNNER_FACTORIES)

    _select_category(window, "Contrast")
    page = _module_page(window, "Multi-Component Analysis")
    assert page is not None

    _set_combo_value(page.input_rows["multi_component_analysis_listbox"].value_widget, "c3")
    page.input_rows["number_of_contrast_points_decomposition"].set_value("3")
    page.input_rows["number_of_components_decomposition"].set_value("2")
    app.processEvents()

    delta_rho = page.input_rows["delta_rho_decomposition"]
    assert isinstance(delta_rho, JsonIntegerPairRepeatingFieldRows)
    assert len(delta_rho.edits) == 3
    assert len(delta_rho.edits[0]) == 2
    assert page.input_rows["mpair_decomposition"].isHidden()
    assert not delta_rho.isHidden()
    assert delta_rho.value().count(";") == 2


def test_repeating_field_resize_preserves_existing_values():
    configure_qt_plugin_paths()
    QApplication.instance() or QApplication([])

    rows = JsonRepeatingFieldRows(
        ModuleField(
            id="filenames",
            label="filename",
            field_type="text",
            role="input",
            default="",
        ),
        "input",
    )

    rows.set_count(2)
    rows.rows[0].set_value("first.dat")
    rows.rows[1].set_value("second.dat")

    rows.set_count(3)
    assert [row.value() for row in rows.rows] == [
        "first.dat",
        "second.dat",
        "",
    ]

    rows.rows[2].set_value("third.dat")
    rows.set_count(2)
    assert [row.value() for row in rows.rows] == ["first.dat", "second.dat"]


def test_integer_pair_headers_refresh_without_dimension_change():
    configure_qt_plugin_paths()
    app = QApplication.instance() or QApplication([])
    row_headers = ["contrast 1", "contrast 2"]
    column_headers = ["component A", "component B"]

    matrix = JsonIntegerPairRepeatingFieldRows(
        ModuleField(
            id="delta_rho",
            label="delta rho",
            field_type="float",
            role="input",
            default="",
        ),
        "input",
        dimensions_provider=lambda: (2, 2),
        header_provider=lambda: (row_headers, column_headers),
    )
    matrix.edits[0][0].setText("1.0")
    matrix.edits[1][1].setText("4.0")

    row_headers[:] = ["D2O 0", "D2O 100"]
    column_headers[:] = ["protein", "RNA"]
    matrix.set_dimensions(2, 2)
    app.processEvents()

    label_texts = {label.text() for label in matrix.findChildren(QLabel)}
    assert {"D2O 0", "D2O 100", "protein", "RNA"} <= label_texts
    assert matrix.edits[0][0].text() == "1.0"
    assert matrix.edits[1][1].text() == "4.0"


def _module_page(window, tab_name):
    for index in range(window.module_tabs.count()):
        if window.module_tabs.tabText(index) == tab_name:
            return window.module_tabs.widget(index)
    return None


def _select_category(window, category_label):
    for row in range(window.category_list.count()):
        item = window.category_list.item(row)
        if item.text() == category_label:
            window.category_list.setCurrentRow(row)
            QApplication.processEvents()
            return
    labels = [
        window.category_list.item(row).text()
        for row in range(window.category_list.count())
    ]
    raise AssertionError(f"Category not found: {category_label!r}; got {labels!r}")


def _set_combo_value(combo_box, value):
    for index in range(combo_box.count()):
        if combo_box.itemData(index) == value:
            combo_box.setCurrentIndex(index)
            return
    raise AssertionError(f"Combo value not found: {value}")
