import unittest

from portrait_core.invariants.ratio_engine import build_invariant_set_from_pfr


class InvariantsRatioEngineTestCase(unittest.TestCase):
    def test_calculates_ratio_from_existing_measurements(self):
        pfr = {
            "id": "PFR-test",
            "dataset_id": "DS-test",
            "measurements": {
                "face": {"face_width": 200.0, "face_height": 300.0},
                "eyes": {"eye_distance": 80.0},
            },
        }

        result = build_invariant_set_from_pfr(pfr)

        self.assertEqual(result.ratios["ipd_face_width"].value, 0.4)
        self.assertEqual(result.ratios["face_height_face_width"].value, 1.5)
        self.assertEqual(result.pfr_id, "PFR-test")
        self.assertEqual(result.dataset_id, "DS-test")

    def test_skips_missing_numerator_without_breaking_process(self):
        pfr = {
            "measurements": {
                "face": {"face_width": 200.0, "face_height": 300.0},
            },
        }

        result = build_invariant_set_from_pfr(pfr)

        self.assertNotIn("ipd_face_width", result.ratios)
        self.assertTrue(any("missing numerator ipd" in item for item in result.warnings))

    def test_skips_zero_denominator(self):
        pfr = {
            "measurements": {
                "face": {"face_width": 0.0, "face_height": 300.0},
                "eyes": {"eye_distance": 80.0},
            },
        }

        result = build_invariant_set_from_pfr(pfr)

        self.assertNotIn("ipd_face_width", result.ratios)
        self.assertTrue(any("zero denominator face_width" in item for item in result.warnings))


if __name__ == "__main__":
    unittest.main()
