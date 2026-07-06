"""Тесты приложения Dataset Builder."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apps.dataset_builder.builder import build_dataset


class DatasetBuilderAppTestCase(unittest.TestCase):
    @patch("apps.dataset_builder.builder.create_portrait_report")
    def test_dataset_builder_delegates_face_analysis_to_portrait_core(self, report_mock):
        report_mock.return_value = {
            "schema_version": 3,
            "quality": {
                "status": "passed",
                "issues": [],
            },
            "lic_core": {},
            "morphology": {},
            "measurements": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "frame001.jpg"
            image.write_bytes(b"not a real image; core is mocked")
            output = root / "dataset"

            summary = build_dataset(str(root), str(output), model_path="model.task")

            report_path = output / "passed" / "frame001_portrait.json"
            copied_image = output / "passed" / "frame001.jpg"

            self.assertEqual(summary["created_reports"], 1)
            self.assertEqual(summary["statuses"]["passed"], 1)
            self.assertTrue(report_path.exists())
            self.assertTrue(copied_image.exists())
            report_mock.assert_called_once()
            self.assertEqual(report_mock.call_args.kwargs["model_path"], "model.task")

    @patch("apps.dataset_builder.builder.create_portrait_report")
    def test_dataset_builder_emits_log_and_progress_callbacks(self, report_mock):
        report_mock.return_value = {
            "schema_version": 3,
            "quality": {
                "status": "warning",
                "issues": ["test warning"],
            },
        }
        logs = []
        progress = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "frame001.jpg").write_bytes(b"one")
            (root / "frame002.jpg").write_bytes(b"two")
            output = root / "dataset"

            summary = build_dataset(
                str(root),
                str(output),
                log=logs.append,
                progress=lambda current, total: progress.append((current, total)),
            )

        self.assertEqual(summary["created_reports"], 2)
        self.assertEqual(progress[-1], (2, 2))
        self.assertTrue(any("portrait_core" in message for message in logs))


if __name__ == "__main__":
    unittest.main()
