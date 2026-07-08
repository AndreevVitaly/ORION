"""Ratio engine for geometric invariant candidates."""

from __future__ import annotations

from typing import Any

from portrait_core.invariants.invariant_models import (
    ENGINE_VERSION,
    InvariantRatio,
    InvariantSet,
    RatioDefinition,
)


RATIO_DEFINITIONS = (
    RatioDefinition("face_height_face_width", "face_height", "face_width", "face"),
    RatioDefinition("face_width_face_height", "face_width", "face_height", "face"),
    RatioDefinition("ipd_face_width", "ipd", "face_width", "eyes"),
    RatioDefinition("ipd_face_height", "ipd", "face_height", "eyes"),
    RatioDefinition("eye_width_left_face_width", "eye_width_left", "face_width", "eyes"),
    RatioDefinition("eye_width_right_face_width", "eye_width_right", "face_width", "eyes"),
    RatioDefinition("eye_height_left_face_height", "eye_height_left", "face_height", "eyes"),
    RatioDefinition("eye_height_right_face_height", "eye_height_right", "face_height", "eyes"),
    RatioDefinition("nose_length_face_height", "nose_length", "face_height", "nose"),
    RatioDefinition("nose_width_face_width", "nose_width", "face_width", "nose"),
    RatioDefinition("nose_width_ipd", "nose_width", "ipd", "nose"),
    RatioDefinition("mouth_width_face_width", "mouth_width", "face_width", "mouth"),
    RatioDefinition("mouth_width_nose_width", "mouth_width", "nose_width", "mouth"),
    RatioDefinition("upper_lip_height_mouth_width", "upper_lip_height", "mouth_width", "mouth"),
    RatioDefinition("lower_lip_height_mouth_width", "lower_lip_height", "mouth_width", "mouth"),
    RatioDefinition("jaw_width_face_width", "jaw_width", "face_width", "jaw"),
    RatioDefinition("chin_height_face_height", "chin_height", "face_height", "jaw"),
    RatioDefinition("jaw_width_ipd", "jaw_width", "ipd", "jaw"),
    RatioDefinition("forehead_height_face_height", "forehead_height", "face_height", "forehead"),
    RatioDefinition("forehead_width_face_width", "forehead_width", "face_width", "forehead"),
)


MEASUREMENT_ALIASES = {
    "face_width": (("face", "face_width"),),
    "face_height": (("face", "face_height"),),
    "ipd": (("eyes", "ipd"), ("eyes", "eye_distance")),
    "eye_width_left": (("eyes", "eye_width_left"), ("eyes", "left_eye_width")),
    "eye_width_right": (("eyes", "eye_width_right"), ("eyes", "right_eye_width")),
    "eye_height_left": (("eyes", "eye_height_left"), ("eyes", "left_eye_height")),
    "eye_height_right": (("eyes", "eye_height_right"), ("eyes", "right_eye_height")),
    "nose_length": (("nose", "nose_length"),),
    "nose_width": (("nose", "nose_width"),),
    "mouth_width": (("mouth", "mouth_width"),),
    "upper_lip_height": (("mouth", "upper_lip_height"),),
    "lower_lip_height": (("mouth", "lower_lip_height"),),
    "jaw_width": (("jaw", "jaw_width"),),
    "chin_height": (("jaw", "chin_height"),),
    "forehead_height": (("forehead", "forehead_height"),),
    "forehead_width": (("forehead", "forehead_width"),),
}


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _get_path(mapping: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = mapping
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def resolve_measurement(measurements: dict[str, Any], name: str) -> float | None:
    for path in MEASUREMENT_ALIASES.get(name, ((name,),)):
        value = _as_number(_get_path(measurements, path))
        if value is not None:
            return value
    return None


def build_invariant_set_from_pfr(
    pfr: dict[str, Any],
    *,
    source: dict[str, Any] | None = None,
) -> InvariantSet:
    measurements = pfr.get("measurements") or {}
    warnings: list[str] = []
    ratios: dict[str, InvariantRatio] = {}

    for definition in RATIO_DEFINITIONS:
        numerator = resolve_measurement(measurements, definition.numerator)
        denominator = resolve_measurement(measurements, definition.denominator)
        if numerator is None:
            warnings.append(f"{definition.name}: missing numerator {definition.numerator}")
            continue
        if denominator is None:
            warnings.append(f"{definition.name}: missing denominator {definition.denominator}")
            continue
        if denominator == 0:
            warnings.append(f"{definition.name}: zero denominator {definition.denominator}")
            continue
        ratios[definition.name] = InvariantRatio(
            name=definition.name,
            numerator=definition.numerator,
            denominator=definition.denominator,
            value=round(numerator / denominator, 6),
            category=definition.category,
        )

    pfr_id = pfr.get("id") or pfr.get("metadata", {}).get("pfr_id")
    return InvariantSet(
        portrait_id=pfr.get("portrait_id") or pfr_id,
        dataset_id=pfr.get("dataset_id") or pfr.get("metadata", {}).get("dataset_id"),
        pfr_id=pfr_id,
        ratios=ratios,
        warnings=warnings,
        source=source or {},
        metadata={
            "created_by": "portrait_core.invariants",
            "version": ENGINE_VERSION,
        },
    )
