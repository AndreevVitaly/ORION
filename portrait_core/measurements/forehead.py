"""Измерения лба и верхней трети лица."""

from .common import face_references, normalized, point_distance
from .geometry import midpoint


def measure_forehead(points: dict) -> dict:
    """Измерить высоту и ширину видимой зоны лба."""
    required = (
        "left_brow_outer",
        "left_brow_inner",
        "right_brow_inner",
        "right_brow_outer",
    )
    if not all(name in points for name in required):
        brow_center = None
    else:
        left_center = midpoint(
            points["left_brow_outer"], points["left_brow_inner"]
        )
        right_center = midpoint(
            points["right_brow_inner"], points["right_brow_outer"]
        )
        brow_center = midpoint(left_center, right_center)

    forehead_height = (
        None
        if brow_center is None or "face_top" not in points
        else point_distance(
            {"top": points["face_top"], "brow": brow_center}, "top", "brow"
        )
    )
    forehead_width = point_distance(
        points, "left_brow_outer", "right_brow_outer"
    )
    references = face_references(points)
    return {
        "forehead_height": forehead_height,
        "forehead_width": forehead_width,
        "forehead_height_ratio": normalized(
            forehead_height, references["face_height"]
        ),
        "forehead_width_ratio": normalized(
            forehead_width, references["face_width"]
        ),
    }
