"""Подготовка и сохранение результатов анализа."""

import json
from pathlib import Path


def build_report(
    image_path: str,
    points: dict,
    analysis: dict,
    *,
    mesh: dict | None = None,
    canonical_mesh: dict | None = None,
    zones: dict | None = None,
    features: dict | None = None,
) -> dict:
    """Собрать переносимый JSON-отчет."""
    return {
        "schema_version": 3,
        "image": str(Path(image_path).resolve()),
        "points": points,
        "mesh": mesh,
        "canonical_mesh": canonical_mesh,
        "zones": zones,
        "features": features,
        **analysis,
    }


def report_to_json(report: dict) -> str:
    """Сериализовать отчет в читаемый JSON."""
    return json.dumps(report, ensure_ascii=False, indent=2)


def save_report(report: dict, output_path: str) -> None:
    """Сохранить отчет в UTF-8."""
    Path(output_path).write_text(report_to_json(report), encoding="utf-8")
