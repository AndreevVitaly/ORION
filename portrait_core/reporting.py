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


def _format_percent(value):
    if value is None:
        return "нет данных"
    return f"{value:.0%}"


def _format_float(value, digits=2):
    if value is None:
        return "нет данных"
    return f"{value:.{digits}f}"


def _quality_label(quality: dict) -> str:
    status = quality.get("status")
    if status == "passed":
        return "подходит"
    if status == "warning":
        return "требует внимания"
    if status == "error":
        return "ошибка анализа"
    return "нет данных"


def format_summary_report(report: dict) -> str:
    """Сформировать короткий человекочитаемый отчет для CLI."""
    image_name = Path(report.get("image", "")).name or "без имени"
    quality = report.get("quality", {})
    morphology = report.get("morphology", {})
    measurements = report.get("measurements", {})
    profile = report.get("profile", {})
    confidence = profile.get("confidence", {})
    metrics = quality.get("metrics", {})

    lines = [
        "ПОРТРЕТ: краткий отчет",
        f"Файл: {image_name}",
        f"Качество кадра: {_quality_label(quality)}",
    ]

    issues = quality.get("issues") or []
    if issues:
        lines.append("Предупреждения:")
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("Предупреждения: нет")

    lines.extend(
        [
            "",
            "Морфология:",
            f"- пропорция лица: {morphology.get('face_proportion', 'нет данных')}",
            f"- ширина челюсти: {morphology.get('jaw_width', 'нет данных')}",
            f"- ширина рта: {morphology.get('mouth_width', 'нет данных')}",
            f"- симметрия: {morphology.get('symmetry', 'нет данных')}",
        ]
    )

    symmetry = measurements.get("symmetry", {}).get("overall_score")
    face = measurements.get("face", {})
    lines.extend(
        [
            "",
            "Ключевые числа:",
            f"- индекс симметрии: {_format_float(symmetry, 3)}",
            f"- отношение ширины лица к высоте: {_format_float(face.get('face_width_to_height_ratio'), 3)}",
            f"- наклон головы: {_format_float(metrics.get('roll_degrees'), 1)}°",
            f"- доля лица в кадре: {_format_percent(metrics.get('face_coverage'))}",
            f"- общая уверенность: {_format_percent(confidence.get('overall'))}",
        ]
    )

    limitations = profile.get("limitations") or []
    if limitations:
        lines.append("")
        lines.append("Ограничения:")
        lines.extend(f"- {limitation}" for limitation in limitations)

    lines.extend(
        [
            "",
            "Важно: это геометрическое описание, не психологический вывод.",
            "Полный JSON можно получить флагом --json или сохранить через --output.",
        ]
    )
    return "\n".join(lines)


def save_report(report: dict, output_path: str) -> None:
    """Сохранить отчет в UTF-8."""
    Path(output_path).write_text(report_to_json(report), encoding="utf-8")
