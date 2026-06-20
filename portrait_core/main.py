"""Запуск портретного анализа с ручными точками или фотографией."""

import argparse
import sys
from pathlib import Path

# Поддерживаем запуск как модуля и напрямую через кнопку Run в IDE.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portrait_core.adapters.factory import create_mesh_adapter
from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.analyzer import analyze_points
from portrait_core.pipeline import analyze_photo_with_adapter
from portrait_core.reporting import (
    build_report,
    format_summary_report,
    report_to_json,
    save_report,
)


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parent / "models" / "face_landmarker.task"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Объективный морфологический анализ лица"
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Путь к фотографии. Без аргумента открывается GUI.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Использовать встроенные тестовые точки без фотографии.",
    )
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL_PATH),
        help="Путь к модели выбранного backend.",
    )
    parser.add_argument(
        "--backend",
        choices=("mediapipe", "onnx"),
        default="mediapipe",
        help="Поставщик плотной сетки лица.",
    )
    parser.add_argument(
        "--topology",
        help="Путь к JSON-sidecar собственной ONNX-модели.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Напечатать полный технический JSON вместо краткой сводки.",
    )
    parser.add_argument(
        "--output",
        help="Сохранить полный JSON-отчет в файл.",
    )
    return parser


def main():
    """Получить точки лица и вывести объективные измерения."""
    args = build_parser().parse_args()
    if args.image:
        adapter = create_mesh_adapter(
            args.backend,
            args.model,
            args.topology,
        )
        _, result = analyze_photo_with_adapter(args.image, adapter)
    elif args.demo:
        adapter = ManualAdapter()
        points = adapter.extract_points("manual-test-image")
        result = build_report(
            "manual-test-image",
            points,
            analyze_points(points),
        )
    else:
        from portrait_core.gui import main as run_gui

        return run_gui()

    if args.output:
        save_report(result, args.output)
    if args.json:
        print(report_to_json(result))
    else:
        print(format_summary_report(result))


if __name__ == "__main__":
    main()
