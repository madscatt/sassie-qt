"""First SASSIE Qt prototype.

This app reads the canonical GenApp menu and module JSON definitions while
incrementally replacing the GenApp layer with native Qt workflows.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Callable

import PySide6
from PySide6.QtCore import QRect, QThread, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
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
from sassie_qt.runners.data_interpolation_runner import (
    DataInterpolationInput,
    DataInterpolationResult,
    DataInterpolationRunner,
)


APPLICATION_ICON_PATH = Path(__file__).resolve().parent / "assets" / "sassie_icon.png"


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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.menu_item = menu_item
        self.module_definition = module_definition
        self.gui_mimic_path = gui_mimic_path
        self.project_directory = project_directory
        self.input_rows: dict[str, JsonFieldRow] = {}
        self.output_rows: dict[str, JsonFieldRow] = {}
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

        views = self.menu_item.views or ("Input", "Output", "Plots", "OpenGL")
        view_tabs = QTabWidget()
        view_tabs.setObjectName("viewTabs")
        self.view_tabs = view_tabs
        for view_name in views:
            view_tabs.addTab(self._build_view(view_name), view_name)
        outer_layout.addWidget(view_tabs, 1)

    def _build_view(self, view_name: str) -> QWidget:
        if view_name.lower() == "input":
            return self._build_field_preview(role="input")
        if view_name.lower() == "output":
            return self._build_field_preview(role="output")

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
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
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
            if field.field_type == "label":
                layout.addWidget(JsonSectionLabel(field.label))
            else:
                row = JsonFieldRow(
                    field,
                    role,
                    project_directory_provider=lambda: self.project_directory,
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
            self.run_log_text.setReadOnly(True)
            self.run_log_text.setMinimumHeight(160)
            layout.addWidget(self.run_log_text)
        layout.addStretch(1)
        scroll_area.setWidget(container)
        return scroll_area

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

    def _handle_run_failure(self, error: str) -> None:
        self._append_run_log(f"\nRun failed:\n{error}\n")
        self._show_error(error)

    def _clear_active_worker(self) -> None:
        self.active_worker = None

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "Data Interpolation", message)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Data Interpolation Failed", message)


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


class JsonFieldRow(QFrame):
    """A compact stub widget row for one GenApp JSON field."""

    def __init__(
        self,
        field: ModuleField,
        role: str,
        project_directory_provider: Callable[[], Path] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.field = field
        self.role = role
        self.project_directory_provider = project_directory_provider
        self.value_widget: QWidget | None = None
        self.setObjectName("jsonFieldRow")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        name = QLabel(field.label)
        name.setMinimumWidth(240)
        name.setWordWrap(True)
        if field.help_text:
            name.setToolTip(field.help_text)
        layout.addWidget(name, 1)

        layout.addWidget(self._build_control(), 3)

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
            _dialog_start_directory(line_edit.text()),
        )
        if file_path:
            try:
                project_file_path = self._copy_file_to_project_directory(Path(file_path))
            except OSError as error:
                QMessageBox.critical(
                    self,
                    "File Upload Failed",
                    f"Could not copy the selected file into the project directory:\n{error}",
                )
                return
            line_edit.setText(str(project_file_path))

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
        self.project_directory = Path.cwd()
        self.module_tabs = QTabWidget()
        self.category_list = QListWidget()
        self.project_directory_edit: QLineEdit | None = None

        self.setWindowTitle("SASSIE Qt Prototype")
        self.setWindowIcon(load_application_icon())
        self.resize(1180, 760)
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
