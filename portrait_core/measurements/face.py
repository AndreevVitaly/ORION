"""Измерения общих пропорций лица."""

from .geometry import distance, ratio


def _get_distance(points: dict, first_key: str, second_key: str):
    """Вернуть расстояние между точками или None, если точки отсутствуют."""
    if first_key not in points or second_key not in points:
        return None
    return distance(points[first_key], points[second_key])


def calculate_face_measurements(points: dict) -> dict:
    """Посчитать базовые размеры лица по словарю точек."""
    face_width = _get_distance(points, "face_left", "face_right")
    face_height = _get_distance(points, "face_top", "chin")
    lower_face_height = _get_distance(points, "nose_tip", "chin")

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
    }


def measure_face(points: dict) -> dict:
    """Совместимое имя для расчета пропорций лица."""
    return calculate_face_measurements(points)
