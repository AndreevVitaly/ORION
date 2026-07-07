"""Tests for the Profile research archive model."""

import json
import tempfile
import unittest
from pathlib import Path

from portrait_core.archive.dataset import create_dataset_archive, write_dataset_files
from portrait_core.archive.experiment import create_experiment_record
from portrait_core.archive.validation import validate_dataset_archive
from portrait_core.archive.common import new_uuid
from portrait_core.report_pack import build_report_pack


class ResearchArchiveTestCase(unittest.TestCase):
    def test_dataset_json_contains_identity_and_items(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_dir, dataset = create_dataset_archive(directory, source="photos")
            pfr_uuid = new_uuid()
            pfr_path = dataset_dir / "pfr" / "one_portrait.json"
            pfr_path.write_text(json.dumps({"id": "PFR-one", "uuid": pfr_uuid}, ensure_ascii=False), encoding="utf-8")
            dataset["items"].append(
                {
                    "pfr_id": "PFR-one",
                    "pfr_uuid": pfr_uuid,
                    "image_path": "images/one.jpg",
                    "pfr_path": "pfr/one_portrait.json",
                    "status": "passed",
                    "issues": [],
                    "source_frame": "one.jpg",
                    "frame_index": None,
                    "timestamp_seconds": None,
                }
            )
            write_dataset_files(dataset_dir, dataset)

            stored = json.loads((dataset_dir / "dataset.json").read_text(encoding="utf-8"))

        self.assertTrue(stored["id"].startswith("DS-"))
        self.assertIn("uuid", stored)
        self.assertEqual(stored["items"][0]["pfr_id"], "PFR-one")
        self.assertEqual(stored["summary"]["created_pfr"], 1)

    def test_experiment_json_contains_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment_dir, experiment = create_experiment_record(
                directory,
                datasets=["DS-test"],
                method="lic_stability",
            )

            stored = json.loads((experiment_dir / "experiment.json").read_text(encoding="utf-8"))

        self.assertTrue(experiment["id"].startswith("EXP-"))
        self.assertEqual(stored["datasets"], ["DS-test"])
        self.assertEqual(stored["method"], "lic_stability")
        self.assertIn("uuid", stored)

    def test_validate_dataset_finds_missing_pfr(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_dir, dataset = create_dataset_archive(directory)
            dataset["items"].append(
                {
                    "pfr_id": "PFR-missing",
                    "pfr_uuid": new_uuid(),
                    "image_path": "images/missing.jpg",
                    "pfr_path": "pfr/missing_portrait.json",
                    "status": "passed",
                    "issues": [],
                    "source_frame": "missing.jpg",
                    "frame_index": None,
                    "timestamp_seconds": None,
                }
            )
            write_dataset_files(dataset_dir, dataset)

            result = validate_dataset_archive(dataset_dir)

        self.assertFalse(result["valid"])
        self.assertTrue(any("does not exist" in error for error in result["errors"]))

    def test_validate_dataset_accepts_correct_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_dir, dataset = create_dataset_archive(directory)
            pfr_uuid = new_uuid()
            (dataset_dir / "pfr" / "ok_portrait.json").write_text(
                json.dumps({"id": "PFR-ok", "uuid": pfr_uuid}, ensure_ascii=False),
                encoding="utf-8",
            )
            dataset["items"].append(
                {
                    "pfr_id": "PFR-ok",
                    "pfr_uuid": pfr_uuid,
                    "image_path": "images/ok.jpg",
                    "pfr_path": "pfr/ok_portrait.json",
                    "status": "passed",
                    "issues": [],
                    "source_frame": "ok.jpg",
                    "frame_index": None,
                    "timestamp_seconds": None,
                }
            )
            write_dataset_files(dataset_dir, dataset)

            result = validate_dataset_archive(dataset_dir)

        self.assertTrue(result["valid"])
        self.assertEqual(result["items_checked"], 1)

    def test_report_pack_preserves_dataset_experiment_and_pfr_links(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_dir, dataset = create_dataset_archive(directory, dataset_id="DS-test")
            pfr_uuid = new_uuid()
            report = {
                "id": "PFR-one",
                "uuid": pfr_uuid,
                "image": "one.jpg",
                "points": {
                    "left_eye_inner": [100.0, 100.0],
                    "right_eye_inner": [200.0, 100.0],
                    "nose_tip": [150.0, 170.0],
                },
                "lic_core": {
                    "recommended_base": "ipd",
                    "base_candidates": {"ipd": {"value": 100.0, "available": True}},
                    "limitations": [],
                },
                "morphology": {},
                "measurements": {},
            }
            (dataset_dir / "pfr" / "one_portrait.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            dataset["items"].append(
                {
                    "pfr_id": "PFR-one",
                    "pfr_uuid": pfr_uuid,
                    "image_path": "images/one.jpg",
                    "pfr_path": "pfr/one_portrait.json",
                    "status": "passed",
                    "issues": [],
                    "source_frame": "one.jpg",
                    "frame_index": None,
                    "timestamp_seconds": None,
                }
            )
            write_dataset_files(dataset_dir, dataset)

            pack = build_report_pack(str(dataset_dir), experiment_id="EXP-test")

        self.assertEqual(pack["dataset_id"], "DS-test")
        self.assertEqual(pack["experiment_id"], "EXP-test")
        self.assertEqual(pack["pfr_records"][0]["pfr_id"], "PFR-one")


if __name__ == "__main__":
    unittest.main()
