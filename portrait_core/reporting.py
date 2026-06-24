"""Подготовка и сохранение результатов анализа."""

import json
from pathlib import Path

from portrait_core.lic import calculate_lic_core


POSE_LIMITATION_TEXT = (
    "Интерпретация ограничена: показатель может быть связан с поворотом "
    "головы, наклоном, мимикой или перспективным искажением кадра, а не "
    "с устойчивой анатомической особенностью."
)
SERIES_LIMITATION_TEXT = (
    "Для вывода об устойчивой анатомической особенности нужна серия "
    "фронтальных нейтральных кадров."
)


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
    report = {
        "schema_version": 3,
        "image": str(Path(image_path).resolve()),
        "points": points,
        "mesh": mesh,
        "canonical_mesh": canonical_mesh,
        "zones": zones,
        "features": features,
        "lic_core": calculate_lic_core(points).to_dict(),
        **analysis,
    }
    report["interpretation"] = build_interpretation(report)
    return report


def build_interpretation(report: dict) -> dict:
    """Собрать безопасные текстовые пояснения к измерениям."""
    symmetry = _symmetry_interpretation(report)
    notes = [symmetry["text"]]
    if symmetry.get("limited_by_pose"):
        notes.append(POSE_LIMITATION_TEXT)
    else:
        notes.append(SERIES_LIMITATION_TEXT)

    quality = report.get("quality", {})
    issues = quality.get("issues") or []
    if issues:
        notes.append(
            "Качество кадра требует внимания: " + "; ".join(issues) + "."
        )

    return {
        "symmetry": symmetry,
        "notes": list(dict.fromkeys(notes)),
        "policy": "Только геометрическое описание изображения; психологические выводы не поддерживаются.",
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


def _is_limited_by_pose(quality: dict) -> bool:
    checks = quality.get("checks") or {}
    return checks.get("head_yaw") is False or checks.get("head_roll") is False


def _symmetry_interpretation(report: dict) -> dict:
    morphology = report.get("morphology", {})
    measurements = report.get("measurements", {})
    quality = report.get("quality", {})
    label = morphology.get("symmetry") or "нет данных"
    score = measurements.get("symmetry", {}).get("overall_score")
    limited_by_pose = _is_limited_by_pose(quality)

    if label == "выраженная асимметрия":
        text = "На изображении выявлена выраженная геометрическая асимметрия."
    elif label == "умеренная симметрия":
        text = "На изображении выявлена умеренная геометрическая симметрия."
    elif label == "высокая симметрия":
        text = "На изображении выявлена высокая геометрическая симметрия."
    else:
        text = "Геометрическую симметрию по изображению оценить не удалось."

    return {
        "label": label,
        "score": score,
        "limited_by_pose": limited_by_pose,
        "text": text,
    }


def format_summary_report(report: dict) -> str:
    """Сформировать короткий человекочитаемый отчет для CLI."""
    image_name = Path(report.get("image", "")).name or "без имени"
    quality = report.get("quality", {})
    morphology = report.get("morphology", {})
    measurements = report.get("measurements", {})
    profile = report.get("profile", {})
    confidence = profile.get("confidence", {})
    metrics = quality.get("metrics", {})
    interpretation = report.get("interpretation") or build_interpretation(report)

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

    notes = interpretation.get("notes") or []
    if notes:
        lines.append("")
        lines.append("Интерпретация:")
        lines.extend(f"- {note}" for note in notes)

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
