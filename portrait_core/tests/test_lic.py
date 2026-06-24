"""Тесты экспериментального LIC Core."""

import json
import tempfile
import unittest
from pathlib import Path

from portrait_core.lic import calculate_lic_core, distance, safe_distance
from portrait_core.lic_experiment import analyze_lic_stability


class LICTestCase(unittest.TestCase):
    def setUp(self):
        self.points = {
            "face_left": [100.0, 200.0],
            "face_right": [340.0, 200.0],
            "face_top": [220.0, 80.0],
            "chin": [220.0, 420.0],
            "left_eye_outer": [140.0, 190.0],
            "left_eye_inner": [190.0, 190.0],
            "right_eye_inner": [250.0, 190.0],
            "right_eye_outer": [300.0, 190.0],
            "nose_tip": [220.0, 270.0],
            "mouth_left": [180.0, 330.0],
            "mouth_right": [260.0, 330.0],
        }

    def test_distance_between_two_points(self):
        self.assertEqual(distance([0, 0], [3, 4]), 5.0)

    def test_safe_distance_does_not_fail_when_points_are_missing(self):
        result = safe_distance({}, "left_pupil", "right_pupil")

        self.assertFalse(result.available)
        self.assertIsNone(result.value)
        self.assertEqual(result.points, ["left_pupil", "right_pupil"])

    def test_lic_core_calculates_ratios(self):
        lic_core = calculate_lic_core(self.points).to_dict()

        self.assertEqual(lic_core["version"], "lic-core/0.1")
        self.assertEqual(lic_core["recommended_base"], "ipd")
        self.assertAlmostEqual(
            lic_core["base_candidates"]["ipd"]["value"],
            110.0,
        )
        self.assertAlmostEqual(
            lic_core["ratios"]["inner_eye_distance/ipd"],
            60.0 / 110.0,
        )
        self.assertTrue(lic_core["base_candidates"]["nose_to_mouth"]["available"])

    def test_lic_core_reports_missing_points_as_limitations(self):
        points = dict(self.points)
        del points["face_left"]

        lic_core = calculate_lic_core(points)

        self.assertFalse(lic_core.base_candidates["face_width"].available)
        self.assertTrue(
            any("face_width" in limitation for limitation in lic_core.limitations)
        )

    def test_lic_experiment_selects_lowest_cv_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            reports = [
                {"lic_core": {"base_candidates": {
                    "ipd": {"value": 100.0, "available": True},
                    "face_width": {"value": 200.0, "available": True},
                }}},
                {"lic_core": {"base_candidates": {
                    "ipd": {"value": 101.0, "available": True},
                    "face_width": {"value": 240.0, "available": True},
                }}},
                {"lic_core": {"base_candidates": {
                    "ipd": {"value": 99.0, "available": True},
                    "face_width": {"value": 160.0, "available": True},
                }}},
            ]
            for index, report in enumerate(reports):
                path = Path(directory) / f"report_{index}_portrait.json"
                path.write_text(
                    json.dumps(report, ensure_ascii=False),
                    encoding="utf-8",
                )

            result = analyze_lic_stability(directory)

        self.assertEqual(result["best_candidate"], "ipd")
        self.assertEqual(result["ranking"][0]["name"], "ipd")
        self.assertLess(
            result["ranking"][0]["coefficient_of_variation"],
            result["ranking"][1]["coefficient_of_variation"],
        )


if __name__ == "__main__":
    unittest.main()
