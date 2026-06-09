"""Измерения носа и его пропорций."""

from .common import face_references, normalized, point_distance


def measure_nose(points: dict) -> dict:
    """Измерить длину и ширину носа."""
    nose_length = point_distance(points, "nose_bridge", "nose_tip")
    nose_width = point_distance(points, "nose_left", "nose_right")
    references = face_references(points)

    return {
        "nose_length": nose_length,
        "nose_width": nose_width,
        "nose_length_ratio": normalized(nose_length, references["face_height"]),
        "nose_width_ratio": normalized(nose_width, references["face_width"]),
        "nose_width_to_length_ratio": normalized(nose_width, nose_length),
    }
