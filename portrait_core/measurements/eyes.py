"""Измерения глаз и межглазного расстояния."""

from .geometry import distance


def _get_distance(points: dict, first_key: str, second_key: str):
    """Вернуть расстояние между точками или None, если точки отсутствуют."""
    if first_key not in points or second_key not in points:
        return None
    return distance(points[first_key], points[second_key])


def calculate_eye_measurements(points: dict) -> dict:
    """Посчитать базовые размеры глаз по словарю точек."""
    left_eye_width = _get_distance(points, "left_eye_outer", "left_eye_inner")
    right_eye_width = _get_distance(points, "right_eye_inner", "right_eye_outer")
    eye_distance = _get_distance(points, "left_eye_inner", "right_eye_inner")
    eyes_total_width = _get_distance(points, "left_eye_outer", "right_eye_outer")

    if left_eye_width is None or right_eye_width is None:
        average_eye_width = None
        eye_width_asymmetry = None
    else:
        average_eye_width = (left_eye_width + right_eye_width) / 2
        eye_width_asymmetry = abs(left_eye_width - right_eye_width)

    return {
        "left_eye_width": left_eye_width,
        "right_eye_width": right_eye_width,
        "eye_distance": eye_distance,
        "average_eye_width": average_eye_width,
        "eye_width_asymmetry": eye_width_asymmetry,
        "eyes_total_width": eyes_total_width,
    }


def measure_eyes(points: dict) -> dict:
    """Совместимое имя для расчета зоны глаз."""
    return calculate_eye_measurements(points)
