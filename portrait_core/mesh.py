"""Версионируемый контракт плотной сетки лица.

Сетка принадлежит проекту и не зависит от конкретного детектора. Адаптеры
обязаны преобразовывать собственный результат в этот формат.
"""

from copy import deepcopy

from portrait_core.landmarks import validate_landmarks
from portrait_core.topologies import validate_contours


MESH_SCHEMA = "portrait-mesh"
MESH_SCHEMA_VERSION = 1
COORDINATE_SYSTEM = "image-pixels"


def build_mesh(
    vertices,
    semantic_map: dict,
    *,
    source: str,
    source_topology: str,
    image_width: int,
    image_height: int,
    dimensions: int = 3,
    metadata: dict | None = None,
) -> dict:
    """Собрать и проверить сетку в формате Portrait Mesh Schema v1."""
    mesh = {
        "schema": MESH_SCHEMA,
        "schema_version": MESH_SCHEMA_VERSION,
        "coordinate_system": COORDINATE_SYSTEM,
        "dimensions": dimensions,
        "image_size": {
            "width": image_width,
            "height": image_height,
        },
        "source": {
            "adapter": source,
            "topology": source_topology,
        },
        "vertices": [list(vertex) for vertex in vertices],
        "semantic_map": dict(semantic_map),
        "metadata": dict(metadata or {}),
    }
    validate_mesh(mesh)
    return mesh


def validate_mesh(mesh: dict) -> None:
    """Проверить структуру, координаты и семантическую карту сетки."""
    if not isinstance(mesh, dict):
        raise TypeError("Сетка лица должна быть передана словарем")
    if mesh.get("schema") != MESH_SCHEMA:
        raise ValueError(f"Ожидается схема {MESH_SCHEMA}")
    if mesh.get("schema_version") != MESH_SCHEMA_VERSION:
        raise ValueError(
            f"Неподдерживаемая версия схемы: {mesh.get('schema_version')}"
        )
    if mesh.get("coordinate_system") != COORDINATE_SYSTEM:
        raise ValueError(
            f"Неподдерживаемая система координат: {mesh.get('coordinate_system')}"
        )

    dimensions = mesh.get("dimensions")
    if dimensions not in (2, 3):
        raise ValueError("Сетка должна содержать двух- или трехмерные координаты")

    image_size = mesh.get("image_size")
    if not isinstance(image_size, dict):
        raise ValueError("Не указан размер исходного изображения")
    if image_size.get("width", 0) <= 0 or image_size.get("height", 0) <= 0:
        raise ValueError("Размер исходного изображения должен быть положительным")

    vertices = mesh.get("vertices")
    if not isinstance(vertices, list) or not vertices:
        raise ValueError("Сетка не содержит вершин")
    for index, vertex in enumerate(vertices):
        if not isinstance(vertex, (list, tuple)) or len(vertex) != dimensions:
            raise ValueError(
                f"Вершина {index} должна содержать {dimensions} координаты"
            )
        if not all(isinstance(value, (int, float)) for value in vertex):
            raise TypeError(f"Координаты вершины {index} должны быть числами")

    semantic_map = mesh.get("semantic_map")
    if not isinstance(semantic_map, dict):
        raise ValueError("Сетка не содержит семантической карты")
    for name, index in semantic_map.items():
        if not isinstance(name, str) or not isinstance(index, int):
            raise TypeError("Семантическая карта должна иметь формат имя -> индекс")
        if index < 0 or index >= len(vertices):
            raise ValueError(f"Индекс точки {name} выходит за границы сетки")

    source = mesh.get("source")
    if not isinstance(source, dict):
        raise ValueError("Не указан источник сетки")
    if not source.get("adapter") or not source.get("topology"):
        raise ValueError("Источник должен содержать адаптер и топологию")

    contours = mesh.get("metadata", {}).get("contours")
    if contours is not None:
        validate_contours(contours, len(vertices))


def project_semantic_points(mesh: dict) -> dict:
    """Получить именованные 2D-точки для измерительного ядра."""
    validate_mesh(mesh)
    vertices = mesh["vertices"]
    points = {
        name: [float(vertices[index][0]), float(vertices[index][1])]
        for name, index in mesh["semantic_map"].items()
    }
    validate_landmarks(points)
    return points


def copy_mesh(mesh: dict) -> dict:
    """Вернуть независимую проверенную копию сетки."""
    validate_mesh(mesh)
    return deepcopy(mesh)
