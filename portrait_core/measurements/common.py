"""Общие помощники для измерений по именованным точкам лица."""

from .geometry import distance, ratio


def point_distance(points: dict, first_key: str, second_key: str):
    """Вернуть расстояние между двумя точками или None."""
    if first_key not in points or second_key not in points:
        return None
    return distance(points[first_key], points[second_key])


def normalized(value, reference):
    """Нормализовать значение относительно опорного размера."""
    if value is None or reference in (None, 0):
        return None
    return ratio(value, reference)


def face_references(points: dict) -> dict:
    """Вернуть основные размеры, используемые для нормализации."""
    return {
        "face_width": point_distance(points, "face_left", "face_right"),
        "face_height": point_distance(points, "face_top", "chin"),
    }
