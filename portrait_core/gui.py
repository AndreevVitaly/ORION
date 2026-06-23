"""Desktop GUI для анализа и ручной правки точек лица."""

import json
import sys
from copy import deepcopy
from pathlib import Path

from PyQt6.QtCore import QObject, QPointF, Qt, QThread, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QPainter,
    QPen,
    QPixmap,
)
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

from portrait_core.dataset import build_draft_annotation
from portrait_core.pipeline import analyze_photo
from portrait_core.reporting import report_to_json, save_report
from portrait_core.visualization import draw_landmarks, landmark_color


MODEL_PATH = Path(__file__).parent / "models" / "face_landmarker.task"


class LandmarkEditor(QLabel):
    """Показать фото и дать вручную перетаскивать семантические точки."""

    points_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__("Фотография не выбрана")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(440, 400)
        self.setMouseTracking(True)
        self.setStyleSheet(
            "QLabel { background: #202124; color: #c8c9cc; border: 1px solid #3b3d40; }"
        )
        self.base_pixmap = None
        self.points = {}
        self.selected_name = None
        self.dragging_name = None
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def set_image(self, pixmap: QPixmap, points: dict | None = None):
        self.base_pixmap = pixmap
        self.points = {
            name: [float(point[0]), float(point[1])]
            for name, point in (points or {}).items()
        }
        self.selected_name = None
        self.dragging_name = None
        self._render()

    def current_points(self) -> dict:
        return {name: list(point) for name, point in self.points.items()}

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.points:
            return
        image_pos = self._widget_to_image(event.position())
        if image_pos is None:
            return
        nearest = self._nearest_point(image_pos)
        if nearest is None:
            return
        self.selected_name = nearest
        self.dragging_name = nearest
        self._move_point(nearest, image_pos)

    def mouseMoveEvent(self, event):
        if self.dragging_name:
            image_pos = self._widget_to_image(event.position())
            if image_pos is not None:
                self._move_point(self.dragging_name, image_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging_name:
            self.dragging_name = None
            self.points_changed.emit(self.current_points())

    def _render(self):
        if self.base_pixmap is None or self.base_pixmap.isNull():
            self.clear()
            self.setText("Фотография не выбрана")
            return

        target = self.size()
        scaled = self.base_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        canvas = QPixmap(target)
        canvas.fill(QColor("#202124"))
        self.offset_x = (target.width() - scaled.width()) / 2
        self.offset_y = (target.height() - scaled.height()) / 2
        self.scale = scaled.width() / self.base_pixmap.width()

        painter = QPainter(canvas)
        painter.drawPixmap(round(self.offset_x), round(self.offset_y), scaled)
        if self.points:
            self._draw_points(painter)
        painter.end()
        self.setPixmap(canvas)

    def _draw_points(self, painter: QPainter):
        radius = max(4, round(min(self.base_pixmap.size().width(), self.base_pixmap.size().height()) * self.scale / 160))
        font = painter.font()
        font.setPointSize(max(7, min(10, round(8 * self.scale + 5))))
        painter.setFont(font)

        for name, point in self.points.items():
            x, y = self._image_to_widget(point)
            color = QColor(landmark_color(name))
            if name == self.selected_name:
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(x, y), radius + 3, radius + 3)
            painter.setPen(QPen(QColor("#111111"), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(x, y), radius, radius)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(round(x + radius + 3), round(y - radius), name)

    def _image_to_widget(self, point):
        return (
            self.offset_x + point[0] * self.scale,
            self.offset_y + point[1] * self.scale,
        )

    def _widget_to_image(self, position: QPointF):
        if self.base_pixmap is None or self.scale == 0:
            return None
        x = (position.x() - self.offset_x) / self.scale
        y = (position.y() - self.offset_y) / self.scale
        if x < 0 or y < 0:
            return None
        if x > self.base_pixmap.width() or y > self.base_pixmap.height():
            return None
        return [float(x), float(y)]

    def _nearest_point(self, image_pos):
        best_name = None
        best_distance = None
        threshold = max(12, 14 / max(self.scale, 0.1))
        for name, point in self.points.items():
            distance = ((point[0] - image_pos[0]) ** 2 + (point[1] - image_pos[1]) ** 2) ** 0.5
            if best_distance is None or distance < best_distance:
                best_name = name
                best_distance = distance
        if best_distance is not None and best_distance <= threshold:
            return best_name
        return None

    def _move_point(self, name: str, image_pos):
        x = min(max(image_pos[0], 0.0), float(self.base_pixmap.width()))
        y = min(max(image_pos[1], 0.0), float(self.base_pixmap.height()))
        self.points[name] = [x, y]
        self._render()


class AnalysisWorker(QObject):
    """Выполнить тяжелый анализ вне GUI-потока."""

    completed = pyqtSignal(dict)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            _, report = analyze_photo(self.image_path, str(MODEL_PATH))
            self.completed.emit(report)
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
        self.points_dirty = False

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

        self.save_annotation_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            "Сохранить аннотацию",
            self,
        )
        self.save_annotation_action.setToolTip("Сохранить исправленные точки для датасета")
        self.save_annotation_action.setEnabled(False)
        self.save_annotation_action.triggered.connect(self.save_annotation)
        toolbar.addAction(self.save_annotation_action)

        self.save_preview_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon),
            "Сохранить изображение",
            self,
        )
        self.save_preview_action.setToolTip("Сохранить фото с текущими точками")
        self.save_preview_action.setEnabled(False)
        self.save_preview_action.triggered.connect(self.save_preview)
        toolbar.addAction(self.save_preview_action)

    def _build_content(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(12, 12, 6, 12)

        self.preview_label = LandmarkEditor()
        self.preview_label.points_changed.connect(self.points_edited)
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
        self.points_dirty = False
        self.preview_label.set_image(pixmap)
        self.summary_table.setRowCount(0)
        self.quality_table.setRowCount(0)
        self.json_view.clear()
        self.analyze_action.setEnabled(True)
        self.save_report_action.setEnabled(False)
        self.save_annotation_action.setEnabled(False)
        self.save_preview_action.setEnabled(False)
        self.statusBar().showMessage(Path(path).name)

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

    def analysis_completed(self, report: dict):
        self.report = report
        self.points_dirty = False
        self.preview_label.set_image(self.preview_pixmap, report["points"])
        self._fill_summary(report)
        self._fill_quality(report["quality"])
        self.json_view.setPlainText(report_to_json(report))
        self.save_report_action.setEnabled(True)
        self.save_annotation_action.setEnabled(True)
        self.save_preview_action.setEnabled(True)
        self.statusBar().showMessage("Анализ завершен. Точки можно перетаскивать мышкой.")

    def analysis_failed(self, message: str):
        self.statusBar().showMessage("Анализ не выполнен")
        QMessageBox.warning(self, "Не удалось выполнить анализ", message)

    def points_edited(self, points: dict):
        if not self.report:
            return
        self.points_dirty = True
        self.report["points"] = points
        self.statusBar().showMessage(
            "Разметка изменена. Сохраните аннотацию для датасета."
        )

    def _fill_summary(self, report: dict):
        morphology = report["morphology"]
        symmetry = report["measurements"]["symmetry"]["overall_score"]
        quality = report["quality"]
        interpretation = report.get("interpretation", {})
        symmetry_text = interpretation.get("symmetry", {}).get(
            "text", "нет данных"
        )
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
            ("Описание симметрии", symmetry_text),
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

    def save_annotation(self):
        if not self.report or not self.image_path:
            return
        default_name = f"{Path(self.image_path).stem}_annotation.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить аннотацию", default_name, "JSON (*.json)"
        )
        if not path:
            return

        mesh = self._mesh_with_current_points()
        annotation = build_draft_annotation(
            self.image_path,
            mesh,
            subject_id=Path(self.image_path).stem,
            split="train",
            consent_version="v1",
            annotator_id="gui",
        )
        annotation["semantic_points"] = self.preview_label.current_points()
        annotation["review"]["notes"] = (
            "Ручная разметка из GUI; точки можно использовать для проверки датасета."
        )
        Path(path).write_text(
            json.dumps(annotation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.points_dirty = False
        self.statusBar().showMessage(f"Аннотация сохранена: {path}")

    def _mesh_with_current_points(self) -> dict:
        mesh = deepcopy(self.report.get("mesh"))
        if not mesh:
            raise ValueError("В отчете нет сетки для сохранения аннотации")
        points = self.preview_label.current_points()
        for name, point in points.items():
            index = mesh["semantic_map"].get(name)
            if index is None:
                continue
            vertex = list(mesh["vertices"][index])
            vertex[0] = float(point[0])
            vertex[1] = float(point[1])
            mesh["vertices"][index] = vertex
        mesh["source"] = dict(mesh["source"])
        mesh["source"]["adapter"] = f'{mesh["source"].get("adapter", "unknown")}+gui-review'
        return mesh

    def save_preview(self):
        if not self.report:
            return
        default_name = f"{Path(self.image_path).stem}_landmarks.jpg"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение с точками",
            default_name,
            "JPEG (*.jpg);;PNG (*.png)",
        )
        if path:
            draw_landmarks(self.image_path, self.preview_label.current_points()).save(path)
            self.statusBar().showMessage(f"Изображение сохранено: {path}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ПОРТРЕТ")
    app.setStyle("Fusion")
    window = PortraitWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
