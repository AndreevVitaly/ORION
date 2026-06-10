"""Классификация морфологических признаков."""

from portrait_core.config import MORPHOLOGY_THRESHOLDS


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

    values = {
        "face_proportion": face.get("face_width_to_height_ratio"),
        "jaw_width": jaw.get("jaw_width_ratio"),
        "mouth_width": mouth.get("mouth_width_ratio"),
        "symmetry": symmetry.get("overall_score"),
    }
    result = {}
    for name, value in values.items():
        settings = MORPHOLOGY_THRESHOLDS[name]
        result[name] = _classify(
            value,
            settings["low"],
            settings["high"],
            settings["labels"],
        )
    return result
