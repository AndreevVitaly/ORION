"""Тесты подготовки собственного landmark-датасета."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.dataset import (
    audit_annotations,
    build_draft_annotation,
)


class DatasetTestCase(unittest.TestCase):
    def test_mesh_can_become_reviewable_draft(self):
        mesh = ManualAdapter().extract_mesh("test-image")
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "face.png"
            Image.new("RGB", (480, 500), "white").save(image_path)
            annotation = build_draft_annotation(
                image_path,
                mesh,
                subject_id="subject-1",
                split="train",
                consent_version="v1",
                annotator_id="auto",
            )

        self.assertEqual(annotation["review"]["status"], "draft")
        self.assertEqual(len(annotation["vertices"]), len(mesh["vertices"]))
        self.assertTrue(annotation["consent"]["biometric_processing"])

    def test_subject_split_leakage_is_detected(self):
        base = {
            "schema_version": 1,
            "subject_id": "subject-1",
            "split": "train",
            "image": {
                "path": "face.png",
                "width": 480,
                "height": 500,
                "sha256": "a" * 64,
            },
            "consent": {"biometric_processing": True},
            "vertices": [
                {
                    "x": 0.5,
                    "y": 0.5,
                    "z": 0.0,
                    "visible": True,
                    "confidence": 1.0,
                }
            ],
            "review": {"status": "reviewed", "annotator_id": "human"},
        }
        second = {**base, "split": "test"}

        audit = audit_annotations([base, second])

        self.assertFalse(audit["ready"])
        self.assertEqual(
            audit["split_leakage"]["subject-1"],
            ["test", "train"],
        )


if __name__ == "__main__":
    unittest.main()
