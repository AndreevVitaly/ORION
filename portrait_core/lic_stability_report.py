"""LIC Stability Report: рейтинг стабильности семантических точек лица."""

import argparse
import json
import math
from pathlib import Path

from portrait_core.lic_experiment import analyze_lic_stability, _report_paths


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float], mean_value: float) -> float:
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _midpoint(point_a, point_b) -> list[float]:
    return [
        (float(point_a[0]) + float(point_b[0])) / 2,
        (float(point_a[1]) + float(point_b[1])) / 2,
    ]


def _anchor_point(points: dict) -> list[float]:
    if "left_eye_inner" in points and "right_eye_inner" in points:
        return _midpoint(points["left_eye_inner"], points["right_eye_inner"])
    if "nose_tip" in points:
        return [float(points["nose_tip"][0]), float(points["nose_tip"][1])]
    return [0.0, 0.0]


def _base_value(report: dict, preferred_base: str | None) -> float | None:
    candidates = report.get("lic_core", {}).get("base_candidates", {})
    names = [preferred_base, report.get("lic_core", {}).get("recommended_base")]
    for name in names:
        if not name:
            continue
        candidate = candidates.get(name, {})
        value = candidate.get("value")
        if candidate.get("available") and isinstance(value, (int, float)) and value:
            return float(value)
    return None


def _normalized_points(report: dict, preferred_base: str | None) -> dict[str, list[float]]:
    points = report.get("points") or {}
    base = _base_value(report, preferred_base)
    if not points or not base:
        return {}

    anchor = _anchor_point(points)
    normalized = {}
    for name, point in points.items():
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        normalized[name] = [
            (float(point[0]) - anchor[0]) / base,
            (float(point[1]) - anchor[1]) / base,
        ]
    return normalized


def _point_stats(name: str, positions: list[list[float]], reports_count: int) -> dict:
    xs = [position[0] for position in positions]
    ys = [position[1] for position in positions]
    mean_x = _mean(xs)
    mean_y = _mean(ys)
    displacements = [
        math.dist(position, [mean_x, mean_y])
        for position in positions
    ]
    mean_displacement = _mean(displacements) if displacements else 0.0
    position_std = _std(displacements, mean_displacement) if displacements else 0.0

    return {
        "name": name,
        "count": len(positions),
        "detection_rate": len(positions) / reports_count if reports_count else 0.0,
        "mean_position": {
            "x": mean_x,
            "y": mean_y,
        },
        "mean_displacement": mean_displacement,
        "position_std": position_std,
        "std_x": _std(xs, mean_x),
        "std_y": _std(ys, mean_y),
    }


def build_lic_stability_report(report_directory: str, top: int = 10) -> dict:
    """Построить TOP стабильных точек по серии JSON-отчетов."""
    paths = _report_paths(report_directory)
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    base_stability = analyze_lic_stability(report_directory)
    preferred_base = base_stability.get("best_candidate")

    positions_by_name = {}
    for report in reports:
        normalized = _normalized_points(report, preferred_base)
        for name, position in normalized.items():
            positions_by_name.setdefault(name, []).append(position)

    ranking = [
        _point_stats(name, positions, len(reports))
        for name, positions in positions_by_name.items()
    ]
    ranking.sort(
        key=lambda row: (
            -row["detection_rate"],
            row["mean_displacement"],
            row["position_std"],
            row["name"],
        )
    )

    return {
        "experiment": "lic_point_stability",
        "reports_count": len(reports),
        "normalization_base": preferred_base,
        "anchor": "inner_eye_midpoint_or_nose_tip",
        "ranking": ranking,
        "top_10": ranking[:top],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Рейтинг стабильности опорных точек LIC по JSON-отчетам"
    )
    parser.add_argument("report_directory")
    parser.add_argument("--output")
    parser.add_argument("--top", type=int, default=10)
    return parser


def main():
    args = build_parser().parse_args()
    result = build_lic_stability_report(args.report_directory, top=args.top)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
