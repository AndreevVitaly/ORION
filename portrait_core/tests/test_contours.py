"""Тесты проектных контуров текущей плотной топологии."""

import unittest
from types import SimpleNamespace

from portrait_core.adapters.mediapipe_adapter import MediaPipeAdapter
from portrait_core.canonical import canonicalize_mesh
from portrait_core.features import extract_dense_features
from portrait_core.zones import assign_vertices_to_zones, build_zone_definitions


class ContourTestCase(unittest.TestCase):
    def _mesh(self):
        landmarks = []
        for index in range(478):
            angle = index / 478 * 6.283185307179586
            landmarks.append(
                SimpleNamespace(
                    x=0.5 + 0.3 * __import__("math").cos(angle),
                    y=0.5 + 0.4 * __import__("math").sin(angle),
                    z=0.0,
                )
            )
        return MediaPipeAdapter.convert_mesh(landmarks, 1000, 1000)

    def test_mediapipe_mesh_contains_project_contours(self):
        mesh = self._mesh()

        self.assertEqual(len(mesh["metadata"]["contours"]["face_oval"]), 36)
        self.assertEqual(len(mesh["metadata"]["contours"]["lips_outer"]), 20)

    def test_lip_features_use_full_contours(self):
        canonical = canonicalize_mesh(self._mesh())
        zones = build_zone_definitions(canonical)
        assignments = assign_vertices_to_zones(canonical, zones)
        result = extract_dense_features(
            canonical,
            assignments,
            canonical["pose"],
        )

        self.assertIsNotNone(result["values"]["lip_outer_height"]["value"])
        self.assertEqual(
            result["values"]["lip_outer_height"]["vertex_count"],
            20,
        )


if __name__ == "__main__":
    unittest.main()
