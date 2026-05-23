"""Минимальные тесты геометрических функций."""

import unittest

from portrait_core.measurements.geometry import (
    distance,
    horizontal_distance,
    midpoint,
    ratio,
    vertical_distance,
)


class GeometryTestCase(unittest.TestCase):
    """Простые проверки базовых геометрических функций."""

    def test_distance_between_points(self):
        """Проверить расчет расстояния по классическому треугольнику 3-4-5."""
        self.assertEqual(distance([0, 0], [3, 4]), 5)

    def test_midpoint_between_points(self):
        """Проверить расчет середины между двумя точками."""
        self.assertEqual(midpoint([0, 0], [10, 10]), [5, 5])

    def test_ratio_with_regular_divisor(self):
        """Проверить обычное деление."""
        self.assertEqual(ratio(10, 2), 5)

    def test_ratio_with_zero_divisor(self):
        """Проверить безопасное деление на ноль."""
        self.assertEqual(ratio(10, 0), 0.0)

    def test_horizontal_distance(self):
        """Проверить расстояние только по оси X."""
        self.assertEqual(horizontal_distance([2, 5], [10, 5]), 8)

    def test_vertical_distance(self):
        """Проверить расстояние только по оси Y."""
        self.assertEqual(vertical_distance([2, 5], [2, 12]), 7)


if __name__ == "__main__":
    unittest.main()
