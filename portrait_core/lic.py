"""LIC Core: экспериментальный Лицевой Инвариантный Каркас.

LIC не является психологической интерпретацией или оценкой личности. Это
геометрический исследовательский слой для проверки устойчивости опорных
расстояний и отношений лица.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Optional


LIC_CORE_VERSION = "lic-core/0.1"


@dataclass(frozen=True)
class LICDistance:
    """Одно кандидатное расстояние LIC."""

    value: Optional[float]
    available: bool
    points: list[str]


@dataclass(frozen=True)
class LICCore:
    """Набор базовых LIC-расстояний и отношений."""

    version: str
    base_candidates: dict[str, LICDistance]
    ratios: dict[str, float]
    recommended_base: Optional[str]
    limitations: list[str]

    def to_dict(self) -> dict:
        """Вернуть JSON-сериализуемое представление."""
        return asdict(self)


def distance(p1, p2) -> float:
    """Евклидово расстояние между двумя 2D-точками."""
    return math.dist((float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1])))


def safe_distance(points: dict, name_a: str, name_b: str) -> LICDistance:
    """Посчитать расстояние без падения при отсутствии точек."""
    used_points = [name_a, name_b]
    if name_a not in points or name_b not in points:
        return LICDistance(None, False, used_points)
    return LICDistance(distance(points[name_a], points[name_b]), True, used_points)


def _midpoint(point_a, point_b) -> list[float]:
    return [
        (float(point_a[0]) + float(point_b[0])) / 2,
        (float(point_a[1]) + float(point_b[1])) / 2,
    ]


def _point_between(points: dict, name_a: str, name_b: str):
    if name_a not in points or name_b not in points:
        return None
    return _midpoint(points[name_a], points[name_b])


def _distance_from_points(value, used_points: list[str]) -> LICDistance:
    if value is None:
        return LICDistance(None, False, used_points)
    point_a, point_b = value
    return LICDistance(distance(point_a, point_b), True, used_points)


def _mouth_center(points: dict):
    return _point_between(points, "mouth_left", "mouth_right")


def _eye_midpoint(points: dict):
    left_eye = _point_between(points, "left_eye_outer", "left_eye_inner")
    right_eye = _point_between(points, "right_eye_inner", "right_eye_outer")
    if left_eye is None or right_eye is None:
        return None
    return _midpoint(left_eye, right_eye)


def _ipd(points: dict, limitations: list[str]) -> LICDistance:
    if "left_pupil" in points and "right_pupil" in points:
        return safe_distance(points, "left_pupil", "right_pupil")

    left_eye = _point_between(points, "left_eye_outer", "left_eye_inner")
    right_eye = _point_between(points, "right_eye_inner", "right_eye_outer")
    used = [
        "left_eye_outer",
        "left_eye_inner",
        "right_eye_inner",
        "right_eye_outer",
    ]
    if left_eye is None or right_eye is None:
        return LICDistance(None, False, ["left_pupil", "right_pupil"])

    limitations.append(
        "ipd рассчитан по центрам глаз, потому что точки зрачков отсутствуют"
    )
    return LICDistance(distance(left_eye, right_eye), True, used)


def _candidate_from_virtual_points(
    points: dict,
    point_a,
    point_b,
    used_points: list[str],
) -> LICDistance:
    if point_a is None or point_b is None:
        return LICDistance(None, False, used_points)
    return LICDistance(distance(point_a, point_b), True, used_points)


def _recommended_base(candidates: dict[str, LICDistance]) -> Optional[str]:
    for name in (
        "ipd",
        "inner_eye_distance",
        "outer_eye_distance",
        "face_width",
        "nose_to_chin",
    ):
        candidate = candidates.get(name)
        if candidate and candidate.available and candidate.value:
            return name
    return None


def _ratios(
    candidates: dict[str, LICDistance],
    base_name: Optional[str],
) -> dict[str, float]:
    if not base_name:
        return {}
    base = candidates[base_name]
    if not base.available or not base.value:
        return {}

    result = {}
    for name, candidate in candidates.items():
        if name == base_name:
            continue
        if candidate.available and candidate.value is not None:
            result[f"{name}/{base_name}"] = candidate.value / base.value
    return result


def calculate_lic_core(points: dict) -> LICCore:
    """Рассчитать экспериментальный LIC Core по семантическим точкам."""
    limitations = []

    mouth_center = _mouth_center(points)
    eye_midpoint = _eye_midpoint(points)

    candidates = {
        "ipd": _ipd(points, limitations),
        "inner_eye_distance": safe_distance(
            points,
            "left_eye_inner",
            "right_eye_inner",
        ),
        "outer_eye_distance": safe_distance(
            points,
            "left_eye_outer",
            "right_eye_outer",
        ),
        "nose_to_mouth": _candidate_from_virtual_points(
            points,
            points.get("nose_tip"),
            mouth_center,
            ["nose_tip", "mouth_left", "mouth_right"],
        ),
        "mouth_to_chin": _candidate_from_virtual_points(
            points,
            mouth_center,
            points.get("chin"),
            ["mouth_left", "mouth_right", "chin"],
        ),
        "nose_to_chin": safe_distance(points, "nose_tip", "chin"),
        "eye_midpoint_to_nose": _candidate_from_virtual_points(
            points,
            eye_midpoint,
            points.get("nose_tip"),
            [
                "left_eye_outer",
                "left_eye_inner",
                "right_eye_inner",
                "right_eye_outer",
                "nose_tip",
            ],
        ),
        "face_width": safe_distance(points, "face_left", "face_right"),
        "cheekbone_width": safe_distance(
            points,
            "cheekbone_left",
            "cheekbone_right",
        ),
    }

    for name, candidate in candidates.items():
        if not candidate.available:
            limitations.append(
                f"{name}: недостаточно точек ({', '.join(candidate.points)})"
            )

    base_name = _recommended_base(candidates)
    return LICCore(
        version=LIC_CORE_VERSION,
        base_candidates=candidates,
        ratios=_ratios(candidates, base_name),
        recommended_base=base_name,
        limitations=list(dict.fromkeys(limitations)),
    )
