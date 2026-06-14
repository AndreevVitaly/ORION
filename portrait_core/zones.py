"""Топологически независимые анатомические зоны канонической сетки."""

from portrait_core.canonical import canonical_semantic_points


ZONE_SCHEMA_VERSION = 2


def _bounds(points: dict, names: tuple[str, ...], padding: float) -> dict:
    selected = [points[name] for name in names]
    min_x = min(point[0] for point in selected) - padding
    max_x = max(point[0] for point in selected) + padding
    min_y = min(point[1] for point in selected) - padding
    max_y = max(point[1] for point in selected) + padding
    return {
        "kind": "bounds",
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
    }


def _contour_definition(canonical_mesh: dict, name: str, kind: str) -> dict | None:
    indexes = canonical_mesh.get("contours", {}).get(name)
    if not indexes:
        return None
    return {
        "kind": kind,
        "indexes": list(indexes),
    }


def build_zone_definitions(canonical_mesh: dict) -> dict:
    """Построить зоны через проектные ориентиры, а не индексы backend."""
    points = canonical_semantic_points(canonical_mesh)
    fallback_definitions = {
        "face": _bounds(
            points,
            ("face_left", "face_right", "face_top", "chin"),
            0.08,
        ),
        "left_eye": _bounds(
            points,
            ("left_eye_outer", "left_eye_inner"),
            0.10,
        ),
        "right_eye": _bounds(
            points,
            ("right_eye_inner", "right_eye_outer"),
            0.10,
        ),
        "left_brow": _bounds(
            points,
            ("left_brow_outer", "left_brow_inner"),
            0.10,
        ),
        "right_brow": _bounds(
            points,
            ("right_brow_inner", "right_brow_outer"),
            0.10,
        ),
        "nose": _bounds(
            points,
            ("nose_bridge", "nose_tip", "nose_left", "nose_right"),
            0.10,
        ),
        "mouth": _bounds(
            points,
            ("mouth_left", "mouth_right", "upper_lip", "lower_lip"),
            0.10,
        ),
        "jaw": _bounds(
            points,
            ("jaw_left", "jaw_right", "chin"),
            0.10,
        ),
    }
    contour_kinds = {
        "face_oval": "polygon",
        "left_eye": "polygon",
        "right_eye": "polygon",
        "nose": "polygon",
        "lips_outer": "polygon",
        "mouth_opening": "polygon",
        "upper_lip": "contour",
        "lower_lip": "contour",
        "jaw": "contour",
        "left_brow": "contour",
        "right_brow": "contour",
    }
    definitions = {}
    for name, kind in contour_kinds.items():
        definition = _contour_definition(canonical_mesh, name, kind)
        if definition is not None:
            definitions[name] = definition

    aliases = {
        "face": "face_oval",
        "mouth": "lips_outer",
    }
    for zone_name, contour_name in aliases.items():
        if contour_name in definitions:
            definitions[zone_name] = dict(definitions[contour_name])

    for name, fallback in fallback_definitions.items():
        definitions.setdefault(name, fallback)

    return {
        "schema_version": ZONE_SCHEMA_VERSION,
        "method": "project-contours-with-semantic-fallback-v2",
        "definitions": definitions,
    }


def _point_in_polygon(point, polygon) -> bool:
    x, y = point[0], point[1]
    inside = False
    previous = polygon[-1]
    for current in polygon:
        x1, y1 = previous[0], previous[1]
        x2, y2 = current[0], current[1]
        intersects = (y1 > y) != (y2 > y)
        if intersects:
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def assign_vertices_to_zones(canonical_mesh: dict, zones: dict) -> dict:
    """Назначить каждой зоне все попавшие в её границы вершины."""
    assignments = {}
    vertices = canonical_mesh["vertices"]
    for zone_name, definition in zones["definitions"].items():
        if definition["kind"] == "contour":
            assignments[zone_name] = list(definition["indexes"])
            continue
        if definition["kind"] == "polygon":
            contour_indexes = definition["indexes"]
            polygon = [vertices[index] for index in contour_indexes]
            inside = [
                index
                for index, vertex in enumerate(vertices)
                if _point_in_polygon(vertex, polygon)
            ]
            assignments[zone_name] = list(
                dict.fromkeys([*contour_indexes, *inside])
            )
            continue
        assignments[zone_name] = [
            index
            for index, vertex in enumerate(vertices)
            if (
                definition["min_x"] <= vertex[0] <= definition["max_x"]
                and definition["min_y"] <= vertex[1] <= definition["max_y"]
            )
        ]
    return assignments
