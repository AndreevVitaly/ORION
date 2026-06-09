"""Простой запуск ядра портретного анализа без внешних библиотек."""

from pprint import pprint

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.analyzer import analyze_points


def main():
    """Получить тестовые точки и вывести базовые измерения."""
    adapter = ManualAdapter()
    points = adapter.extract_points("manual-test-image")

    result = analyze_points(points)
    pprint(result, sort_dicts=False)


if __name__ == "__main__":
    main()
