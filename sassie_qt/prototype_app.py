"""First SASSIE Qt prototype.

This app reads the canonical GenApp menu and module JSON definitions while
incrementally replacing the GenApp layer with native Qt workflows.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import sys
import webbrowser
from pathlib import Path
from typing import Callable

import pyqtgraph as pg
from pyqtgraph import exporters as pg_exporters
import PySide6
from PySide6.QtCore import QRect, QThread, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sassie_qt.menu_loader import (
    DEFAULT_GENAPP_ZAZZIE_ROOT,
    DEFAULT_ZAZZIE_ROOT,
    MenuGroup,
    ModuleDefinition,
    ModuleField,
    ModuleMenuItem,
    find_gui_mimic_path,
    load_menu,
    load_module_definition,
)
from sassie_qt.plotting.data_interpolation_plot import (
    export_data_interpolation_plotly_html,
    load_data_interpolation_plot_data,
)
from sassie_qt.runners.data_interpolation_runner import (
    DataInterpolationInput,
    DataInterpolationResult,
    DataInterpolationRunner,
)


APPLICATION_ICON_PATH = Path(__file__).resolve().parent / "assets" / "sassie_icon.png"
DEFAULT_PROJECT_DIRECTORY_NAME = "no_project_specified"


def configure_qt_plugin_paths() -> None:
    """Point Qt at PySide6's bundled plugins when Anaconda's Qt5 path wins."""

    pyside_plugins = Path(PySide6.__file__).resolve().parent / "Qt" / "plugins"
    if not pyside_plugins.exists():
        return

    existing_plugin_path = os.environ.get("QT_PLUGIN_PATH")
    plugin_paths = [str(pyside_plugins)]
    if existing_plugin_path:
        plugin_paths.append(existing_plugin_path)
    os.environ["QT_PLUGIN_PATH"] = os.pathsep.join(plugin_paths)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(pyside_plugins / "platforms")


def load_application_icon() -> QIcon:
    """Load the SASSIE cat-silhouette application icon."""

    return QIcon(str(APPLICATION_ICON_PATH))


def default_project_directory(base_directory: Path | None = None) -> Path:
    """Return the SASSIE-web-compatible default project directory."""

    base_directory = Path.cwd() if base_directory is None else base_directory
    return (base_directory / DEFAULT_PROJECT_DIRECTORY_NAME).expanduser().resolve()


class DataInterpolationWorker(QThread):
    """Run data_interpolation off the GUI thread."""

    message_received = Signal(str)
    progress_changed = Signal(float)
    finished_successfully = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        inputs: DataInterpolationInput,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.inputs = inputs

    def run(self) -> None:
        try:
            result = DataInterpolationRunner().run(
                self.inputs,
                message_callback=self.message_received.emit,
                progress_callback=self.progress_changed.emit,
            )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished_successfully.emit(result)


class ModuleStubPage(QWidget):
    """Preview one module without wiring the scientific backend."""

    def __init__(
        self,
        menu_item: ModuleMenuItem,
        module_definition: ModuleDefinition | None,
        gui_mimic_path: Path | None,
        project_directory: Path,
        last_file_directories: dict[str, Path],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.menu_item = menu_item
        self.module_definition = module_definition
        self.gui_mimic_path = gui_mimic_path
        self.project_directory = project_directory
        self.last_file_directories = last_file_directories
        self.input_rows: dict[str, JsonFieldRow] = {}
        self.output_rows: dict[str, JsonFieldRow] = {}
        self.plot_widgets: dict[str, DataInterpolationPlotWidget] = {}
        self.run_log_text: QTextEdit | None = None
        self.view_tabs: QTabWidget | None = None
        self.active_worker: DataInterpolationWorker | None = None
        self._build_ui()

    def set_project_directory(self, project_directory: Path) -> None:
        self.project_directory = project_directory

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(18, 16, 18, 18)
        outer_layout.setSpacing(12)

        title = QLabel(self.menu_item.label)
        title.setObjectName("moduleTitle")
        outer_layout.addWidget(title)

        views = self._visible_views()
        view_tabs = QTabWidget()
        view_tabs.setObjectName("viewTabs")
        self.view_tabs = view_tabs
        for view_name in views:
            view_tabs.addTab(self._build_view(view_name), view_name)
        outer_layout.addWidget(view_tabs, 1)

    def _visible_views(self) -> tuple[str, ...]:
        views = self.menu_item.views or ("Input", "Output", "Plots", "OpenGL")
        if self.menu_item.id == "data_interpolation":
            return tuple(view for view in views if view.lower() != "opengl")
        return tuple(views)

    def _build_view(self, view_name: str) -> QWidget:
        if view_name.lower() == "input":
            return self._build_field_preview(role="input")
        if view_name.lower() == "output":
            return self._build_field_preview(role="output")
        if view_name.lower() == "plots":
            return self._build_plot_preview()

        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setContentsMargins(14, 14, 14, 14)
        label = QLabel(f"{view_name} surface placeholder")
        label.setObjectName("panelTitle")
        body = QLabel("This area is reserved for the native Qt implementation.")
        body.setObjectName("mutedText")
        body.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(body)
        layout.addStretch(1)
        return placeholder

    def _build_field_preview(self, role: str) -> QWidget:
        scroll_area = QScrollArea()
        if role == "output":
            scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        if role == "output":
            layout.setContentsMargins(0, 14, 0, 14)
        else:
            layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        if self.module_definition is None:
            message = QLabel("No field metadata is available for this module yet.")
            message.setObjectName("mutedText")
            layout.addWidget(message)
            layout.addStretch(1)
            scroll_area.setWidget(container)
            return scroll_area

        fields = [
            field
            for field in self.module_definition.fields
            if field.role == role
        ]
        if not fields:
            message = QLabel(f"No {role} fields are declared for this module.")
            message.setObjectName("mutedText")
            layout.addWidget(message)
            layout.addStretch(1)
            scroll_area.setWidget(container)
            return scroll_area

        for field in fields:
            if role == "output" and field.id == "progress_html":
                continue
            if role == "output" and field.field_type == "plotly":
                continue
            if field.field_type == "label":
                section_label = JsonSectionLabel(field.label)
                _apply_tooltip(section_label, field.help_text)
                layout.addWidget(section_label)
            else:
                row = JsonFieldRow(
                    field,
                    role,
                    project_directory_provider=lambda: self.project_directory,
                    file_dialog_directory_provider=(
                        lambda field_id=field.id: self._file_dialog_start_directory(field_id)
                    ),
                    file_source_directory_recorder=(
                        lambda source_path, field_id=field.id: (
                            self._remember_file_source_directory(field_id, source_path)
                        )
                    ),
                )
                if role == "input":
                    self.input_rows[field.id] = row
                else:
                    self.output_rows[field.id] = row
                layout.addWidget(row)
        if role == "input" and self.menu_item.id == "data_interpolation":
            layout.addWidget(self._build_data_interpolation_actions())
        if role == "output" and self.menu_item.id == "data_interpolation":
            layout.addWidget(JsonSectionLabel("Run Log"))
            self.run_log_text = QTextEdit()
            self.run_log_text.setObjectName("runLogText")
            self.run_log_text.setReadOnly(True)
            self.run_log_text.document().setDocumentMargin(4)
            self.run_log_text.setMinimumHeight(340)
            layout.addWidget(self.run_log_text, 1)
        if not (role == "output" and self.menu_item.id == "data_interpolation"):
            layout.addStretch(1)
        scroll_area.setWidget(container)
        return scroll_area

    def _build_plot_preview(self) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        plot_fields = self._plot_fields()
        if not plot_fields:
            message = QLabel("No plots are declared for this module.")
            message.setObjectName("mutedText")
            layout.addWidget(message)
            layout.addStretch(1)
            scroll_area.setWidget(container)
            return scroll_area

        for field in plot_fields:
            plot_widget = DataInterpolationPlotWidget()
            _apply_tooltip(plot_widget, field.help_text)
            self.plot_widgets[field.id] = plot_widget
            layout.addWidget(plot_widget)

        layout.addStretch(1)

        scroll_area.setWidget(container)
        return scroll_area

    def _plot_fields(self) -> list[ModuleField]:
        if self.module_definition is None:
            return []
        return [
            field
            for field in self.module_definition.fields
            if field.role == "output" and field.field_type == "plotly"
        ]

    def _build_data_interpolation_actions(self) -> QWidget:
        actions = QWidget()
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.addStretch(1)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self._reset_input_fields)
        layout.addWidget(reset_button)

        run_button = QPushButton("Run")
        run_button.setObjectName("primaryButton")
        run_button.clicked.connect(self._run_data_interpolation)
        layout.addWidget(run_button)
        return actions

    def _reset_input_fields(self) -> None:
        for row in self.input_rows.values():
            row.reset_value()

    def _run_data_interpolation(self) -> None:
        if self.active_worker is not None and self.active_worker.isRunning():
            message = "A data interpolation run is already active."
            self._append_run_log(f"{message}\n")
            self._show_warning(message)
            return

        try:
            inputs = self._collect_data_interpolation_inputs()
        except ValueError as error:
            self._set_progress(0.0)
            self._append_run_log(f"{error}\n")
            self._show_output_tab()
            self._show_warning(str(error))
            return

        self._clear_output_widgets()
        self._set_progress(0.0)
        self._append_run_log("Starting data interpolation...\n")
        self._show_output_tab()

        worker = DataInterpolationWorker(inputs)
        worker.message_received.connect(self._append_run_log)
        worker.progress_changed.connect(self._set_progress)
        worker.finished_successfully.connect(self._handle_run_success)
        worker.failed.connect(self._handle_run_failure)
        worker.finished.connect(self._clear_active_worker)
        self.active_worker = worker
        worker.start()

    def _collect_data_interpolation_inputs(self) -> DataInterpolationInput:
        required_fields = [
            "run_name",
            "data_file_name",
            "output_file_name",
            "izero",
            "izero_error",
            "delta_q",
            "maximum_points",
        ]
        missing_fields = [
            field_id for field_id in required_fields if field_id not in self.input_rows
        ]
        if missing_fields:
            raise ValueError(f"Missing data_interpolation fields: {', '.join(missing_fields)}")

        run_directory = self.project_directory.expanduser()
        run_name = self.input_rows["run_name"].value().strip()
        data_file_name = self.input_rows["data_file_name"].value().strip()
        output_file_name = self.input_rows["output_file_name"].value().strip()

        if not str(run_directory).strip():
            raise ValueError("Choose a project directory before running.")
        if not run_name:
            raise ValueError("Enter a run name before running.")
        if not data_file_name:
            raise ValueError("Choose an experimental data file before running.")
        if not output_file_name:
            raise ValueError("Enter an output file name before running.")

        data_file_path = Path(data_file_name).expanduser()
        if data_file_path.is_dir():
            raise ValueError("Choose an experimental data file, not a directory.")
        if not data_file_path.exists():
            raise ValueError(f"Experimental data file does not exist: {data_file_path}")

        return DataInterpolationInput(
            run_directory=run_directory,
            run_name=run_name,
            data_file_name=data_file_path,
            output_file_name=output_file_name,
            izero=self.input_rows["izero"].value(),
            izero_error=self.input_rows["izero_error"].value(),
            delta_q=self.input_rows["delta_q"].value(),
            maximum_points=self.input_rows["maximum_points"].value(),
        )

    def _show_output_tab(self) -> None:
        if self.view_tabs is None:
            return
        for index in range(self.view_tabs.count()):
            if self.view_tabs.tabText(index).lower() == "output":
                self.view_tabs.setCurrentIndex(index)
                return

    def _clear_output_widgets(self) -> None:
        if self.run_log_text is not None:
            self.run_log_text.clear()
        for row in self.output_rows.values():
            row.clear_output()
        for plot_widget in self.plot_widgets.values():
            plot_widget.clear()

    def _append_run_log(self, message: str) -> None:
        if self.run_log_text is None:
            return
        self.run_log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.run_log_text.insertPlainText(message)
        self.run_log_text.moveCursor(QTextCursor.MoveOperation.End)

    def _set_progress(self, progress: float) -> None:
        progress_row = self.output_rows.get("progress_output")
        if progress_row is not None:
            progress_row.set_progress(progress)

    def _handle_run_success(self, result: DataInterpolationResult) -> None:
        self._set_progress(1.0)
        self._append_run_log("\nRun complete.\n")
        self._append_run_log(f"Output: {result.output_file}\n")
        self._append_run_log(f"S/N output: {result.signal_to_noise_output_file}\n")
        self._append_run_log(f"Plot JSON: {result.plot_json_file}\n")
        try:
            self._set_data_interpolation_plot(result.plot_json_file)
        except Exception as error:
            self._append_run_log(f"Plot update failed: {error}\n")
            self._show_warning(f"Run complete, but the plot could not be loaded:\n{error}")
            return
        self._show_plots_tab()

    def _handle_run_failure(self, error: str) -> None:
        self._append_run_log(f"\nRun failed:\n{error}\n")
        self._show_error(error)

    def _clear_active_worker(self) -> None:
        self.active_worker = None

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "Data Interpolation", message)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Data Interpolation Failed", message)

    def _show_plots_tab(self) -> None:
        if self.view_tabs is None:
            return
        for index in range(self.view_tabs.count()):
            if self.view_tabs.tabText(index).lower() == "plots":
                self.view_tabs.setCurrentIndex(index)
                return

    def _set_data_interpolation_plot(self, plot_data_file: Path) -> None:
        plot_widget = self.plot_widgets.get("lineplot")
        if plot_widget is None:
            return
        plot_widget.set_plot_data(plot_data_file)

    def _file_dialog_start_directory(self, field_id: str) -> Path:
        remembered_directory = self.last_file_directories.get(
            self._file_directory_key(field_id)
        )
        if remembered_directory is not None and remembered_directory.is_dir():
            return remembered_directory
        if self.project_directory.is_dir():
            return self.project_directory
        return Path.home()

    def _remember_file_source_directory(self, field_id: str, source_path: Path) -> None:
        source_directory = source_path.expanduser().resolve().parent
        if source_directory.is_dir():
            self.last_file_directories[self._file_directory_key(field_id)] = (
                source_directory
            )

    def _file_directory_key(self, field_id: str) -> str:
        return f"{self.menu_item.id}:{field_id}"


class JsonSectionLabel(QLabel):
    """A section heading declared in a GenApp module JSON file."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text.strip() or "Section", parent)
        self.setObjectName("jsonSectionLabel")
        self.setWordWrap(True)


class InvertingTextProgressBar(QProgressBar):
    """Progress bar that keeps centered percent text legible across the chunk."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(24)
        self.setFormat("0%")

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bar_rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QColor("#cbd5e1"))
        painter.setBrush(QColor("#eef2f7"))
        painter.drawRoundedRect(bar_rect, 4, 4)

        if self.maximum() > self.minimum():
            ratio = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
        else:
            ratio = 0
        ratio = max(0.0, min(1.0, ratio))
        fill_rect = QRect(bar_rect)
        fill_rect.setWidth(round(bar_rect.width() * ratio))
        if fill_rect.width() > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#4f83f1"))
            painter.drawRoundedRect(fill_rect, 4, 4)

        text = self.text()
        painter.setClipRect(bar_rect)
        painter.setPen(QColor("#1f2933"))
        painter.drawText(bar_rect, Qt.AlignCenter, text)
        if fill_rect.width() > 0:
            painter.setClipRect(fill_rect)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(bar_rect, Qt.AlignCenter, text)


class DataInterpolationPlotWidget(QWidget):
    """Native Qt data_interpolation plot with optional Plotly export."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.plot_data_file: Path | None = None
        self.plot_data: dict | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        actions = QWidget()
        action_layout = QHBoxLayout(actions)
        action_layout.setContentsMargins(0, 0, 0, 0)

        self.pan_button = QPushButton("Pan")
        self.pan_button.setCheckable(True)
        self.pan_button.setChecked(True)
        self.pan_button.clicked.connect(self.set_pan_mode)
        action_layout.addWidget(self.pan_button)

        self.box_zoom_button = QPushButton("Box Zoom")
        self.box_zoom_button.setCheckable(True)
        self.box_zoom_button.clicked.connect(self.set_box_zoom_mode)
        action_layout.addWidget(self.box_zoom_button)

        self.mouse_mode_buttons = QButtonGroup(self)
        self.mouse_mode_buttons.setExclusive(True)
        self.mouse_mode_buttons.addButton(self.pan_button)
        self.mouse_mode_buttons.addButton(self.box_zoom_button)

        action_layout.addStretch(1)

        self.reset_view_button = QPushButton("Reset View")
        self.reset_view_button.setEnabled(False)
        self.reset_view_button.clicked.connect(self.reset_view)
        action_layout.addWidget(self.reset_view_button)

        self.save_png_button = QPushButton("Save PNG")
        self.save_png_button.setEnabled(False)
        self.save_png_button.clicked.connect(lambda: self.save_png())
        action_layout.addWidget(self.save_png_button)

        self.export_plotly_button = QPushButton("Export Plotly HTML")
        self.export_plotly_button.setEnabled(False)
        self.export_plotly_button.clicked.connect(lambda: self.export_plotly_html())
        action_layout.addWidget(self.export_plotly_button)

        self.open_plotly_button = QPushButton("Open Plotly")
        self.open_plotly_button.setEnabled(False)
        self.open_plotly_button.clicked.connect(lambda: self.open_plotly_html())
        action_layout.addWidget(self.open_plotly_button)

        self.canvas = DataInterpolationPlotCanvas()
        self.legend_panel = self._build_legend_panel()
        self._update_legend_labels(None)
        self.plot_help_box = self._build_plot_help_box()

        plot_area = QWidget()
        plot_area.setMaximumHeight(330)
        plot_layout = QHBoxLayout(plot_area)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(10)
        plot_layout.addWidget(self.canvas, 1)
        plot_layout.addWidget(self.legend_panel)

        layout.addWidget(actions)
        layout.addWidget(self.plot_help_box)
        layout.addWidget(plot_area, 1)

        self.setMinimumHeight(280)
        self.setMaximumHeight(455)

    def set_plot_data(self, plot_data_file: Path) -> None:
        self.plot_data_file = plot_data_file
        self.plot_data = load_data_interpolation_plot_data(plot_data_file)
        self.canvas.set_plot_data(self.plot_data)
        self._update_legend_labels(self.plot_data)
        self.reset_view_button.setEnabled(True)
        self.save_png_button.setEnabled(True)
        self.export_plotly_button.setEnabled(True)
        self.open_plotly_button.setEnabled(True)

    def clear(self) -> None:
        self.plot_data_file = None
        self.plot_data = None
        self.canvas.clear()
        self._update_legend_labels(None)
        self.reset_view_button.setEnabled(False)
        self.save_png_button.setEnabled(False)
        self.export_plotly_button.setEnabled(False)
        self.open_plotly_button.setEnabled(False)

    def reset_view(self) -> None:
        self.canvas.reset_view()

    def set_pan_mode(self) -> None:
        self.pan_button.setChecked(True)
        self.canvas.set_pan_mode()

    def set_box_zoom_mode(self) -> None:
        self.box_zoom_button.setChecked(True)
        self.canvas.set_box_zoom_mode()

    def save_png(self, show_dialog: bool = True) -> Path | None:
        if self.plot_data_file is None:
            return None

        output_file = self.plot_data_file.with_name(f"{self.plot_data_file.stem}_plot.png")
        if show_dialog:
            selected_file, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "Save Plot PNG",
                str(output_file),
                "PNG Images (*.png)",
            )
            if not selected_file:
                return None
            output_file = Path(selected_file)

        self.canvas.save_png(output_file)
        if show_dialog:
            QMessageBox.information(
                self,
                "Plot Saved",
                f"PNG written to:\n{output_file}",
            )
        return output_file

    def export_plotly_html(self, show_message: bool = True) -> Path | None:
        if self.plot_data_file is None:
            return None
        html_file = export_data_interpolation_plotly_html(self.plot_data_file)
        if show_message:
            QMessageBox.information(
                self,
                "Plotly Export",
                f"Plotly HTML written to:\n{html_file}",
            )
        return html_file

    def open_plotly_html(self) -> Path | None:
        if self.plot_data_file is None:
            return None
        html_file = export_data_interpolation_plotly_html(self.plot_data_file)
        webbrowser.open(html_file.resolve().as_uri())
        return html_file

    def _build_legend_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("plotLegendPanel")
        panel.setMinimumWidth(260)
        panel.setMaximumWidth(360)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(8)
        original_row, self.original_legend_label = self._legend_row(
            "#d32f2f",
            "original data",
        )
        interpolated_row, self.interpolated_legend_label = self._legend_row(
            "#3f5ee8",
            "interpolated data",
        )
        cutoff_row, self.cutoff_legend_label = self._legend_row("#6b7280", "")
        layout.addWidget(original_row)
        layout.addWidget(interpolated_row)
        layout.addWidget(cutoff_row)
        layout.addStretch(1)
        return panel

    def _legend_row(self, color: str, text: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        swatch = QFrame()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        label = QLabel(text)
        label.setTextFormat(Qt.PlainText)
        label.setWordWrap(True)
        label.setObjectName("plotLegendText")
        layout.addWidget(swatch, 0, Qt.AlignTop)
        layout.addWidget(label, 1)
        return row, label

    def _build_plot_help_box(self) -> QFrame:
        box = QFrame()
        box.setObjectName("plotHelpBox")
        box.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(box)
        layout.setContentsMargins(10, 6, 10, 6)
        label = QLabel(
            "Plot controls: Pan drags the view; Box Zoom drags a rectangle over "
            "x and y; mouse wheel zooms; drag an axis for one-axis zoom; "
            "right-click for plot options."
        )
        label.setObjectName("plotHelpText")
        label.setWordWrap(True)
        layout.addWidget(label)
        return box

    def _update_legend_labels(self, plot_data: dict | None) -> None:
        self.original_legend_label.setText("original data")
        self.interpolated_legend_label.setText("interpolated data")
        cutoff_x = (
            None
            if plot_data is None
            else plot_data.get("signal_to_noise_cutoff_value")
        )
        if cutoff_x is None or cutoff_x <= 0:
            self.cutoff_legend_label.setText("S/N cutoff")
            return

        self.cutoff_legend_label.setText(
            f"cutoff q value: {cutoff_x:.4g}\n"
            "[I(q)/(std.dev. I(q))] < 2"
        )


class SparseLogAxisItem(pg.AxisItem):
    """Log axis that labels only stable, readable q ticks."""

    def tickStrings(self, values, scale, spacing):  # noqa: N802 - Qt override name
        if not self.logMode:
            return super().tickStrings(values, scale, spacing)

        labels = []
        for value in values:
            q_value = 10 ** value
            if self._is_preferred_q_tick(q_value):
                labels.append(f"{q_value:.3g}")
            else:
                labels.append("")
        return labels

    def _is_preferred_q_tick(self, q_value: float) -> bool:
        if q_value <= 0:
            return False

        exponent = math.floor(math.log10(q_value))
        mantissa = q_value / (10 ** exponent)
        return any(math.isclose(mantissa, tick, rel_tol=0.015) for tick in (1, 2, 5))


class DataInterpolationPlotCanvas(pg.PlotWidget):
    """Interactive PyQtGraph plot for data_interpolation output."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            axisItems={"bottom": SparseLogAxisItem("bottom")},
        )
        self.plot_data: dict | None = None
        self.default_view_range: tuple[
            tuple[float, float],
            tuple[float, float],
        ] | None = None
        self.setMinimumHeight(224)
        self.plot_item = self.getPlotItem()
        self.plot_item.setTitle("Data Interpolation Plot", color="#253244", size="14pt")
        self.plot_item.setLabel("bottom", "q (1/Å)")
        self.plot_item.setLabel("left", "I(q)")
        self.plot_item.setLogMode(x=True, y=True)
        self.plot_item.showGrid(x=True, y=True, alpha=0.25)
        self.plot_item.setMenuEnabled(True)
        self._configure_axes()
        self.set_pan_mode()
        self.setBackground("w")

    def set_plot_data(self, plot_data: dict) -> None:
        self.plot_data = plot_data
        self._render_plot()

    def clear(self) -> None:
        self.plot_data = None
        self.default_view_range = None
        self.plot_item.clear()

    def reset_view(self) -> None:
        if self.default_view_range is not None:
            self.plot_item.setRange(
                xRange=self.default_view_range[0],
                yRange=self.default_view_range[1],
                padding=0,
            )
            return
        self.plot_item.enableAutoRange()
        self.plot_item.autoRange()

    def set_pan_mode(self) -> None:
        self.plot_item.getViewBox().setMouseMode(pg.ViewBox.PanMode)

    def set_box_zoom_mode(self) -> None:
        self.plot_item.getViewBox().setMouseMode(pg.ViewBox.RectMode)

    def save_png(self, output_file: Path) -> None:
        exporter = pg_exporters.ImageExporter(self.plot_item)
        exporter.export(str(output_file))

    def _configure_axes(self) -> None:
        bottom_axis = self.plot_item.getAxis("bottom")
        left_axis = self.plot_item.getAxis("left")
        for axis in (bottom_axis, left_axis):
            axis.enableAutoSIPrefix(False)
            axis.setStyle(maxTextLevel=0, maxTickLevel=1)
        bottom_axis.setStyle(tickTextWidth=70)

    def _render_plot(self) -> None:
        self.plot_item.clear()
        if not self.plot_data:
            return

        self.default_view_range = self._visible_plot_range()
        y_floor = (
            10 ** self.default_view_range[1][0]
            if self.default_view_range is not None
            else None
        )

        self._plot_series(
            x_values=self.plot_data.get("original_q", []),
            y_values=self.plot_data.get("original_iq", []),
            y_errors=self.plot_data.get("original_iq_error", []),
            color="#d32f2f",
            name="original data",
            connect_points=False,
            y_floor=y_floor,
        )
        self._plot_series(
            x_values=self.plot_data.get("q", []),
            y_values=self.plot_data.get("iq", []),
            y_errors=self.plot_data.get("iq_error", []),
            color="#3f5ee8",
            name="interpolated data",
            connect_points=True,
            y_floor=y_floor,
        )
        self._plot_cutoff_marker()
        self.reset_view()

    def _plot_series(
        self,
        x_values: list[float],
        y_values: list[float],
        y_errors: list[float],
        color: str,
        name: str,
        connect_points: bool,
        y_floor: float | None,
    ) -> None:
        x_filtered, y_filtered, error_segments = self._positive_points_and_errors(
            x_values,
            y_values,
            y_errors,
            y_floor,
        )
        if not x_filtered:
            return

        if error_segments[0]:
            self.plot_item.plot(
                error_segments[0],
                error_segments[1],
                pen=pg.mkPen(color, width=1),
                connect="finite",
            )

        self.plot_item.plot(
            x_filtered,
            y_filtered,
            pen=pg.mkPen(color, width=2) if connect_points else None,
            symbol="o",
            symbolBrush=pg.mkBrush(color),
            symbolPen=pg.mkPen(color),
            symbolSize=6,
            name=name,
        )

    def _positive_points_and_errors(
        self,
        x_values: list[float],
        y_values: list[float],
        y_errors: list[float],
        y_floor: float | None = None,
    ) -> tuple[list[float], list[float], tuple[list[float], list[float]]]:
        x_filtered = []
        y_filtered = []
        error_x_values = []
        error_y_values = []
        for index, (x_value, y_value) in enumerate(zip(x_values, y_values)):
            if x_value <= 0 or y_value <= 0:
                continue
            x_filtered.append(x_value)
            y_filtered.append(y_value)
            if index < len(y_errors):
                y_error = y_errors[index]
                high_value = y_value + y_error
                low_value = y_value - y_error
                if y_floor is not None:
                    low_value = max(low_value, y_floor)
                if low_value > 0 and high_value > low_value:
                    error_x_values.extend([x_value, x_value, float("nan")])
                    error_y_values.extend([low_value, high_value, float("nan")])
        return x_filtered, y_filtered, (error_x_values, error_y_values)

    def _visible_plot_range(
        self,
    ) -> tuple[tuple[float, float], tuple[float, float]] | None:
        if self.plot_data is None:
            return None

        x_values = []
        y_values = []
        for x_key, y_key, error_key in (
            ("original_q", "original_iq", "original_iq_error"),
            ("q", "iq", "iq_error"),
        ):
            series_x_values = self.plot_data.get(x_key, [])
            series_y_values = self.plot_data.get(y_key, [])
            series_error_values = self.plot_data.get(error_key, [])
            for index, (x_value, y_value) in enumerate(
                zip(series_x_values, series_y_values)
            ):
                if x_value > 0:
                    x_values.append(x_value)
                if y_value > 0:
                    y_values.append(y_value)
                if index < len(series_error_values):
                    y_error = series_error_values[index]
                    low_value = y_value - y_error
                    high_value = y_value + y_error
                    if low_value > 0:
                        y_values.append(low_value)
                    if high_value > 0:
                        y_values.append(high_value)

        if not x_values or not y_values:
            return None

        return (
            self._padded_log_range(min(x_values), max(x_values), padding=0.04),
            self._padded_log_range(min(y_values), max(y_values), padding=0.08),
        )

    def _padded_log_range(
        self,
        minimum_value: float,
        maximum_value: float,
        padding: float,
    ) -> tuple[float, float]:
        log_minimum = math.log10(minimum_value)
        log_maximum = math.log10(maximum_value)
        if log_minimum == log_maximum:
            return (log_minimum - 0.5, log_maximum + 0.5)

        span = log_maximum - log_minimum
        return (
            log_minimum - span * padding,
            log_maximum + span * padding,
        )

    def _plot_cutoff_marker(self) -> None:
        cutoff_x = self.plot_data.get("signal_to_noise_cutoff_value")
        if cutoff_x is None or cutoff_x <= 0:
            return

        y_values = [
            value
            for key in ("original_iq", "iq")
            for value in self.plot_data.get(key, [])
            if value > 0
        ]
        if not y_values:
            return
        if self.default_view_range is not None:
            y_minimum = 10 ** self.default_view_range[1][0]
            y_maximum = 10 ** self.default_view_range[1][1]
        else:
            y_minimum = min(y_values)
            y_maximum = max(y_values)

        self.plot_item.plot(
            [cutoff_x, cutoff_x],
            [y_minimum, y_maximum],
            pen=pg.mkPen("#6b7280", width=2, style=Qt.DashLine),
        )


class JsonFieldRow(QFrame):
    """A compact stub widget row for one GenApp JSON field."""

    def __init__(
        self,
        field: ModuleField,
        role: str,
        project_directory_provider: Callable[[], Path] | None = None,
        file_dialog_directory_provider: Callable[[], Path] | None = None,
        file_source_directory_recorder: Callable[[Path], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.field = field
        self.role = role
        self.project_directory_provider = project_directory_provider
        self.file_dialog_directory_provider = file_dialog_directory_provider
        self.file_source_directory_recorder = file_source_directory_recorder
        self.value_widget: QWidget | None = None
        self.setObjectName("jsonFieldRow")
        self.setFrameShape(QFrame.StyledPanel)
        _apply_tooltip(self, field.help_text)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        name = QLabel(field.label)
        name.setMinimumWidth(240)
        name.setWordWrap(True)
        _apply_tooltip(name, field.help_text)
        layout.addWidget(name, 1)

        control = self._build_control()
        _apply_tooltip(control, field.help_text)
        layout.addWidget(control, 3)

    def _build_control(self) -> QWidget:
        if self.role == "output":
            return self._build_output_control()

        field_type = self.field.field_type
        if field_type == "checkbox":
            checkbox = QCheckBox()
            checkbox.setChecked(str(self.field.default).lower() == "true")
            self.value_widget = checkbox
            return checkbox

        if field_type == "listbox":
            combo_box = QComboBox()
            for label, value in _parse_genapp_values(self.field.values):
                combo_box.addItem(label, value)
                if str(value) == str(self.field.default):
                    combo_box.setCurrentText(label)
            if combo_box.count() == 0:
                combo_box.addItem(_field_value_to_text(self.field.default))
            self.value_widget = combo_box
            return combo_box

        if field_type in {"lrfile", "rpath"}:
            wrapper = QWidget()
            layout = QHBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            line_edit = QLineEdit(_field_value_to_text(self.field.default))
            line_edit.setPlaceholderText("Choose a local file" if field_type == "lrfile" else "Choose a path")
            browse_button = QPushButton("Browse")
            if field_type == "lrfile":
                browse_button.clicked.connect(lambda: self._browse_for_file(line_edit))
            else:
                browse_button.clicked.connect(lambda: self._browse_for_directory(line_edit))
            layout.addWidget(line_edit, 1)
            layout.addWidget(browse_button)
            self.value_widget = line_edit
            return wrapper

        if field_type == "button":
            button = QPushButton(self.field.label or self.field.id)
            button.setEnabled(False)
            self.value_widget = button
            return button

        if field_type == "textarea":
            text_edit = QTextEdit(_field_value_to_text(self.field.default))
            text_edit.setMinimumHeight(70)
            self.value_widget = text_edit
            return text_edit

        if field_type == "integerpair":
            wrapper = QWidget()
            layout = QHBoxLayout(wrapper)
            layout.setContentsMargins(0, 0, 0, 0)
            default_values = _field_value_to_text(self.field.default).split(",")
            first = QLineEdit(default_values[0].strip() if default_values else "")
            second = QLineEdit(default_values[1].strip() if len(default_values) > 1 else "")
            first.setPlaceholderText("first")
            second.setPlaceholderText("second")
            layout.addWidget(first)
            layout.addWidget(second)
            self.value_widget = wrapper
            return wrapper

        line_edit = QLineEdit(_field_value_to_text(self.field.default))
        if field_type == "integer":
            line_edit.setPlaceholderText("integer")
        elif field_type == "float":
            line_edit.setPlaceholderText("float")
        self.value_widget = line_edit
        return line_edit

    def value(self) -> str:
        if isinstance(self.value_widget, QLineEdit):
            return self.value_widget.text()
        if isinstance(self.value_widget, QCheckBox):
            return "true" if self.value_widget.isChecked() else "false"
        if isinstance(self.value_widget, QComboBox):
            value = self.value_widget.currentData()
            return "" if value is None else str(value)
        if isinstance(self.value_widget, QTextEdit):
            return self.value_widget.toPlainText()
        if self.field.field_type == "integerpair" and self.value_widget is not None:
            line_edits = self.value_widget.findChildren(QLineEdit)
            return ",".join(line_edit.text() for line_edit in line_edits)
        return ""

    def reset_value(self) -> None:
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.setText(_field_value_to_text(self.field.default))
        elif isinstance(self.value_widget, QCheckBox):
            self.value_widget.setChecked(str(self.field.default).lower() == "true")
        elif isinstance(self.value_widget, QComboBox):
            for index in range(self.value_widget.count()):
                if str(self.value_widget.itemData(index)) == str(self.field.default):
                    self.value_widget.setCurrentIndex(index)
                    return
            self.value_widget.setCurrentIndex(0)
        elif isinstance(self.value_widget, QTextEdit):
            self.value_widget.setPlainText(_field_value_to_text(self.field.default))

    def set_value(self, value: str) -> None:
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.setText(value)
        elif isinstance(self.value_widget, QTextEdit):
            self.value_widget.setPlainText(value)

    def _browse_for_file(self, line_edit: QLineEdit) -> None:
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            f"Choose {self.field.label or self.field.id}",
            self._file_dialog_start_directory(line_edit.text()),
        )
        if file_path:
            source_path = Path(file_path)
            try:
                project_file_path = self._copy_file_to_project_directory(source_path)
            except OSError as error:
                QMessageBox.critical(
                    self,
                    "File Upload Failed",
                    f"Could not copy the selected file into the project directory:\n{error}",
                )
                return
            if self.file_source_directory_recorder is not None:
                self.file_source_directory_recorder(source_path)
            line_edit.setText(str(project_file_path))

    def _file_dialog_start_directory(self, fallback_text: str = "") -> str:
        if self.file_dialog_directory_provider is not None:
            directory = self.file_dialog_directory_provider().expanduser()
            if directory.is_dir():
                return str(directory.resolve())
        return _dialog_start_directory(fallback_text)

    def _copy_file_to_project_directory(self, file_path: Path) -> Path:
        if self.project_directory_provider is None:
            return file_path

        project_directory = self.project_directory_provider().expanduser().resolve()
        project_directory.mkdir(parents=True, exist_ok=True)
        source_path = file_path.expanduser().resolve()
        destination_path = project_directory / source_path.name
        if source_path == destination_path:
            return destination_path
        shutil.copy2(source_path, destination_path)
        return destination_path

    def _browse_for_directory(self, line_edit: QLineEdit) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            f"Choose {self.field.label or self.field.id}",
            _dialog_start_directory(line_edit.text()),
        )
        if directory:
            line_edit.setText(directory)

    def _build_output_control(self) -> QWidget:
        field_type = self.field.field_type
        if field_type == "progress":
            progress_bar = InvertingTextProgressBar()
            self.value_widget = progress_bar
            return progress_bar

        if field_type in {"html", "textarea"}:
            text_edit = QTextEdit()
            text_edit.setMinimumHeight(70)
            text_edit.setPlaceholderText(f"{self.field.label} output")
            text_edit.setReadOnly(True)
            self.value_widget = text_edit
            return text_edit

        placeholder = QLabel(_output_placeholder_text(field_type))
        placeholder.setObjectName("outputPlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setMinimumHeight(58)
        self.value_widget = placeholder
        return placeholder

    def clear_output(self) -> None:
        if isinstance(self.value_widget, QProgressBar):
            self.value_widget.setValue(0)
            self.value_widget.setFormat("0%")
        elif isinstance(self.value_widget, QTextEdit):
            self.value_widget.clear()
        elif isinstance(self.value_widget, QLabel):
            self.value_widget.setText(_output_placeholder_text(self.field.field_type))

    def set_progress(self, progress: float) -> None:
        if isinstance(self.value_widget, QProgressBar):
            percentage = round(max(0.0, min(1.0, progress)) * 100)
            self.value_widget.setValue(percentage)
            self.value_widget.setFormat(f"{percentage}%")

    def set_output_text(self, text: str) -> None:
        if isinstance(self.value_widget, QTextEdit):
            self.value_widget.setPlainText(text)
        elif isinstance(self.value_widget, QLabel):
            self.value_widget.setText(text)


def _field_value_to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _parse_genapp_values(values) -> list[tuple[str, str]]:
    if values is None:
        return []
    if isinstance(values, list):
        return [(str(item), str(item)) for item in values]
    if not isinstance(values, str):
        return [(str(values), str(values))]

    parts = [part.strip() for part in values.split("~") if part.strip()]
    if len(parts) < 2:
        return [(values, values)]
    return [
        (parts[index], parts[index + 1])
        for index in range(0, len(parts) - 1, 2)
    ]


def _output_placeholder_text(field_type: str) -> str:
    placeholders = {
        "plotly": "Plot placeholder",
        "atomicstructure": "Molecular structure placeholder",
        "image": "Image placeholder",
    }
    return placeholders.get(field_type, "Output placeholder")


def _apply_tooltip(widget: QWidget, tooltip: str) -> None:
    if not tooltip:
        return
    widget.setToolTip(tooltip)
    for child in widget.findChildren(QWidget):
        child.setToolTip(tooltip)


def _dialog_start_directory(current_text: str) -> str:
    if not current_text:
        return str(Path.home())

    current_path = Path(current_text).expanduser()
    if current_path.is_file():
        return str(current_path.parent)
    if current_path.is_dir():
        return str(current_path)
    if current_path.parent.is_dir():
        return str(current_path.parent)
    return str(Path.home())


class SassieQtPrototype(QMainWindow):
    """Main window for the first navigation prototype."""

    def __init__(
        self,
        menu_groups: tuple[MenuGroup, ...],
        genapp_zazzie_root: Path,
        zazzie_root: Path,
    ) -> None:
        super().__init__()
        self.menu_groups = menu_groups
        self.genapp_zazzie_root = genapp_zazzie_root
        self.zazzie_root = zazzie_root
        self.project_directory = default_project_directory()
        self.project_directory.mkdir(parents=True, exist_ok=True)
        self.last_file_directories: dict[str, Path] = {}
        self.module_tabs = QTabWidget()
        self.category_list = QListWidget()
        self.project_directory_edit: QLineEdit | None = None

        self.setWindowTitle("SASSIE Qt Prototype")
        self.setWindowIcon(load_application_icon())
        self.resize(1180, 860)
        self._build_menu_bar()
        self._build_ui()
        self._apply_style()

        initial_index = self._preferred_initial_group_index()
        self.category_list.setCurrentRow(initial_index)

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        project_directory_action = QAction("Select Project Directory...", self)
        project_directory_action.triggered.connect(self._choose_project_directory)
        file_menu.addAction(project_directory_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _build_ui(self) -> None:
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        self.setCentralWidget(splitter)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 12, 10, 12)
        sidebar_layout.setSpacing(10)

        app_title = QLabel("SASSIE")
        app_title.setObjectName("appTitle")
        sidebar_layout.addWidget(app_title)

        self.category_list.setObjectName("categoryList")
        self.category_list.setIconSize(self.category_list.iconSize() * 1.4)
        self.category_list.currentRowChanged.connect(self._show_group)
        for group in self.menu_groups:
            item = QListWidgetItem(group.label)
            item.setData(Qt.UserRole, group.id)
            if group.icon_path:
                item.setIcon(QIcon(str(group.icon_path)))
            self.category_list.addItem(item)
        sidebar_layout.addWidget(self.category_list, 1)

        splitter.addWidget(sidebar)

        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 14, 18, 14)
        content_layout.setSpacing(12)

        header = QLabel("Choose a SASSIE area")
        header.setObjectName("sectionTitle")
        content_layout.addWidget(header)
        self.header = header

        content_layout.addWidget(self._build_project_directory_bar())

        self.module_tabs.setObjectName("moduleTabs")
        self.module_tabs.setDocumentMode(True)
        content_layout.addWidget(self.module_tabs, 1)
        splitter.addWidget(content)
        splitter.setSizes([230, 950])

        status = QStatusBar()
        self.setStatusBar(status)
        self._update_project_directory_ui()

    def _build_project_directory_bar(self) -> QWidget:
        project_bar = QFrame()
        project_bar.setObjectName("projectDirectoryBar")
        project_bar.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(project_bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        label = QLabel("Project directory")
        label.setObjectName("metadataLabel")
        layout.addWidget(label)

        self.project_directory_edit = QLineEdit(str(self.project_directory))
        self.project_directory_edit.setReadOnly(True)
        self.project_directory_edit.setToolTip("Local folder used as the base directory for module runs.")
        layout.addWidget(self.project_directory_edit, 1)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._choose_project_directory)
        layout.addWidget(browse_button)

        return project_bar

    def _preferred_initial_group_index(self) -> int:
        for index, group in enumerate(self.menu_groups):
            if group.id == "tools":
                return index
        return 0

    def _show_group(self, index: int) -> None:
        if index < 0 or index >= len(self.menu_groups):
            return

        group = self.menu_groups[index]
        self.header.setText(group.label)
        self.module_tabs.clear()

        if not group.modules:
            empty_page = QWidget()
            layout = QVBoxLayout(empty_page)
            layout.addWidget(QLabel("This menu group has no modules yet."))
            layout.addStretch(1)
            self.module_tabs.addTab(empty_page, "Empty")
            return

        for module in group.modules:
            module_definition = load_module_definition(module.id, self.genapp_zazzie_root)
            gui_mimic_path = find_gui_mimic_path(module.id, self.zazzie_root)
            page = ModuleStubPage(
                module,
                module_definition,
                gui_mimic_path,
                self.project_directory,
                self.last_file_directories,
            )
            self.module_tabs.addTab(page, module.label.strip())

        self.statusBar().showMessage(f"Showing {group.label}")

    def _choose_project_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose Project Directory",
            str(self.project_directory),
        )
        if directory:
            self.set_project_directory(Path(directory))

    def set_project_directory(self, project_directory: Path) -> None:
        self.project_directory = project_directory.expanduser().resolve()
        self.project_directory.mkdir(parents=True, exist_ok=True)
        self._update_project_directory_ui()
        for index in range(self.module_tabs.count()):
            page = self.module_tabs.widget(index)
            if isinstance(page, ModuleStubPage):
                page.set_project_directory(self.project_directory)

    def _update_project_directory_ui(self) -> None:
        directory_text = str(self.project_directory)
        if self.project_directory_edit is not None:
            self.project_directory_edit.setText(directory_text)
        if self.statusBar() is not None:
            self.statusBar().showMessage(f"Project directory: {directory_text}")

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f7f8fa;
                color: #1f2933;
            }
            QWidget#sidebar {
                background: #151a21;
                color: #f5f7fa;
            }
            QLabel#appTitle {
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
                padding: 4px 6px 10px 6px;
            }
            QListWidget#categoryList {
                background: transparent;
                border: 0;
                color: #d8dee7;
                outline: 0;
            }
            QListWidget#categoryList::item {
                min-height: 40px;
                padding: 7px 8px;
                border-radius: 6px;
            }
            QListWidget#categoryList::item:selected {
                background: #2d6cdf;
                color: #ffffff;
            }
            QWidget#content {
                background: #f7f8fa;
            }
            QLabel#sectionTitle {
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#moduleTitle {
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#panelTitle {
                font-size: 16px;
                font-weight: 650;
            }
            QLabel#metadataLabel {
                font-weight: 650;
                color: #3a4654;
            }
            QLabel#mutedText {
                color: #66717f;
            }
            QFrame#plotHelpBox {
                background: #f8fafc;
                border: 1px solid #d8e0eb;
                border-radius: 5px;
            }
            QLabel#plotHelpText {
                color: #465364;
                font-size: 12px;
            }
            QTextEdit#runLogText {
                padding: 2px;
            }
            QTabWidget#moduleTabs::pane,
            QTabWidget#viewTabs::pane {
                border: 1px solid #d8dde5;
                background: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                padding: 8px 12px;
                min-height: 22px;
            }
            QTabBar::tab:selected {
                color: #1d4ed8;
                font-weight: 650;
            }
            QLabel#jsonSectionLabel {
                color: #253244;
                font-size: 15px;
                font-weight: 650;
                padding: 10px 4px 4px 4px;
            }
            QFrame#jsonFieldRow {
                background: #ffffff;
                border: 1px solid #dce2ea;
                border-radius: 6px;
            }
            QLabel#outputPlaceholder {
                background: #f3f6fa;
                border: 1px dashed #bcc7d5;
                border-radius: 6px;
                color: #5e6b78;
                padding: 10px;
            }
            QLabel#typeBadge {
                background: #e8eef7;
                border-radius: 5px;
                color: #24466f;
                padding: 4px 8px;
            }
            QLabel#requiredBadge {
                background: #fff1d7;
                border-radius: 5px;
                color: #7c4d00;
                padding: 4px 8px;
            }
            QPushButton {
                min-height: 30px;
            }
            QPushButton#moduleButton {
                text-align: left;
                padding: 7px 10px;
                border: 1px solid #cfd7e3;
                border-radius: 6px;
                background: #ffffff;
                color: #223042;
            }
            QPushButton#moduleButton:hover {
                border-color: #2d6cdf;
                color: #1d4ed8;
            }
            """
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the SASSIE Qt prototype.")
    parser.add_argument(
        "--genapp-zazzie-root",
        type=Path,
        default=DEFAULT_GENAPP_ZAZZIE_ROOT,
        help="Path to the GenApp SASSIE/Zazzie repository.",
    )
    parser.add_argument(
        "--zazzie-root",
        type=Path,
        default=DEFAULT_ZAZZIE_ROOT,
        help="Path to the SASSIE/Zazzie source repository containing gui_mimic files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    configure_qt_plugin_paths()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("SASSIE Qt")
    app.setWindowIcon(load_application_icon())
    menu_groups = load_menu(args.genapp_zazzie_root)
    window = SassieQtPrototype(menu_groups, args.genapp_zazzie_root, args.zazzie_root)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
