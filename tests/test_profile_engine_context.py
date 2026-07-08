import tempfile
import unittest
from pathlib import Path

from portrait_core.archive.dataset import create_dataset_archive
from profile_engine.context import ProfileEngineContext


class ProfileEngineContextTestCase(unittest.TestCase):
    def test_context_resolves_dataset_paths_and_records_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_dir, dataset = create_dataset_archive(directory, dataset_id="DS-test")
            context = ProfileEngineContext(dataset_dir, config={"dry_run": True})
            artifact = dataset_dir / "experiments" / "result.json"

            context.add_artifact("result", artifact)
            context.add_warning("careful")
            context.add_error("problem")

            self.assertEqual(context.dataset_id, dataset["id"])
            self.assertEqual(context.paths["dataset_json"], Path(dataset_dir) / "dataset.json")
            self.assertEqual(context.artifacts[0]["path"], "experiments/result.json")
            self.assertEqual(context.warnings, ["careful"])
            self.assertEqual(context.errors, ["problem"])


if __name__ == "__main__":
    unittest.main()
