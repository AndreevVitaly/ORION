"""Полный конвейер анализа одной фотографии."""

from portrait_core.adapters.mediapipe_adapter import MediaPipeAdapter
from portrait_core.analyzer import analyze_points
from portrait_core.quality import assess_image_quality
from portrait_core.reporting import build_report


def analyze_photo(image_path: str, model_path: str) -> tuple[dict, dict]:
    """Вернуть именованные точки и полный отчет по фотографии."""
    points = MediaPipeAdapter(model_path).extract_points(image_path)
    analysis = analyze_points(points)
    analysis["quality"] = assess_image_quality(image_path, points)
    return points, build_report(image_path, points, analysis)
