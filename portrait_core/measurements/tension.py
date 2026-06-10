"""Оценка визуального напряжения черт лица."""

from .common import normalized, point_distance


def measure_tension(points: dict) -> dict:
    """Вернуть геометрический индикатор положения губ и бровей."""
    mouth_width = point_distance(points, "mouth_left", "mouth_right")
    lip_gap = point_distance(points, "upper_lip", "lower_lip")
    left_brow = point_distance(points, "left_brow_outer", "left_brow_inner")
    right_brow = point_distance(points, "right_brow_inner", "right_brow_outer")

    mouth_opening_ratio = normalized(lip_gap, mouth_width)
    if left_brow is None or right_brow is None:
        brow_asymmetry_ratio = None
    else:
        brow_asymmetry_ratio = normalized(
            abs(left_brow - right_brow), (left_brow + right_brow) / 2
        )

    components = [
        value
        for value in (mouth_opening_ratio, brow_asymmetry_ratio)
        if value is not None
    ]
    geometric_index = sum(components) / len(components) if components else None
    return {
        "mouth_opening_ratio": mouth_opening_ratio,
        "brow_asymmetry_ratio": brow_asymmetry_ratio,
        "geometric_tension_index": geometric_index,
        "interpretation": "геометрический индикатор, не оценка эмоций",
    }
