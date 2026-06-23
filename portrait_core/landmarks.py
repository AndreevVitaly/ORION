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

LANDMARK_LABELS_RU = {
    "face_left": "лицо слева",
    "face_right": "лицо справа",
    "face_top": "верх лица",
    "chin": "подбородок",
    "left_eye_outer": "левый глаз внеш.",
    "left_eye_inner": "левый глаз внутр.",
    "right_eye_inner": "правый глаз внутр.",
    "right_eye_outer": "правый глаз внеш.",
    "nose_tip": "кончик носа",
    "nose_bridge": "переносица",
    "nose_left": "нос слева",
    "nose_right": "нос справа",
    "mouth_left": "рот слева",
    "mouth_right": "рот справа",
    "upper_lip": "верхняя губа",
    "lower_lip": "нижняя губа",
    "jaw_left": "челюсть слева",
    "jaw_right": "челюсть справа",
    "left_brow_outer": "левая бровь внеш.",
    "left_brow_inner": "левая бровь внутр.",
    "right_brow_inner": "правая бровь внутр.",
    "right_brow_outer": "правая бровь внеш.",
}


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
