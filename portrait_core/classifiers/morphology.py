"""Классификация морфологических признаков."""


def _classify(value, low, high, labels):
    if value is None:
        return None
    if value < low:
        return labels[0]
    if value > high:
        return labels[2]
    return labels[1]


def classify_morphology(measurements: dict) -> dict:
    """Описать измеряемые пропорции без психологической интерпретации."""
    face = measurements.get("face", {})
    jaw = measurements.get("jaw", {})
    mouth = measurements.get("mouth", {})
    symmetry = measurements.get("symmetry", {})

    return {
        "face_proportion": _classify(
            face.get("face_width_to_height_ratio"),
            0.65,
            0.80,
            ("вытянутое", "среднее", "широкое"),
        ),
        "jaw_width": _classify(
            jaw.get("jaw_width_ratio"),
            0.60,
            0.78,
            ("узкая", "средняя", "широкая"),
        ),
        "mouth_width": _classify(
            mouth.get("mouth_width_ratio"),
            0.35,
            0.48,
            ("узкий", "средний", "широкий"),
        ),
        "symmetry": _classify(
            symmetry.get("overall_score"),
            0.90,
            0.97,
            ("выраженная асимметрия", "умеренная симметрия", "высокая симметрия"),
        ),
    }
