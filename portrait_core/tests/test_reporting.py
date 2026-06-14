"""Тесты отчета и визуализации."""

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.analyzer import analyze_points
from portrait_core.reporting import build_report, report_to_json, save_report
from portrait_core.visualization import draw_landmarks, landmark_color


class ReportingTestCase(unittest.TestCase):
    def setUp(self):
        self.points = ManualAdapter().extract_points("test-image")
        self.analysis = analyze_points(self.points)

    def test_report_is_serializable_and_contains_schema(self):
        mesh = ManualAdapter().extract_mesh("test-image")
        report = build_report(
            "photo.jpg",
            self.points,
            self.analysis,
            mesh=mesh,
        )
        restored = json.loads(report_to_json(report))

        self.assertEqual(restored["schema_version"], 3)
        self.assertIn("measurements", restored)
        self.assertIn("points", restored)
        self.assertEqual(restored["mesh"]["schema"], "portrait-mesh")

    def test_report_can_be_saved(self):
        report = build_report("photo.jpg", self.points, self.analysis)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            save_report(report, output)

            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["schema_version"],
                3,
            )

    def test_landmarks_are_drawn_on_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            Image.new("RGB", (500, 500), "black").save(source)

            rendered = draw_landmarks(source, self.points)

            self.assertEqual(rendered.size, (500, 500))
            self.assertNotEqual(rendered.getpixel((240, 270)), (0, 0, 0))

    def test_zone_colors_are_stable(self):
        self.assertEqual(landmark_color("nose_tip"), "#E09F00")
        self.assertEqual(landmark_color("mouth_left"), "#E5484D")


if __name__ == "__main__":
    unittest.main()
