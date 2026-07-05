"""Тесты компактной упаковки серии portrait JSON."""

import json
import tempfile
import unittest
from pathlib import Path

from portrait_core.report_pack import build_report_pack, render_markdown


class ReportPackTestCase(unittest.TestCase):
    def test_report_pack_builds_compact_dataset_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            reports = [
                {
                    "image": "frame001.jpg",
                    "points": {
                        "left_eye_inner": [100.0, 100.0],
                        "right_eye_inner": [200.0, 100.0],
                        "nose_tip": [150.0, 170.0],
                    },
                    "mesh": {"vertices": [[1, 2, 3]]},
                    "morphology": {
                        "face_proportion": "среднее",
                        "symmetry": "высокая симметрия",
                    },
                    "measurements": {
                        "face": {"face_width_to_height_ratio": 0.7},
                        "symmetry": {"overall_score": 0.95},
                    },
                    "lic_core": {
                        "recommended_base": "ipd",
                        "base_candidates": {
                            "ipd": {"value": 100.0, "available": True},
                            "face_width": {"value": 220.0, "available": True},
                        },
                        "limitations": [],
                    },
                },
                {
                    "image": "frame002.jpg",
                    "points": {
                        "left_eye_inner": [101.0, 100.0],
                        "right_eye_inner": [201.0, 100.0],
                        "nose_tip": [151.0, 171.0],
                    },
                    "mesh": {"vertices": [[4, 5, 6]]},
                    "morphology": {
                        "face_proportion": "среднее",
                        "symmetry": "умеренная симметрия",
                    },
                    "measurements": {
                        "face": {"face_width_to_height_ratio": 0.72},
                        "symmetry": {"overall_score": 0.9},
                    },
                    "lic_core": {
                        "recommended_base": "ipd",
                        "base_candidates": {
                            "ipd": {"value": 101.0, "available": True},
                            "face_width": {"value": 260.0, "available": True},
                        },
                        "limitations": ["test limitation"],
                    },
                },
            ]
            for index, report in enumerate(reports, start=1):
                (source / f"frame00{index}_portrait.json").write_text(
                    json.dumps(report, ensure_ascii=False),
                    encoding="utf-8",
                )
            summary = [
                {
                    "image": "frame001.jpg",
                    "status": "passed",
                    "issues": "",
                    "report": "frame001_portrait.json",
                },
                {
                    "image": "frame002.jpg",
                    "status": "warning",
                    "issues": "лицо заметно повернуто; фотография размыта",
                    "report": "frame002_portrait.json",
                },
            ]
            (source / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False),
                encoding="utf-8",
            )

            pack = build_report_pack(directory)
            markdown = render_markdown(pack)

        self.assertEqual(pack["schema"], "portrait-report-pack/1")
        self.assertEqual(pack["reports_count"], 2)
        self.assertEqual(pack["quality"]["statuses"], {"passed": 1, "warning": 1})
        self.assertEqual(pack["lic_stability"]["best_candidate"], "ipd")
        self.assertIn("left_eye_inner", [row["name"] for row in pack["point_stability"]["top_10"]])
        self.assertEqual(pack["morphology"]["face_proportion"], {"среднее": 2})
        self.assertIn("face_width_to_height_ratio", pack["measurements"])
        self.assertIn("frames", pack)
        self.assertNotIn("mesh", pack["frames"][0])
        self.assertNotIn("points", pack["frames"][0])
        self.assertIn("Лучший кандидат", markdown)


if __name__ == "__main__":
    unittest.main()
