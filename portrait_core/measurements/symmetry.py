"""Оценка симметрии лица."""

from .common import normalized, point_distance


def measure_symmetry(points: dict) -> dict:
    """Оценить симметрию парных зон по разнице их размеров."""
    pairs = {
        "eyes": (
            point_distance(points, "left_eye_outer", "left_eye_inner"),
            point_distance(points, "right_eye_inner", "right_eye_outer"),
        ),
        "brows": (
            point_distance(points, "left_brow_outer", "left_brow_inner"),
            point_distance(points, "right_brow_inner", "right_brow_outer"),
        ),
        "jaw": (
            point_distance(points, "jaw_left", "chin"),
            point_distance(points, "chin", "jaw_right"),
        ),
    }

    zone_scores = {}
    for zone, (left_value, right_value) in pairs.items():
        if left_value is None or right_value is None:
            zone_scores[zone] = None
            continue
        average = (left_value + right_value) / 2
        asymmetry = normalized(abs(left_value - right_value), average)
        zone_scores[zone] = None if asymmetry is None else max(0.0, 1 - asymmetry)

    available_scores = [
        score for score in zone_scores.values() if score is not None
    ]
    overall_score = (
        sum(available_scores) / len(available_scores)
        if available_scores
        else None
    )

    return {
        "zone_scores": zone_scores,
        "overall_score": overall_score,
    }
