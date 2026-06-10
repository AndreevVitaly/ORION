"""Тесты оценки качества фотографии."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.quality import assess_image_quality


class QualityTestCase(unittest.TestCase):
    def setUp(self):
        self.points = ManualAdapter().extract_points("test-image")

    def _create_image(self, directory, name, size=(500, 500)):
        path = Path(directory) / name
        image = Image.new("L", size)
        pixels = image.load()
        for y in range(size[1]):
            for x in range(size[0]):
                pixels[x, y] = 40 if (x // 10 + y // 10) % 2 else 210
        image.convert("RGB").save(path)
        return path

    def test_quality_contains_all_expected_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            image = self._create_image(directory, "quality.png")
            result = assess_image_quality(image, self.points)

        self.assertEqual(
            set(result["checks"]),
            {
                "head_roll",
                "head_yaw",
                "sharpness",
                "brightness",
                "contrast",
                "face_size",
                "neutral_expression",
                "resolution",
            },
        )

    def test_tilted_eye_line_is_reported(self):
        points = dict(self.points)
        points["right_eye_inner"] = [275, 245]
        points["right_eye_outer"] = [325, 245]
        with tempfile.TemporaryDirectory() as directory:
            image = self._create_image(directory, "tilted.png")
            result = assess_image_quality(image, points)

        self.assertFalse(result["checks"]["head_roll"])
        self.assertIn("сильный наклон головы", result["issues"])

    def test_small_source_is_reported_without_blocking_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            image = self._create_image(
                directory, "small.png", size=(236, 300)
            )
            result = assess_image_quality(image, self.points)

        self.assertFalse(result["checks"]["resolution"])
        self.assertIn(
            "низкое исходное разрешение фотографии", result["issues"]
        )


if __name__ == "__main__":
    unittest.main()
