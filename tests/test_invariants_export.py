import json
import tempfile
import unittest
from pathlib import Path

from portrait_core.invariants import build_invariants_for_portrait


class InvariantsExportTestCase(unittest.TestCase):
    def test_exports_json_from_minimal_portrait(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pfr_path = root / "portrait.json"
            output_path = root / "invariants.json"
            pfr_path.write_text(
                json.dumps(
                    {
                        "id": "PFR-one",
                        "dataset_id": "DS-one",
                        "measurements": {
                            "face": {"face_width": 200.0, "face_height": 300.0},
                            "eyes": {"eye_distance": 80.0},
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            payload = build_invariants_for_portrait(pfr_path, output_path)
            stored = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema"], "profile.invariants.v1")
        self.assertEqual(stored["pfr_id"], "PFR-one")
        self.assertEqual(stored["ratios"]["ipd_face_width"]["value"], 0.4)
        self.assertEqual(stored["source"]["portrait_json"], "portrait.json")


if __name__ == "__main__":
    unittest.main()
