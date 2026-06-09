"""Тесты измерительного конвейера."""

import unittest

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.analyzer import analyze_points
from portrait_core.measurements.mouth import measure_mouth
from portrait_core.measurements.nose import measure_nose


class MeasurementTestCase(unittest.TestCase):
    def setUp(self):
        self.points = ManualAdapter().extract_points("test-image")

    def test_mouth_measurements_are_normalized_by_face_width(self):
        result = measure_mouth(self.points)

        self.assertEqual(result["mouth_width"], 100.0)
        self.assertAlmostEqual(result["mouth_width_ratio"], 100 / 240)
        self.assertAlmostEqual(
            result["lip_height_to_mouth_width_ratio"], 30 / 100
        )

    def test_nose_measurements_are_available(self):
        result = measure_nose(self.points)

        self.assertEqual(result["nose_length"], 60.0)
        self.assertEqual(result["nose_width"], 40.0)
        self.assertAlmostEqual(result["nose_width_to_length_ratio"], 2 / 3)

    def test_missing_points_produce_none_values(self):
        result = measure_nose({})

        self.assertIsNone(result["nose_length"])
        self.assertIsNone(result["nose_width_ratio"])

    def test_analyzer_returns_all_supported_zones(self):
        result = analyze_points(self.points)

        self.assertEqual(
            set(result["measurements"]),
            {"face", "eyes", "brows", "nose", "mouth", "jaw", "symmetry"},
        )
        self.assertEqual(result["morphology"]["symmetry"], "высокая симметрия")

    def test_normalized_measurements_do_not_depend_on_image_scale(self):
        scaled_points = {
            key: [coordinate * 2 for coordinate in point]
            for key, point in self.points.items()
        }

        original = analyze_points(self.points)["measurements"]
        scaled = analyze_points(scaled_points)["measurements"]

        self.assertAlmostEqual(
            original["face"]["face_width_to_height_ratio"],
            scaled["face"]["face_width_to_height_ratio"],
        )
        self.assertAlmostEqual(
            original["mouth"]["mouth_width_ratio"],
            scaled["mouth"]["mouth_width_ratio"],
        )
        self.assertAlmostEqual(
            original["jaw"]["jaw_width_ratio"],
            scaled["jaw"]["jaw_width_ratio"],
        )


if __name__ == "__main__":
    unittest.main()
