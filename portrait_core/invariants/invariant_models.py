"""Data models for the Profile geometric invariant engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = "profile.invariants.v1"
ENGINE_VERSION = "0.1.0"


@dataclass(frozen=True)
class RatioDefinition:
    name: str
    numerator: str
    denominator: str
    category: str


@dataclass
class InvariantRatio:
    name: str
    numerator: str
    denominator: str
    value: float
    category: str
    source: str = "measurements"
    quality: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "category": self.category,
            "source": self.source,
            "quality": self.quality,
        }


@dataclass
class InvariantSet:
    portrait_id: str | None
    dataset_id: str | None
    pfr_id: str | None
    ratios: dict[str, InvariantRatio] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "portrait_id": self.portrait_id,
            "dataset_id": self.dataset_id,
            "pfr_id": self.pfr_id,
            "source": self.source,
            "ratios": {
                name: ratio.to_dict()
                for name, ratio in sorted(self.ratios.items())
            },
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }


@dataclass
class InvariantStats:
    ratio_name: str
    mean: float | None
    median: float | None
    std: float | None
    variance: float | None
    cv: float | None
    mad: float | None
    min: float | None
    max: float | None
    count: int
    missing_count: int
    stability_score: float | None
    stability_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ratio_name": self.ratio_name,
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "variance": self.variance,
            "cv": self.cv,
            "mad": self.mad,
            "min": self.min,
            "max": self.max,
            "count": self.count,
            "missing_count": self.missing_count,
            "stability_score": self.stability_score,
            "stability_class": self.stability_class,
        }
