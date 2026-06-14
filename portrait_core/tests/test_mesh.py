"""Тесты независимого контракта плотной сетки лица."""

import unittest

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.mesh import build_mesh, project_semantic_points, validate_mesh


class MeshContractTestCase(unittest.TestCase):
    def test_manual_mesh_uses_project_schema(self):
        mesh = ManualAdapter().extract_mesh("test-image")

        self.assertEqual(mesh["schema"], "portrait-mesh")
        self.assertEqual(mesh["schema_version"], 1)
        self.assertEqual(mesh["source"]["adapter"], "manual")
        self.assertEqual(mesh["dimensions"], 3)

    def test_semantic_projection_is_independent_from_vertex_order(self):
        original = ManualAdapter().extract_mesh("test-image")
        vertices = list(reversed(original["vertices"]))
        last_index = len(vertices) - 1
        semantic_map = {
            name: last_index - index
            for name, index in original["semantic_map"].items()
        }
        mesh = build_mesh(
            vertices,
            semantic_map,
            source="test-detector",
            source_topology="reversed-test-topology",
            image_width=480,
            image_height=500,
        )

        self.assertEqual(
            project_semantic_points(mesh),
            project_semantic_points(original),
        )

    def test_out_of_range_semantic_index_is_rejected(self):
        mesh = ManualAdapter().extract_mesh("test-image")
        mesh["semantic_map"]["nose_tip"] = len(mesh["vertices"])

        with self.assertRaisesRegex(ValueError, "nose_tip"):
            validate_mesh(mesh)


if __name__ == "__main__":
    unittest.main()
