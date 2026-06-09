"""Измерения рта и губ."""

from .common import face_references, normalized, point_distance


def measure_mouth(points: dict) -> dict:
    """Измерить ширину рта и видимую высоту губ."""
    mouth_width = point_distance(points, "mouth_left", "mouth_right")
    lip_height = point_distance(points, "upper_lip", "lower_lip")
    face_width = face_references(points)["face_width"]

    return {
        "mouth_width": mouth_width,
        "lip_height": lip_height,
        "mouth_width_ratio": normalized(mouth_width, face_width),
        "lip_height_to_mouth_width_ratio": normalized(lip_height, mouth_width),
    }
