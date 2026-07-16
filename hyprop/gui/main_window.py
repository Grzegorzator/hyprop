"""PySide6 main window (stage E12) - a thin view over SessionViewModel.

Tabs: input forms (generated from viewmodel.FORM_LAYOUT), Results
(summary table + matplotlib plots with ROP markers), and toolbar
actions: Open / Save / Run / Export / Report. The transient runs in a
worker thread to keep the UI responsive; the CEA table build makes the
first run take ~20-30 s (subsequent runs are cached).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QToolBar,
    QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from hyprop.gui.viewmodel import FORM_LAYOUT, SessionViewModel


class _RunWorker(QThread):
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, viewmodel: SessionViewModel) -> None:
        super().__init__()
        self._vm = viewmodel

    def run(self) -> None:                                # pragma: no cover
        try:
            self._vm.run()
            self.finished_ok.emit()
        except Exception as exc:                          # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """HyProp GUI: forms -> run -> plots/ROP -> export/report."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HyProp - Hybrid Rocket Sizing")
        self.resize(1150, 750)
        self.vm = SessionViewModel()
        self._fields: dict = {}

        toolbar = QToolBar(); self.addToolBar(toolbar)
        for label, slot in (("Open...", self._open), ("Save...", self._save),
                            ("Run", self._run), ("Export...", self._export),
                            ("Report...", self._report)):
            button = QPushButton(label); button.clicked.connect(slot)
            toolbar.addWidget(button)
        self.status = QLabel("Open an EngineConfig YAML to begin.")
        toolbar.addWidget(self.status)

        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        for tab_name, rows in FORM_LAYOUT.items():
            page = QWidget(); form = QFormLayout(page)
            for path, label, unit in rows:
                edit = QLineEdit(); edit.setObjectName(path)
                edit.editingFinished.connect(
                    lambda p=path, e=edit: self.vm.set(p, e.text()))
                form.addRow(f"{label} [{unit}]", edit)
                self._fields[path] = edit
            self.tabs.addTab(page, tab_name)

        results = QWidget(); layout = QVBoxLayout(results)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Quantity", "Value"])
        self.canvas = FigureCanvasQTAgg(Figure(figsize=(9, 5)))
        layout.addWidget(self.table, 1); layout.addWidget(self.canvas, 3)
        self.tabs.addTab(results, "Results")

    # ------------------------------------------------------------ slots
    def _open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open config", "", "YAML (*.yaml *.yml)")
        if not path:
            return
        self.vm.load(path)
        for field_path, edit in self._fields.items():
            try:
                value = self.vm.get(field_path)
                edit.setText("" if value is None else str(value))
            except (KeyError, TypeError):
                edit.setText("")
        self.status.setText(f"Loaded {Path(path).name}")

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save config", "", "YAML (*.yaml)")
        if path:
            self.vm.save(path); self.status.setText(f"Saved {path}")

    def _run(self) -> None:
        error = self.vm.validate()
        if error:
            QMessageBox.warning(self, "Invalid config", error); return
        self.status.setText("Running (first run builds the CEA table)...")
        self._worker = _RunWorker(self.vm)
        self._worker.finished_ok.connect(self._show_results)
        self._worker.failed.connect(
            lambda msg: QMessageBox.critical(self, "Run failed", msg))
        self._worker.start()

    def _show_results(self) -> None:
        rows = self.vm.summary_rows()
        self.table.setRowCount(len(rows))
        for index, (key, value) in enumerate(rows):
            self.table.setItem(index, 0, QTableWidgetItem(key))
            self.table.setItem(index, 1, QTableWidgetItem(value))
        figure = self.canvas.figure; figure.clear()
        df = self.vm.result.history.to_dataframe()
        lro = self.vm.result.event_time("liquid_runout")
        for position, (column, title, scale) in enumerate((
                ("thrust", "Thrust [N]", 1.0), ("pc", "Pc [bar]", 1e5),
                ("of", "O/F [-]", 1.0), ("impulse", "It [Ns]", 1.0))):
            axes = figure.add_subplot(2, 2, position + 1)
            axes.plot(df.t, df[column] / scale)
            if lro:
                axes.axvline(lro, ls="--", color="r", alpha=0.6)
            axes.set_title(title); axes.grid(alpha=0.3)
        figure.tight_layout(); self.canvas.draw()
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
        self.status.setText("Done.")

    def _export(self) -> None:
        if self.vm.result is None:
            QMessageBox.information(self, "No results", "Run first."); return
        directory = QFileDialog.getExistingDirectory(self, "Export to...")
        if directory:
            files = self.vm.export(directory)
            self.status.setText(f"Exported {len(files)} files.")

    def _report(self) -> None:
        if self.vm.result is None:
            QMessageBox.information(self, "No results", "Run first."); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Report", "report.tex", "LaTeX/PDF (*.tex)")
        if path:
            out = self.vm.report(path)
            self.status.setText(f"Report: {out}")
