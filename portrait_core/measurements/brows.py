"""Измерения бровей и их положения."""

from .common import face_references, normalized, point_distance


def measure_brows(points: dict) -> dict:
    """Измерить ширину бровей, расстояние между ними и асимметрию."""
    left_brow_width = point_distance(
        points, "left_brow_outer", "left_brow_inner"
    )
    right_brow_width = point_distance(
        points, "right_brow_inner", "right_brow_outer"
    )
    brow_distance = point_distance(
        points, "left_brow_inner", "right_brow_inner"
    )

    if left_brow_width is None or right_brow_width is None:
        average_brow_width = None
        brow_width_asymmetry = None
    else:
        average_brow_width = (left_brow_width + right_brow_width) / 2
        brow_width_asymmetry = abs(left_brow_width - right_brow_width)

    face_width = face_references(points)["face_width"]
    return {
        "left_brow_width": left_brow_width,
        "right_brow_width": right_brow_width,
        "brow_distance": brow_distance,
        "average_brow_width": average_brow_width,
        "brow_width_asymmetry": brow_width_asymmetry,
        "brow_distance_ratio": normalized(brow_distance, face_width),
        "brow_width_asymmetry_ratio": normalized(
            brow_width_asymmetry, average_brow_width
        ),
    }
