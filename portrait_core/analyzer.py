"""Единая точка запуска объективных измерений лица."""

from portrait_core.classifiers.morphology import classify_morphology
from portrait_core.measurements.brows import measure_brows
from portrait_core.measurements.eyes import measure_eyes
from portrait_core.measurements.face import measure_face
from portrait_core.measurements.jaw import measure_jaw
from portrait_core.measurements.mouth import measure_mouth
from portrait_core.measurements.nose import measure_nose
from portrait_core.measurements.symmetry import measure_symmetry


def analyze_points(points: dict) -> dict:
    """Выполнить измерения и вернуть объективный морфологический профиль."""
    measurements = {
        "face": measure_face(points),
        "eyes": measure_eyes(points),
        "brows": measure_brows(points),
        "nose": measure_nose(points),
        "mouth": measure_mouth(points),
        "jaw": measure_jaw(points),
        "symmetry": measure_symmetry(points),
    }
    return {
        "measurements": measurements,
        "morphology": classify_morphology(measurements),
    }
