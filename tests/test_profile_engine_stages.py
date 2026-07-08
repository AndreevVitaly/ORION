import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from portrait_core.archive.dataset import create_dataset_archive, write_dataset_files
from profile_engine.context import ProfileEngineContext
from profile_engine.stages import EnsurePFRStage


class ProfileEngineStagesTestCase(unittest.TestCase):
    @patch("portrait_core.create_portrait_report")
    def test_ensure_pfr_creates_missing_report(self, report_mock):
        with tempfile.TemporaryDirectory() as directory:
            dataset_dir, dataset = create_dataset_archive(directory, dataset_id="DS-test")
            image_path = dataset_dir / "images" / "one.jpg"
            image_path.write_bytes(b"fake")
            dataset["items"].append(
                {
                    "image_path": "images/one.jpg",
                    "pfr_path": None,
                    "status": "pending",
                    "issues": [],
                }
            )
            write_dataset_files(dataset_dir, dataset)
            report_mock.return_value = {
                "id": "PFR-new",
                "uuid": "uuid-new",
                "quality": {"status": "passed", "issues": []},
            }
            context = ProfileEngineContext(dataset_dir)

            result = EnsurePFRStage().run(context)
            stored = (Path(dataset_dir) / "pfr" / "one_portrait.json").read_text(encoding="utf-8")

            self.assertEqual(result["stats"]["created"], 1)
            self.assertIn("PFR-new", stored)
            report_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
