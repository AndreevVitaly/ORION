"""Запуск портретного анализа с ручными точками или фотографией."""

import argparse
from pprint import pprint

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.adapters.mediapipe_adapter import MediaPipeAdapter
from portrait_core.analyzer import analyze_points


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Объективный морфологический анализ лица"
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Путь к фотографии. Без аргумента используются тестовые точки.",
    )
    parser.add_argument(
        "--model",
        default="portrait_core/models/face_landmarker.task",
        help="Путь к модели MediaPipe Face Landmarker.",
    )
    return parser


def main():
    """Получить точки лица и вывести объективные измерения."""
    args = build_parser().parse_args()
    if args.image:
        adapter = MediaPipeAdapter(args.model)
        points = adapter.extract_points(args.image)
    else:
        adapter = ManualAdapter()
        points = adapter.extract_points("manual-test-image")

    result = analyze_points(points)
    pprint(result, sort_dicts=False)


if __name__ == "__main__":
    main()
