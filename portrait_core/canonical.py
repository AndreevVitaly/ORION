"""Канонизация плотной сетки и оценка положения головы."""

import math

from portrait_core.mesh import validate_mesh


def _vertex(mesh: dict, name: str) -> list:
    index = mesh["semantic_map"][name]
    return mesh["vertices"][index]


def _midpoint(point_a, point_b) -> list[float]:
    return [
        (point_a[0] + point_b[0]) / 2,
        (point_a[1] + point_b[1]) / 2,
        (point_a[2] + point_b[2]) / 2,
    ]


def _distance_2d(point_a, point_b) -> float:
    return math.hypot(point_b[0] - point_a[0], point_b[1] - point_a[1])


def estimate_pose(mesh: dict) -> dict:
    """Оценить roll и диагностические прокси yaw/pitch по ориентирам."""
    validate_mesh(mesh)
    left_eye = _midpoint(
        _vertex(mesh, "left_eye_outer"),
        _vertex(mesh, "left_eye_inner"),
    )
    right_eye = _midpoint(
        _vertex(mesh, "right_eye_inner"),
        _vertex(mesh, "right_eye_outer"),
    )
    eye_center = _midpoint(left_eye, right_eye)
    eye_distance = _distance_2d(left_eye, right_eye)
    if eye_distance == 0:
        raise ValueError("Невозможно канонизировать сетку с совпадающими глазами")

    roll = math.degrees(
        math.atan2(
            right_eye[1] - left_eye[1],
            right_eye[0] - left_eye[0],
        )
    )
    face_left = _vertex(mesh, "face_left")
    face_right = _vertex(mesh, "face_right")
    face_top = _vertex(mesh, "face_top")
    chin = _vertex(mesh, "chin")
    nose = _vertex(mesh, "nose_tip")

    face_width = _distance_2d(face_left, face_right)
    face_height = _distance_2d(face_top, chin)
    face_center_x = (face_left[0] + face_right[0]) / 2
    yaw_proxy = (
        (nose[0] - face_center_x) / face_width
        if face_width
        else 0.0
    )

    expected_nose_y = eye_center[1] + face_height * 0.22
    pitch_proxy = (
        (nose[1] - expected_nose_y) / face_height
        if face_height
        else 0.0
    )

    return {
        "roll_degrees": roll,
        "yaw_proxy": yaw_proxy,
        "pitch_proxy": pitch_proxy,
        "method": "semantic-geometry-v1",
        "metric_3d": False,
    }


def canonicalize_mesh(mesh: dict) -> dict:
    """Убрать перенос, масштаб и наклон плоскости изображения."""
    validate_mesh(mesh)
    pose = estimate_pose(mesh)
    left_eye = _midpoint(
        _vertex(mesh, "left_eye_outer"),
        _vertex(mesh, "left_eye_inner"),
    )
    right_eye = _midpoint(
        _vertex(mesh, "right_eye_inner"),
        _vertex(mesh, "right_eye_outer"),
    )
    origin = _midpoint(left_eye, right_eye)
    scale = _distance_2d(left_eye, right_eye)
    angle = math.radians(-pose["roll_degrees"])
    cosine = math.cos(angle)
    sine = math.sin(angle)

    vertices = []
    for vertex in mesh["vertices"]:
        translated_x = vertex[0] - origin[0]
        translated_y = vertex[1] - origin[1]
        rotated_x = translated_x * cosine - translated_y * sine
        rotated_y = translated_x * sine + translated_y * cosine
        depth = vertex[2] - origin[2] if len(vertex) == 3 else 0.0
        vertices.append(
            [
                float(rotated_x / scale),
                float(rotated_y / scale),
                float(depth / scale),
            ]
        )

    return {
        "schema": "portrait-canonical-mesh",
        "schema_version": 1,
        "coordinate_system": "eye-centered-interocular",
        "dimensions": 3,
        "vertices": vertices,
        "semantic_map": dict(mesh["semantic_map"]),
        "source_mesh_schema": (
            f'{mesh["schema"]}/{mesh["schema_version"]}'
        ),
        "transform": {
            "origin": origin,
            "scale": scale,
            "rotation_degrees": -pose["roll_degrees"],
        },
        "pose": pose,
        "contours": {
            name: list(indexes)
            for name, indexes in (
                mesh.get("metadata", {}).get("contours") or {}
            ).items()
        },
    }


def canonical_semantic_points(canonical_mesh: dict) -> dict:
    """Вернуть семантические точки канонической сетки."""
    return {
        name: list(canonical_mesh["vertices"][index])
        for name, index in canonical_mesh["semantic_map"].items()
    }
