"""Измерения общих пропорций лица."""

from .common import normalized, point_distance
from .geometry import ratio


def calculate_face_measurements(points: dict) -> dict:
    """Посчитать базовые размеры лица по словарю точек."""
    face_width = point_distance(points, "face_left", "face_right")
    face_height = point_distance(points, "face_top", "chin")
    lower_face_height = point_distance(points, "nose_tip", "chin")

    if face_width is None or face_height is None:
        face_width_to_height_ratio = None
    else:
        face_width_to_height_ratio = ratio(face_width, face_height)

    return {
        "face_width": face_width,
        "face_height": face_height,
        "face_width_to_height_ratio": face_width_to_height_ratio,
        "cheek_width": face_width,
        "lower_face_height": lower_face_height,
        "lower_face_height_ratio": normalized(lower_face_height, face_height),
    }


def measure_face(points: dict) -> dict:
    """Совместимое имя для расчета пропорций лица."""
    return calculate_face_measurements(points)
