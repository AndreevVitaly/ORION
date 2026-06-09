"""Измерения глаз и межглазного расстояния."""

from .common import face_references, normalized, point_distance


def calculate_eye_measurements(points: dict) -> dict:
    """Посчитать базовые размеры глаз по словарю точек."""
    left_eye_width = point_distance(points, "left_eye_outer", "left_eye_inner")
    right_eye_width = point_distance(points, "right_eye_inner", "right_eye_outer")
    eye_distance = point_distance(points, "left_eye_inner", "right_eye_inner")
    eyes_total_width = point_distance(points, "left_eye_outer", "right_eye_outer")
    face_width = face_references(points)["face_width"]

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
        "eye_distance_ratio": normalized(eye_distance, face_width),
        "average_eye_width_ratio": normalized(average_eye_width, face_width),
        "eye_width_asymmetry_ratio": normalized(
            eye_width_asymmetry, average_eye_width
        ),
    }


def measure_eyes(points: dict) -> dict:
    """Совместимое имя для расчета зоны глаз."""
    return calculate_eye_measurements(points)
