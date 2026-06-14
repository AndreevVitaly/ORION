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
from portrait_core.mesh import project_semantic_points, validate_mesh


class LandmarkContractTestCase(unittest.TestCase):
    def test_manual_adapter_satisfies_contract(self):
        adapter = ManualAdapter()
        mesh = adapter.extract_mesh("test-image")
        points = adapter.extract_points("test-image")

        validate_mesh(mesh)
        self.assertEqual(set(points), set(REQUIRED_LANDMARKS))
        validate_landmarks(points)

    def test_missing_required_point_is_rejected(self):
        points = ManualAdapter().extract_points("test-image")
        del points["nose_tip"]

        with self.assertRaisesRegex(ValueError, "nose_tip"):
            validate_landmarks(points)

    def test_mediapipe_landmarks_are_converted_to_pixels(self):
        landmarks = [
            SimpleNamespace(x=0.0, y=0.0, z=0.0)
            for _ in range(478)
        ]
        landmarks[1] = SimpleNamespace(x=0.25, y=0.75, z=-0.1)

        mesh = MediaPipeAdapter.convert_mesh(
            landmarks,
            width=400,
            height=200,
            offset_x=10,
            offset_y=20,
            coordinate_scale=2,
        )
        points = project_semantic_points(mesh)

        self.assertEqual(mesh["schema"], "portrait-mesh")
        self.assertEqual(len(mesh["vertices"]), 478)
        self.assertEqual(mesh["source"]["topology"], "mediapipe-478")
        self.assertEqual(points["nose_tip"], [55.0, 85.0])
        self.assertEqual(mesh["vertices"][1][2], -20.0)

    def test_legacy_conversion_still_returns_named_points(self):
        landmarks = [
            SimpleNamespace(x=0.0, y=0.0, z=0.0)
            for _ in range(478)
        ]

        points = MediaPipeAdapter.convert_landmarks(
            landmarks,
            width=400,
            height=200,
        )

        self.assertEqual(set(points), set(REQUIRED_LANDMARKS))

    def test_invalid_image_size_is_rejected(self):
        landmarks = [SimpleNamespace(x=0.0, y=0.0) for _ in range(478)]

        with self.assertRaises(ValueError):
            MediaPipeAdapter.convert_landmarks(landmarks, width=0, height=200)

    def test_default_model_settings_are_explicit(self):
        adapter = MediaPipeAdapter("face_landmarker.task")

        self.assertEqual(adapter.min_detection_confidence, 0.35)
        self.assertEqual(adapter.min_presence_confidence, 0.5)
        self.assertEqual(adapter.min_image_size, 256)

    def test_candidate_regions_include_full_frame_and_center(self):
        regions = MediaPipeAdapter._candidate_regions(1000, 800)

        self.assertEqual(regions[0], (0, 0, 1000, 800))
        self.assertIn((160, 88, 840, 712), regions)
        self.assertEqual(len(regions), 10)

    def test_model_can_be_read_from_unicode_path(self):
        with tempfile.TemporaryDirectory(prefix="модель_") as directory:
            model = Path(directory) / "лицо.task"
            model.write_bytes(b"model-data")

            adapter = MediaPipeAdapter(str(model))

            self.assertEqual(adapter.model_path.read_bytes(), b"model-data")


if __name__ == "__main__":
    unittest.main()
