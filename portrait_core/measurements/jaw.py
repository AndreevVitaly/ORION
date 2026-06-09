"""Измерения нижней челюсти и подбородка."""

from .common import face_references, normalized, point_distance


def measure_jaw(points: dict) -> dict:
    """Измерить ширину челюсти и ее пропорцию к лицу."""
    jaw_width = point_distance(points, "jaw_left", "jaw_right")
    chin_height = point_distance(points, "lower_lip", "chin")
    references = face_references(points)

    return {
        "jaw_width": jaw_width,
        "chin_height": chin_height,
        "jaw_width_ratio": normalized(jaw_width, references["face_width"]),
        "chin_height_ratio": normalized(chin_height, references["face_height"]),
    }
