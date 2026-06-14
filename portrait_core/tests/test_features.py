"""Тесты зон и плотных геометрических признаков."""

import unittest

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.canonical import canonicalize_mesh
from portrait_core.features import FEATURE_REGISTRY, extract_dense_features
from portrait_core.zones import assign_vertices_to_zones, build_zone_definitions


class DenseFeatureTestCase(unittest.TestCase):
    def setUp(self):
        self.canonical = canonicalize_mesh(
            ManualAdapter().extract_mesh("test-image")
        )
        self.zones = build_zone_definitions(self.canonical)
        self.assignments = assign_vertices_to_zones(
            self.canonical,
            self.zones,
        )

    def test_zones_are_derived_without_backend_indexes(self):
        self.assertIn("face", self.assignments)
        self.assertIn("mouth", self.assignments)
        self.assertGreater(len(self.assignments["face"]), 3)
        self.assertGreater(len(self.assignments["mouth"]), 0)

    def test_registry_features_include_value_and_confidence(self):
        result = extract_dense_features(
            self.canonical,
            self.assignments,
            self.canonical["pose"],
        )

        self.assertEqual(len(result["values"]), len(FEATURE_REGISTRY))
        self.assertIsNotNone(result["values"]["face_hull_area"]["value"])
        self.assertGreaterEqual(
            result["values"]["face_hull_area"]["confidence"],
            0.0,
        )
        self.assertIn(
            "pose",
            result["values"]["face_hull_area"]["confidence_components"],
        )


if __name__ == "__main__":
    unittest.main()
