"""Адаптер собственной ONNX-модели плотной сетки лица."""

import json
from pathlib import Path

from portrait_core.mesh import build_mesh

from .base import FacePointAdapter


class OnnxModelContractError(RuntimeError):
    """ONNX-модель или ее sidecar не соответствуют контракту проекта."""


class OnnxMeshAdapter(FacePointAdapter):
    """Запустить ONNX-модель с выходом [1, vertex_count, 3]."""

    def __init__(
        self,
        model_path: str,
        topology_path: str | None = None,
        *,
        session=None,
    ):
        self.model_path = Path(model_path)
        self.topology_path = Path(
            topology_path or f"{self.model_path}.json"
        )
        self.specification = self._load_specification()
        self.session = session

    def _load_specification(self) -> dict:
        if not self.topology_path.is_file():
            raise FileNotFoundError(
                f"Не найдена спецификация ONNX-модели: {self.topology_path}"
            )
        specification = json.loads(
            self.topology_path.read_text(encoding="utf-8")
        )
        required = {
            "model_id",
            "input_name",
            "input_size",
            "vertex_count",
            "semantic_map",
        }
        missing = sorted(required - specification.keys())
        if missing:
            raise OnnxModelContractError(
                f"В спецификации отсутствуют поля: {', '.join(missing)}"
            )
        if specification.get("output_coordinates") != "normalized-image":
            raise OnnxModelContractError(
                "Поддерживаются координаты normalized-image"
            )
        return specification

    def _get_session(self):
        if self.session is not None:
            return self.session
        if not self.model_path.is_file():
            raise FileNotFoundError(f"ONNX-модель не найдена: {self.model_path}")
        try:
            import onnxruntime as ort
        except ImportError as error:
            raise OnnxModelContractError(
                "Для собственной модели установите onnxruntime"
            ) from error
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )
        return self.session

    def _prepare_input(self, image):
        import numpy as np

        width, height = self.specification["input_size"]
        resized = image.resize((width, height))
        array = np.asarray(resized, dtype=np.float32) / 255.0
        return np.transpose(array, (2, 0, 1))[None, ...]

    def extract_mesh(self, image_path: str) -> dict:
        image_file = Path(image_path)
        if not image_file.is_file():
            raise FileNotFoundError(f"Фотография не найдена: {image_file}")

        import numpy as np
        from PIL import Image, ImageOps

        with Image.open(image_file) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        session = self._get_session()
        outputs = session.run(
            None,
            {
                self.specification["input_name"]: self._prepare_input(image)
            },
        )
        if not outputs:
            raise OnnxModelContractError("ONNX-модель не вернула результат")
        raw_vertices = np.asarray(outputs[0], dtype=float)
        if raw_vertices.ndim == 3 and raw_vertices.shape[0] == 1:
            raw_vertices = raw_vertices[0]
        expected_shape = (self.specification["vertex_count"], 3)
        if raw_vertices.shape != expected_shape:
            raise OnnxModelContractError(
                f"Ожидается выход {expected_shape}, получен {raw_vertices.shape}"
            )

        vertices = [
            [
                float(vertex[0] * image.width),
                float(vertex[1] * image.height),
                float(vertex[2] * image.width),
            ]
            for vertex in raw_vertices
        ]
        return build_mesh(
            vertices,
            self.specification["semantic_map"],
            source=self.specification["model_id"],
            source_topology=self.specification.get(
                "topology_id",
                f'portrait-{len(vertices)}',
            ),
            image_width=image.width,
            image_height=image.height,
            metadata={
                "runtime": "onnx",
                "model_version": self.specification.get("model_version"),
                "contours": self.specification.get("contours"),
            },
        )
