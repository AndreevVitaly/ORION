"""Простой запуск ядра портретного анализа без внешних библиотек."""

from pprint import pprint

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.measurements.eyes import calculate_eye_measurements
from portrait_core.measurements.face import calculate_face_measurements


def main():
    """Получить тестовые точки и вывести базовые измерения."""
    adapter = ManualAdapter()
    points = adapter.extract_points("manual-test-image")

    face_measurements = calculate_face_measurements(points)
    eye_measurements = calculate_eye_measurements(points)

    result = {
        "face": face_measurements,
        "eyes": eye_measurements,
    }

    pprint(result, sort_dicts=False)


if __name__ == "__main__":
    main()
