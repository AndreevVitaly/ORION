"""Тест независимости конвейера от конкретного детектора."""

import unittest
from unittest.mock import patch

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.pipeline import analyze_photo_with_adapter


class PipelineTestCase(unittest.TestCase):
    @patch("portrait_core.pipeline.assess_image_quality")
    def test_pipeline_accepts_generic_mesh_adapter(self, quality_mock):
        quality_mock.return_value = {
            "status": "passed",
            "issues": [],
            "checks": {},
            "metrics": {},
        }

        points, report = analyze_photo_with_adapter(
            "photo.jpg",
            ManualAdapter(),
        )

        self.assertEqual(report["mesh"]["source"]["adapter"], "manual")
        self.assertEqual(report["points"], points)
        self.assertIn("measurements", report)
        self.assertIn("canonical_mesh", report)
        self.assertIn("features", report)
        self.assertIn("profile", report)


if __name__ == "__main__":
    unittest.main()
