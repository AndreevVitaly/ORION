"""Тесты пакетной обработки."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from portrait_core.batch import analyze_directory


class BatchTestCase(unittest.TestCase):
    @patch("portrait_core.batch.analyze_photo")
    def test_batch_saves_summary_and_report(self, analyze_photo_mock):
        analyze_photo_mock.return_value = (
            {},
            {
                "quality": {"status": "passed", "issues": []},
                "morphology": {
                    "face_proportion": "среднее",
                    "symmetry": "высокая симметрия",
                },
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            output = Path(directory) / "output"
            source.mkdir()
            Image.new("RGB", (300, 300), "white").save(source / "face.jpg")

            rows = analyze_directory(source, output, "model.task")

            self.assertEqual(rows[0]["status"], "passed")
            self.assertTrue((output / "summary.csv").is_file())
            self.assertTrue((output / "summary.json").is_file())
            self.assertTrue((output / "face_portrait.json").is_file())

    @patch("portrait_core.batch.analyze_photo")
    def test_batch_marks_exact_duplicates(self, analyze_photo_mock):
        analyze_photo_mock.return_value = (
            {},
            {
                "quality": {"status": "passed", "issues": []},
                "morphology": {
                    "face_proportion": "среднее",
                    "symmetry": "высокая симметрия",
                },
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            output = Path(directory) / "output"
            source.mkdir()
            image = Image.new("RGB", (300, 300), "white")
            image.save(source / "first.jpg")
            image.save(source / "second.jpg")

            rows = analyze_directory(source, output, "model.task")

        self.assertEqual(rows[1]["status"], "duplicate")
        self.assertEqual(rows[1]["duplicate_of"], "first.jpg")
        self.assertEqual(analyze_photo_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
