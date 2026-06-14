"""Тесты оценки повторяемости признаков."""

import unittest

from portrait_core.stability import (
    analyze_report_stability,
    build_series_profile,
)


def _report(face_ratio, jaw_area):
    return {
        "profile": {
            "dense_features": {
                "face_bbox_ratio": {"value": face_ratio},
                "jaw_hull_area": {
                    "value": jaw_area,
                    "role": "morphology",
                },
                "backend_density": {
                    "value": 100,
                    "topology_invariant": False,
                },
            }
        }
    }


class StabilityTestCase(unittest.TestCase):
    def test_stable_series_is_marked_stable(self):
        result = analyze_report_stability(
            [_report(0.70, 0.40), _report(0.71, 0.405), _report(0.69, 0.395)]
        )

        self.assertEqual(
            result["features"]["face_bbox_ratio"]["status"],
            "stable",
        )
        self.assertEqual(result["sample_count"], 3)
        self.assertNotIn("backend_density", result["features"])
        self.assertEqual(result["roles"]["morphology"]["stable_count"], 2)

    def test_single_report_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_report_stability([_report(0.7, 0.4)])

    def test_series_profile_separates_stable_morphology(self):
        reports = [
            {
                **_report(0.70, 0.40),
                "quality": {"status": "passed"},
                "profile": {
                    **_report(0.70, 0.40)["profile"],
                    "confidence": {"components": {"pose": 0.8}},
                },
            },
            {
                **_report(0.71, 0.405),
                "quality": {"status": "passed"},
                "profile": {
                    **_report(0.71, 0.405)["profile"],
                    "confidence": {"components": {"pose": 0.7}},
                },
            },
        ]

        result = build_series_profile(reports, subject_label="test")

        self.assertEqual(result["selected_group"], "quality_passed")
        self.assertIn("face_bbox_ratio", result["stable_morphology"])


if __name__ == "__main__":
    unittest.main()
