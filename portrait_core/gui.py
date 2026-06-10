"""Desktop GUI для анализа фотографий."""

import sys
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from portrait_core.pipeline import analyze_photo
from portrait_core.reporting import report_to_json, save_report
from portrait_core.visualization import draw_landmarks


MODEL_PATH = Path(__file__).parent / "models" / "face_landmarker.task"


def pil_to_pixmap(image) -> QPixmap:
    """Преобразовать PIL.Image в независимый QPixmap."""
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimage = QImage(
        data,
        rgba.width,
        rgba.height,
        rgba.width * 4,
        QImage.Format.Format_RGBA8888,
    ).copy()
    return QPixmap.fromImage(qimage)


class AnalysisWorker(QObject):
    """Выполнить тяжелый анализ вне GUI-потока."""

    completed = pyqtSignal(dict, object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            points, report = analyze_photo(self.image_path, str(MODEL_PATH))
            preview = draw_landmarks(self.image_path, points)
            self.completed.emit(report, preview)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


class PortraitWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.image_path = None
        self.report = None
        self.preview_pixmap = None
        self.analysis_thread = None
        self.worker = None

        self.setWindowTitle("ПОРТРЕТ")
        self.resize(1180, 760)
        self.setMinimumSize(900, 600)

        self._build_toolbar()
        self._build_content()
        self.statusBar().showMessage("Выберите фотографию")

    def _build_toolbar(self):
        toolbar = QToolBar("Основные действия")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        self.open_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            "Открыть",
            self,
        )
        self.open_action.setToolTip("Выбрать фотографию")
        self.open_action.triggered.connect(self.open_image)
        toolbar.addAction(self.open_action)

        self.analyze_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay),
            "Анализировать",
            self,
        )
        self.analyze_action.setToolTip("Найти точки и выполнить измерения")
        self.analyze_action.setEnabled(False)
        self.analyze_action.triggered.connect(self.start_analysis)
        toolbar.addAction(self.analyze_action)

        toolbar.addSeparator()

        self.save_report_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            "Сохранить JSON",
            self,
        )
        self.save_report_action.setEnabled(False)
        self.save_report_action.triggered.connect(self.save_json)
        toolbar.addAction(self.save_report_action)

        self.save_preview_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon),
            "Сохранить разметку",
            self,
        )
        self.save_preview_action.setEnabled(False)
        self.save_preview_action.triggered.connect(self.save_preview)
        toolbar.addAction(self.save_preview_action)

    def _build_content(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(12, 12, 6, 12)

        self.preview_label = QLabel("Фотография не выбрана")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(440, 400)
        self.preview_label.setStyleSheet(
            "QLabel { background: #202124; color: #c8c9cc; border: 1px solid #3b3d40; }"
        )
        preview_layout.addWidget(self.preview_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        preview_layout.addWidget(self.progress)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(["Параметр", "Результат"])
        self.summary_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.summary_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.summary_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.summary_table, "Сводка")

        self.quality_table = QTableWidget(0, 2)
        self.quality_table.setHorizontalHeaderLabels(["Проверка", "Результат"])
        self.quality_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.quality_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.quality_table.verticalHeader().setVisible(False)
        self.quality_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.quality_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.quality_table, "Качество")

        self.json_view = QTextEdit()
        self.json_view.setReadOnly(True)
        self.json_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.tabs.addTab(self.json_view, "JSON")

        result_panel = QWidget()
        result_layout = QVBoxLayout(result_panel)
        result_layout.setContentsMargins(6, 12, 12, 12)
        result_layout.addWidget(self.tabs)

        splitter.addWidget(preview_panel)
        splitter.addWidget(result_panel)
        splitter.setSizes([650, 530])
        self.setCentralWidget(splitter)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фотографию",
            "",
            "Изображения (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if not path:
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть изображение")
            return

        self.image_path = path
        self.report = None
        self.preview_pixmap = pixmap
        self._show_pixmap()
        self.summary_table.setRowCount(0)
        self.quality_table.setRowCount(0)
        self.json_view.clear()
        self.analyze_action.setEnabled(True)
        self.save_report_action.setEnabled(False)
        self.save_preview_action.setEnabled(False)
        self.statusBar().showMessage(Path(path).name)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._show_pixmap()

    def _show_pixmap(self):
        if not self.preview_pixmap:
            return
        target = self.preview_label.size()
        scaled = self.preview_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def start_analysis(self):
        if not self.image_path:
            return

        self._set_busy(True)
        self.analysis_thread = QThread(self)
        self.worker = AnalysisWorker(self.image_path)
        self.worker.moveToThread(self.analysis_thread)
        self.analysis_thread.started.connect(self.worker.run)
        self.worker.completed.connect(self.analysis_completed)
        self.worker.failed.connect(self.analysis_failed)
        self.worker.finished.connect(self.analysis_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
        self.analysis_thread.finished.connect(lambda: self._set_busy(False))
        self.analysis_thread.start()

    def _set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        self.open_action.setEnabled(not busy)
        self.analyze_action.setEnabled(not busy and bool(self.image_path))
        if busy:
            self.statusBar().showMessage("Выполняется анализ...")

    def analysis_completed(self, report: dict, preview):
        self.report = report
        self.preview_pixmap = pil_to_pixmap(preview)
        self._show_pixmap()
        self._fill_summary(report)
        self._fill_quality(report["quality"])
        self.json_view.setPlainText(report_to_json(report))
        self.save_report_action.setEnabled(True)
        self.save_preview_action.setEnabled(True)
        self.statusBar().showMessage("Анализ завершен")

    def analysis_failed(self, message: str):
        self.statusBar().showMessage("Анализ не выполнен")
        QMessageBox.warning(self, "Не удалось выполнить анализ", message)

    def _fill_summary(self, report: dict):
        morphology = report["morphology"]
        symmetry = report["measurements"]["symmetry"]["overall_score"]
        quality = report["quality"]
        quality_text = (
            "подходит"
            if quality["status"] == "passed"
            else "; ".join(quality["issues"])
        )
        rows = [
            ("Качество кадра", quality_text),
            ("Пропорция лица", morphology["face_proportion"]),
            ("Ширина челюсти", morphology["jaw_width"]),
            ("Ширина рта", morphology["mouth_width"]),
            ("Симметрия", morphology["symmetry"]),
            (
                "Индекс симметрии",
                "нет данных" if symmetry is None else f"{symmetry:.3f}",
            ),
            (
                "Наклон головы",
                f'{quality["metrics"]["roll_degrees"]:.1f}°',
            ),
            (
                "Доля лица в кадре",
                f'{quality["metrics"]["face_coverage"]:.1%}',
            ),
        ]

        self.summary_table.setRowCount(len(rows))
        for row, (name, value) in enumerate(rows):
            self.summary_table.setItem(row, 0, QTableWidgetItem(name))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _fill_quality(self, quality: dict):
        labels = {
            "head_roll": "Наклон головы",
            "head_yaw": "Поворот головы",
            "sharpness": "Резкость",
            "brightness": "Яркость",
            "contrast": "Контраст",
            "face_size": "Размер лица",
            "neutral_expression": "Нейтральное выражение",
            "resolution": "Разрешение",
        }
        rows = [
            (labels[name], "пройдено" if passed else "предупреждение")
            for name, passed in quality["checks"].items()
        ]
        self.quality_table.setRowCount(len(rows))
        for row, (name, value) in enumerate(rows):
            self.quality_table.setItem(row, 0, QTableWidgetItem(name))
            self.quality_table.setItem(row, 1, QTableWidgetItem(value))

    def save_json(self):
        if not self.report:
            return
        default_name = f"{Path(self.image_path).stem}_portrait.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", default_name, "JSON (*.json)"
        )
        if path:
            save_report(self.report, path)
            self.statusBar().showMessage(f"Отчет сохранен: {path}")

    def save_preview(self):
        if not self.report:
            return
        default_name = f"{Path(self.image_path).stem}_landmarks.jpg"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить размеченную фотографию",
            default_name,
            "JPEG (*.jpg);;PNG (*.png)",
        )
        if path:
            draw_landmarks(self.image_path, self.report["points"]).save(path)
            self.statusBar().showMessage(f"Разметка сохранена: {path}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ПОРТРЕТ")
    app.setStyle("Fusion")
    window = PortraitWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
