"""Сборка измерительного профиля с явной оценкой доверия."""


PROFILE_SCHEMA_VERSION = 2


def _quality_confidence(quality: dict) -> float:
    checks = quality.get("checks", {})
    if not checks:
        return 0.0
    return sum(bool(value) for value in checks.values()) / len(checks)


def _feature_confidence(features: dict) -> float:
    confidences = [
        feature["confidence"]
        for feature in features.get("values", {}).values()
        if (
            feature.get("value") is not None
            and feature.get("role") == "morphology"
        )
    ]
    return sum(confidences) / len(confidences) if confidences else 0.0


def build_profile(
    morphology: dict,
    features: dict,
    quality: dict,
    pose: dict,
) -> dict:
    """Собрать профиль без психологических или поведенческих выводов."""
    quality_confidence = _quality_confidence(quality)
    feature_confidence = _feature_confidence(features)
    overall_confidence = (quality_confidence + feature_confidence) / 2
    limitations = []
    if quality.get("issues"):
        limitations.extend(quality["issues"])
    if abs(pose["yaw_proxy"]) > 0.12:
        limitations.append("поворот головы снижает надежность геометрии")
    if abs(pose["pitch_proxy"]) > 0.18:
        limitations.append("наклон головы вперед или назад снижает надежность")

    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "kind": "morphological-measurement-profile",
        "morphology": morphology,
        "dense_features": features["values"],
        "confidence": {
            "overall": overall_confidence,
            "image_quality": quality_confidence,
            "dense_geometry": feature_confidence,
            "components": {
                "landmark_validity": _component_confidence(
                    features, "landmark_validity"
                ),
                "pose": _component_confidence(features, "pose"),
                "zone_coverage": _component_confidence(
                    features, "zone_coverage"
                ),
                "stability": None,
            },
        },
        "limitations": list(dict.fromkeys(limitations)),
        "interpretation_policy": (
            "Только геометрические описания; психологические и поведенческие "
            "выводы не поддерживаются."
        ),
    }


def _component_confidence(features: dict, name: str) -> float | None:
    values = [
        feature.get("confidence_components", {}).get(name)
        for feature in features.get("values", {}).values()
    ]
    available = [value for value in values if value is not None]
    return sum(available) / len(available) if available else None
