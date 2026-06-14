"""Подготовка и аудит аннотаций собственного landmark-датасета."""

import hashlib
import json
from pathlib import Path

from portrait_core.mesh import validate_mesh


DATASET_SCHEMA_VERSION = 1
DATASET_SPLITS = {"train", "validation", "test"}


def build_draft_annotation(
    image_path: str,
    mesh: dict,
    *,
    subject_id: str,
    split: str,
    consent_version: str,
    annotator_id: str,
) -> dict:
    """Преобразовать сетку backend в черновую аннотацию для ручной проверки."""
    validate_mesh(mesh)
    if split not in DATASET_SPLITS:
        raise ValueError(f"Неизвестная часть датасета: {split}")
    image_file = Path(image_path)
    if not image_file.is_file():
        raise FileNotFoundError(f"Изображение не найдено: {image_file}")

    width = mesh["image_size"]["width"]
    height = mesh["image_size"]["height"]
    vertices = [
        {
            "x": vertex[0] / width,
            "y": vertex[1] / height,
            "z": vertex[2] / width if len(vertex) == 3 else None,
            "visible": True,
            "confidence": 0.5,
        }
        for vertex in mesh["vertices"]
    ]
    annotation = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "subject_id": subject_id,
        "split": split,
        "image": {
            "path": str(image_file),
            "width": width,
            "height": height,
            "sha256": hashlib.sha256(image_file.read_bytes()).hexdigest(),
        },
        "consent": {
            "biometric_processing": True,
            "version": consent_version,
        },
        "vertices": vertices,
        "review": {
            "status": "draft",
            "annotator_id": annotator_id,
            "notes": "Автоматическая предразметка; требуется ручная проверка.",
        },
        "source": dict(mesh["source"]),
    }
    validate_annotation(annotation)
    return annotation


def validate_annotation(annotation: dict) -> None:
    """Проверить обязательные инварианты аннотации без внешних библиотек."""
    required = {
        "schema_version",
        "subject_id",
        "split",
        "image",
        "consent",
        "vertices",
        "review",
    }
    missing = sorted(required - annotation.keys())
    if missing:
        raise ValueError(f"В аннотации отсутствуют поля: {', '.join(missing)}")
    if annotation["schema_version"] != DATASET_SCHEMA_VERSION:
        raise ValueError("Неподдерживаемая версия аннотации")
    if not isinstance(annotation["subject_id"], str) or not annotation["subject_id"]:
        raise ValueError("Не указан идентификатор человека")
    if annotation["split"] not in DATASET_SPLITS:
        raise ValueError("Некорректная часть датасета")
    if not annotation["consent"].get("biometric_processing"):
        raise ValueError("Нет согласия на обработку биометрических данных")
    image = annotation["image"]
    if image.get("width", 0) < 64 or image.get("height", 0) < 64:
        raise ValueError("Некорректный размер изображения")
    digest = image.get("sha256", "")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("Некорректный SHA-256 изображения")
    if annotation["review"].get("status") not in {"draft", "reviewed", "rejected"}:
        raise ValueError("Некорректный статус проверки")
    if not annotation["vertices"]:
        raise ValueError("Аннотация не содержит вершин")
    for index, vertex in enumerate(annotation["vertices"]):
        if not 0 <= vertex["x"] <= 1 or not 0 <= vertex["y"] <= 1:
            raise ValueError(
                f"Вершина {index} выходит за нормализованные границы"
            )
        if not 0 <= vertex["confidence"] <= 1:
            raise ValueError(f"Некорректная уверенность вершины {index}")
        if not isinstance(vertex["visible"], bool):
            raise ValueError(f"Некорректная видимость вершины {index}")


def audit_annotations(annotations: list[dict]) -> dict:
    """Найти ошибки разметки и утечки людей между частями датасета."""
    errors = []
    subject_splits = {}
    status_counts = {}
    vertex_counts = {}
    for index, annotation in enumerate(annotations):
        try:
            validate_annotation(annotation)
        except (KeyError, TypeError, ValueError) as error:
            errors.append({"index": index, "error": str(error)})
            continue
        subject_splits.setdefault(annotation["subject_id"], set()).add(
            annotation["split"]
        )
        status = annotation["review"]["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        count = len(annotation["vertices"])
        vertex_counts[count] = vertex_counts.get(count, 0) + 1

    leakage = {
        subject: sorted(splits)
        for subject, splits in subject_splits.items()
        if len(splits) > 1
    }
    return {
        "schema_version": 1,
        "annotation_count": len(annotations),
        "valid_count": len(annotations) - len(errors),
        "subject_count": len(subject_splits),
        "review_statuses": status_counts,
        "vertex_counts": vertex_counts,
        "split_leakage": leakage,
        "errors": errors,
        "ready": not errors and not leakage,
    }


def audit_annotation_directory(directory: str) -> dict:
    """Загрузить JSON-аннотации из папки и вернуть результат аудита."""
    source = Path(directory)
    annotations = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(source.glob("*.json"))
    ]
    return audit_annotations(annotations)
