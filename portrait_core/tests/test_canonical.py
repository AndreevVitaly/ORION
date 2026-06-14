"""Тесты канонизации сетки лица."""

import unittest

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.canonical import canonicalize_mesh, estimate_pose
from portrait_core.mesh import build_mesh


class CanonicalizationTestCase(unittest.TestCase):
    def test_manual_pose_is_nearly_frontal(self):
        pose = estimate_pose(ManualAdapter().extract_mesh("test-image"))

        self.assertAlmostEqual(pose["roll_degrees"], 0.0)
        self.assertAlmostEqual(pose["yaw_proxy"], 0.0)
        self.assertAlmostEqual(pose["pitch_proxy"], 0.0, places=2)
        self.assertFalse(pose["metric_3d"])

    def test_translation_and_scale_do_not_change_canonical_vertices(self):
        original = ManualAdapter().extract_mesh("test-image")
        transformed = build_mesh(
            [
                [
                    vertex[0] * 2 + 100,
                    vertex[1] * 2 - 50,
                    vertex[2] * 2,
                ]
                for vertex in original["vertices"]
            ],
            original["semantic_map"],
            source="test",
            source_topology="scaled",
            image_width=1060,
            image_height=950,
        )

        canonical_original = canonicalize_mesh(original)["vertices"]
        canonical_transformed = canonicalize_mesh(transformed)["vertices"]

        for first, second in zip(canonical_original, canonical_transformed):
            for first_value, second_value in zip(first, second):
                self.assertAlmostEqual(first_value, second_value)


if __name__ == "__main__":
    unittest.main()
