"""Реестр воспроизводимых признаков плотной геометрии."""

from dataclasses import asdict, dataclass
import math


FEATURE_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    zone: str
    unit: str
    method: str
    minimum_vertices: int = 3
    topology_invariant: bool = True
    ordered_contour: bool = False
    role: str = "morphology"


FEATURE_REGISTRY = (
    FeatureDefinition("face_bbox_ratio", "face", "ratio", "bbox_ratio"),
    FeatureDefinition("face_hull_area", "face", "canonical_area", "hull_area"),
    FeatureDefinition("face_hull_perimeter", "face", "canonical_length", "hull_perimeter"),
    FeatureDefinition("face_compactness", "face", "score", "compactness"),
    FeatureDefinition(
        "face_mirror_error",
        "face",
        "canonical_length",
        "mirror_error",
        role="diagnostic",
    ),
    FeatureDefinition(
        "lip_outer_height",
        "lips_outer",
        "canonical_length",
        "bbox_height",
        ordered_contour=True,
    ),
    FeatureDefinition(
        "mouth_opening_height",
        "mouth_opening",
        "canonical_length",
        "bbox_height",
        ordered_contour=True,
        role="expression",
    ),
    FeatureDefinition(
        "mouth_opening_area",
        "mouth_opening",
        "canonical_area",
        "polygon_area",
        ordered_contour=True,
        role="expression",
    ),
    FeatureDefinition(
        "lip_tissue_area",
        "lips_outer",
        "canonical_area",
        "lip_tissue_area",
        ordered_contour=True,
    ),
    FeatureDefinition(
        "upper_lip_curvature",
        "upper_lip",
        "score",
        "arc_chord_excess",
        ordered_contour=True,
    ),
    FeatureDefinition(
        "lower_lip_curvature",
        "lower_lip",
        "score",
        "arc_chord_excess",
        ordered_contour=True,
    ),
    FeatureDefinition(
        "lip_mirror_error",
        "lips_outer",
        "canonical_length",
        "mirror_error",
        ordered_contour=True,
        role="diagnostic",
    ),
    FeatureDefinition(
        "left_eye_density",
        "left_eye",
        "count",
        "vertex_count",
        1,
        False,
        False,
        "diagnostic",
    ),
    FeatureDefinition(
        "right_eye_density",
        "right_eye",
        "count",
        "vertex_count",
        1,
        False,
        False,
        "diagnostic",
    ),
    FeatureDefinition("nose_bbox_ratio", "nose", "ratio", "bbox_ratio"),
    FeatureDefinition("mouth_bbox_ratio", "mouth", "ratio", "bbox_ratio"),
    FeatureDefinition("jaw_hull_area", "jaw", "canonical_area", "hull_area"),
)


def _cross(origin, point_a, point_b) -> float:
    return (
        (point_a[0] - origin[0]) * (point_b[1] - origin[1])
        - (point_a[1] - origin[1]) * (point_b[0] - origin[0])
    )


def _convex_hull(points: list[list[float]]) -> list[list[float]]:
    unique = sorted({(point[0], point[1]) for point in points})
    if len(unique) <= 1:
        return [list(point) for point in unique]
    lower = []
    for point in unique:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return [list(point) for point in lower[:-1] + upper[:-1]]


def _hull_area(points: list[list[float]]) -> float | None:
    hull = _convex_hull(points)
    if len(hull) < 3:
        return None
    total = 0.0
    for index, point in enumerate(hull):
        next_point = hull[(index + 1) % len(hull)]
        total += point[0] * next_point[1] - next_point[0] * point[1]
    return abs(total) / 2


def _hull_perimeter(points: list[list[float]]) -> float | None:
    hull = _convex_hull(points)
    if len(hull) < 2:
        return None
    return sum(
        math.dist(hull[index], hull[(index + 1) % len(hull)])
        for index in range(len(hull))
    )


def _bbox_ratio(points: list[list[float]]) -> float | None:
    if not points:
        return None
    width = max(point[0] for point in points) - min(point[0] for point in points)
    height = max(point[1] for point in points) - min(point[1] for point in points)
    return width / height if height else None


def _bbox_height(points: list[list[float]]) -> float | None:
    if not points:
        return None
    return max(point[1] for point in points) - min(point[1] for point in points)


def _polygon_area(points: list[list[float]]) -> float | None:
    if len(points) < 3:
        return None
    total = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        total += point[0] * next_point[1] - next_point[0] * point[1]
    return abs(total) / 2


def _arc_chord_excess(points: list[list[float]]) -> float | None:
    if len(points) < 2:
        return None
    arc = sum(
        math.dist(points[index], points[index + 1])
        for index in range(len(points) - 1)
    )
    chord = math.dist(points[0], points[-1])
    return arc / chord - 1 if chord else None


def _compactness(points: list[list[float]]) -> float | None:
    area = _hull_area(points)
    perimeter = _hull_perimeter(points)
    if area is None or perimeter in (None, 0):
        return None
    return 4 * math.pi * area / (perimeter**2)


def _mirror_error(points: list[list[float]]) -> float | None:
    if len(points) < 2:
        return None
    errors = []
    for point in points:
        mirrored = (-point[0], point[1])
        nearest = min(
            math.dist(mirrored, (candidate[0], candidate[1]))
            for candidate in points
        )
        errors.append(nearest)
    return sum(errors) / len(errors)


def _calculate(method: str, points: list[list[float]]) -> float | None:
    calculators = {
        "bbox_ratio": _bbox_ratio,
        "bbox_height": _bbox_height,
        "hull_area": _hull_area,
        "hull_perimeter": _hull_perimeter,
        "polygon_area": _polygon_area,
        "arc_chord_excess": _arc_chord_excess,
        "compactness": _compactness,
        "mirror_error": _mirror_error,
        "vertex_count": lambda values: float(len(values)),
    }
    return calculators[method](points)


def extract_dense_features(
    canonical_mesh: dict,
    zone_assignments: dict,
    pose: dict,
    quality: dict | None = None,
) -> dict:
    """Рассчитать зарегистрированные признаки и доверие к ним."""
    pose_confidence = max(
        0.0,
        1.0
        - max(
            abs(pose["yaw_proxy"]) / 0.12,
            abs(pose["pitch_proxy"]) / 0.18,
            abs(pose["roll_degrees"]) / 15.0,
        ),
    )
    checks = (quality or {}).get("checks", {})
    quality_confidence = (
        sum(bool(value) for value in checks.values()) / len(checks)
        if checks
        else 1.0
    )
    contours = canonical_mesh.get("contours", {})
    values = {}
    for definition in FEATURE_REGISTRY:
        if definition.ordered_contour and definition.zone in contours:
            indexes = contours[definition.zone]
        else:
            indexes = zone_assignments.get(definition.zone, [])
        points = [canonical_mesh["vertices"][index] for index in indexes]
        enough_vertices = len(points) >= definition.minimum_vertices
        if definition.method == "lip_tissue_area" and enough_vertices:
            outer_area = _polygon_area(points)
            opening_points = [
                canonical_mesh["vertices"][index]
                for index in contours.get("mouth_opening", [])
            ]
            opening_area = _polygon_area(opening_points)
            value = (
                max(0.0, outer_area - opening_area)
                if outer_area is not None and opening_area is not None
                else None
            )
        else:
            value = _calculate(definition.method, points) if enough_vertices else None

        finite_coordinates = sum(
            all(math.isfinite(coordinate) for coordinate in point)
            for point in points
        )
        landmark_validity = (
            finite_coordinates / len(points) if points else 0.0
        )
        expected_count = (
            len(contours[definition.zone])
            if definition.ordered_contour and definition.zone in contours
            else max(definition.minimum_vertices * 4, 1)
        )
        zone_coverage = min(1.0, len(points) / expected_count)
        confidence_components = {
            "landmark_validity": landmark_validity,
            "pose": pose_confidence,
            "zone_coverage": zone_coverage,
            "image_quality": quality_confidence,
            "stability": None,
        }
        available_confidences = [
            component
            for component in confidence_components.values()
            if component is not None
        ]
        confidence = (
            sum(available_confidences) / len(available_confidences)
            if value is not None
            else 0.0
        )
        values[definition.name] = {
            "value": value,
            "confidence": confidence,
            "confidence_components": confidence_components,
            "zone": definition.zone,
            "unit": definition.unit,
            "method": definition.method,
            "vertex_count": len(points),
            "topology_invariant": definition.topology_invariant,
            "role": definition.role,
        }
    return {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "registry": [asdict(definition) for definition in FEATURE_REGISTRY],
        "values": values,
    }
