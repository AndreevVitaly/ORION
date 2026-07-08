"""Stability statistics for Profile geometric invariants."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any, Iterable

from portrait_core.archive.common import read_json, write_json
from portrait_core.invariants.invariant_export import invariant_set_from_dict
from portrait_core.invariants.invariant_models import InvariantSet, InvariantStats


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def stability_class(score: float | None, count: int) -> str:
    if count < 3 or score is None:
        return "insufficient_data"
    if 0.0 <= score < 0.05:
        return "excellent"
    if score < 0.10:
        return "stable"
    if score < 0.20:
        return "moderate"
    return "unstable"


def _load_invariant_set(value: str | Path | InvariantSet | dict[str, Any]) -> InvariantSet:
    if isinstance(value, InvariantSet):
        return value
    if isinstance(value, dict):
        return invariant_set_from_dict(value)
    return invariant_set_from_dict(read_json(value))


def compute_invariant_stats(
    invariant_sets: Iterable[str | Path | InvariantSet | dict[str, Any]],
) -> dict[str, InvariantStats]:
    sets = [_load_invariant_set(item) for item in invariant_sets]
    ratio_names = sorted({name for item in sets for name in item.ratios})
    result: dict[str, InvariantStats] = {}

    for name in ratio_names:
        values = [item.ratios[name].value for item in sets if name in item.ratios]
        count = len(values)
        missing_count = len(sets) - count
        if values:
            mean = statistics.fmean(values)
            median = statistics.median(values)
            variance = statistics.pvariance(values) if count > 1 else 0.0
            std = variance**0.5
            cv = None if mean == 0 else abs(std / mean)
            mad = statistics.median([abs(value - median) for value in values])
            min_value = min(values)
            max_value = max(values)
        else:
            mean = median = variance = std = cv = mad = min_value = max_value = None
        score = cv
        result[name] = InvariantStats(
            ratio_name=name,
            mean=_round(mean),
            median=_round(median),
            std=_round(std),
            variance=_round(variance),
            cv=_round(cv),
            mad=_round(mad),
            min=_round(min_value),
            max=_round(max_value),
            count=count,
            missing_count=missing_count,
            stability_score=_round(score),
            stability_class=stability_class(score, count),
        )
    return result


def build_invariant_stats(
    invariants_paths: Iterable[str | Path | InvariantSet | dict[str, Any]],
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    stats = compute_invariant_stats(invariants_paths)
    payload = {
        "schema": "profile.invariants.stats.v1",
        "stats": {name: item.to_dict() for name, item in sorted(stats.items())},
        "metadata": {
            "created_by": "portrait_core.invariants",
            "version": "0.1.0",
        },
    }
    if output_path is not None:
        write_json(output_path, payload)
    return payload
