"""Официальный публичный API Scientific Engine проекта Profile."""

from pathlib import Path
from typing import Any

from portrait_core.adapters.factory import create_mesh_adapter
from portrait_core.pipeline import analyze_photo_with_adapter
from portrait_core.reporting import save_report


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "face_landmarker.task"


def create_portrait_report(
    image_path: str,
    *,
    backend: str = "mediapipe",
    model_path: str | None = None,
    topology_path: str | None = None,
    output_path: str | None = None,
    input_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Создать полный portrait.json для одного изображения.

    Это официальный вход для приложений Profile. Приложения не должны
    самостоятельно вычислять landmarks, mesh, morphology, measurements, LIC
    или report pack: они передают изображение в этот API и получают отчет.
    """
    adapter = create_mesh_adapter(
        backend,
        model_path or str(DEFAULT_MODEL_PATH),
        topology_path,
    )
    _, report = analyze_photo_with_adapter(image_path, adapter, input_metadata=input_metadata)
    if output_path:
        save_report(report, output_path)
    return report


def analyze(image_path: str, **kwargs) -> dict[str, Any]:
    """Официальный короткий алиас для анализа изображения."""
    return create_portrait_report(image_path, **kwargs)


def process_face(image_path: str, **kwargs) -> dict[str, Any]:
    """Совместимый алиас для приложений, работающих с кадрами лица."""
    return create_portrait_report(image_path, **kwargs)
