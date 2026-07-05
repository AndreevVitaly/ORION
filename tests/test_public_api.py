"""Тесты официального API portrait_core."""

import unittest
from unittest.mock import patch

import portrait_core


class PublicApiTestCase(unittest.TestCase):
    def test_public_api_exports_scientific_engine_entrypoints(self):
        self.assertTrue(callable(portrait_core.analyze))
        self.assertTrue(callable(portrait_core.process_face))
        self.assertTrue(callable(portrait_core.create_portrait_report))

    @patch("portrait_core.api.analyze_photo_with_adapter")
    @patch("portrait_core.api.create_mesh_adapter")
    def test_create_portrait_report_uses_configured_adapter(self, adapter_mock, pipeline_mock):
        adapter = object()
        adapter_mock.return_value = adapter
        pipeline_mock.return_value = ({"nose_tip": [1, 2]}, {"schema_version": 3})

        report = portrait_core.create_portrait_report(
            "photo.jpg",
            backend="onnx",
            model_path="model.onnx",
            topology_path="model.json",
        )

        self.assertEqual(report, {"schema_version": 3})
        adapter_mock.assert_called_once_with("onnx", "model.onnx", "model.json")
        pipeline_mock.assert_called_once_with("photo.jpg", adapter)


if __name__ == "__main__":
    unittest.main()
