"""Контракт именованных точек лица, используемых измерительным ядром."""

REQUIRED_LANDMARKS = frozenset(
    {
        "face_left",
        "face_right",
        "face_top",
        "chin",
        "left_eye_outer",
        "left_eye_inner",
        "right_eye_inner",
        "right_eye_outer",
        "nose_tip",
        "nose_bridge",
        "nose_left",
        "nose_right",
        "mouth_left",
        "mouth_right",
        "upper_lip",
        "lower_lip",
        "jaw_left",
        "jaw_right",
        "left_brow_outer",
        "left_brow_inner",
        "right_brow_inner",
        "right_brow_outer",
    }
)


def validate_landmarks(points: dict) -> None:
    """Проверить полноту и формат словаря точек."""
    if not isinstance(points, dict):
        raise TypeError("Точки лица должны быть переданы словарем")

    missing = sorted(REQUIRED_LANDMARKS - points.keys())
    if missing:
        raise ValueError(f"Отсутствуют обязательные точки: {', '.join(missing)}")

    for name in REQUIRED_LANDMARKS:
        point = points[name]
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"Точка {name} должна иметь формат [x, y]")
        if not all(isinstance(value, (int, float)) for value in point):
            raise TypeError(f"Координаты точки {name} должны быть числами")
