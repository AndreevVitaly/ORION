"""Тесты контракта собственной ONNX-модели."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from portrait_core.adapters.manual_adapter import ManualAdapter
from portrait_core.adapters.onnx_adapter import OnnxMeshAdapter


class FakeSession:
    def __init__(self, output):
        self.output = output
        self.inputs = None

    def run(self, output_names, inputs):
        self.inputs = inputs
        return [self.output]


class OnnxAdapterTestCase(unittest.TestCase):
    def test_adapter_converts_normalized_output_to_project_mesh(self):
        manual_mesh = ManualAdapter().extract_mesh("test-image")
        vertex_count = len(manual_mesh["vertices"])
        output = np.zeros((1, vertex_count, 3), dtype=np.float32)
        output[0, :, 0] = 0.25
        output[0, :, 1] = 0.50
        session = FakeSession(output)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "face.png"
            model_path = root / "portrait.onnx"
            spec_path = root / "portrait.onnx.json"
            Image.new("RGB", (400, 200), "white").save(image_path)
            spec_path.write_text(
                json.dumps(
                    {
                        "model_id": "portrait-test-model",
                        "input_name": "image",
                        "input_size": [64, 64],
                        "vertex_count": vertex_count,
                        "output_coordinates": "normalized-image",
                        "semantic_map": manual_mesh["semantic_map"],
                    }
                ),
                encoding="utf-8",
            )

            mesh = OnnxMeshAdapter(
                model_path,
                session=session,
            ).extract_mesh(image_path)

        self.assertEqual(mesh["source"]["adapter"], "portrait-test-model")
        self.assertEqual(mesh["vertices"][0], [100.0, 100.0, 0.0])
        self.assertEqual(
            session.inputs["image"].shape,
            (1, 3, 64, 64),
        )


if __name__ == "__main__":
    unittest.main()
