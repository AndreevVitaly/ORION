"""Тесты контракта точек и преобразования MediaPipe."""

import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.adapters.mediapipe_adapter import (
    MediaPipeAdapter,
)
from portrait_core.landmarks import REQUIRED_LANDMARKS, validate_landmarks


class LandmarkContractTestCase(unittest.TestCase):
    def test_manual_adapter_satisfies_contract(self):
        points = ManualAdapter().extract_points("test-image")

        self.assertEqual(set(points), set(REQUIRED_LANDMARKS))
        validate_landmarks(points)

    def test_missing_required_point_is_rejected(self):
        points = ManualAdapter().extract_points("test-image")
        del points["nose_tip"]

        with self.assertRaisesRegex(ValueError, "nose_tip"):
            validate_landmarks(points)

    def test_mediapipe_landmarks_are_converted_to_pixels(self):
        landmarks = [SimpleNamespace(x=0.0, y=0.0) for _ in range(478)]
        landmarks[1] = SimpleNamespace(x=0.25, y=0.75)

        points = MediaPipeAdapter.convert_landmarks(
            landmarks, width=400, height=200
        )

        self.assertEqual(points["nose_tip"], [100.0, 150.0])

    def test_invalid_image_size_is_rejected(self):
        landmarks = [SimpleNamespace(x=0.0, y=0.0) for _ in range(478)]

        with self.assertRaises(ValueError):
            MediaPipeAdapter.convert_landmarks(landmarks, width=0, height=200)

    def test_default_model_settings_are_explicit(self):
        adapter = MediaPipeAdapter("face_landmarker.task")

        self.assertEqual(adapter.min_detection_confidence, 0.5)
        self.assertEqual(adapter.min_presence_confidence, 0.5)
        self.assertEqual(adapter.min_image_size, 256)

    def test_model_can_be_read_from_unicode_path(self):
        with tempfile.TemporaryDirectory(prefix="модель_") as directory:
            model = Path(directory) / "лицо.task"
            model.write_bytes(b"model-data")

            adapter = MediaPipeAdapter(str(model))

            self.assertEqual(adapter.model_path.read_bytes(), b"model-data")


if __name__ == "__main__":
    unittest.main()
