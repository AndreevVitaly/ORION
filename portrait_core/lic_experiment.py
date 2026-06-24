"""Эксперимент стабильности LIC Core по серии JSON-отчетов."""

import argparse
import json
import math
from pathlib import Path


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float], mean_value: float) -> float:
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _report_paths(directory: str) -> list[Path]:
    source = Path(directory)
    portrait_reports = sorted(source.glob("*_portrait.json"))
    if portrait_reports:
        return portrait_reports
    return sorted(source.glob("*.json"))


def _candidate_values(reports: list[dict]) -> dict[str, list[float]]:
    values = {}
    for report in reports:
        candidates = report.get("lic_core", {}).get("base_candidates", {})
        for name, candidate in candidates.items():
            if not candidate.get("available"):
                continue
            value = candidate.get("value")
            if isinstance(value, (int, float)):
                values.setdefault(name, []).append(float(value))
    return values


def analyze_lic_stability(report_directory: str) -> dict:
    """Рассчитать стабильность LIC-кандидатов по папке отчетов."""
    reports = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in _report_paths(report_directory)
    ]
    values_by_name = _candidate_values(reports)
    ranking = []

    for name, values in values_by_name.items():
        mean_value = _mean(values)
        std_value = _std(values, mean_value)
        cv = std_value / mean_value if mean_value else None
        ranking.append(
            {
                "name": name,
                "count": len(values),
                "mean": mean_value,
                "std": std_value,
                "coefficient_of_variation": cv,
                "min": min(values),
                "max": max(values),
            }
        )

    ranking.sort(
        key=lambda row: (
            row["coefficient_of_variation"] is None,
            row["coefficient_of_variation"] or float("inf"),
            row["name"],
        )
    )
    return {
        "experiment": "lic_core_stability",
        "reports_count": len(reports),
        "ranking": ranking,
        "best_candidate": ranking[0]["name"] if ranking else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Эксперимент стабильности LIC Core по JSON-отчетам"
    )
    parser.add_argument("report_directory")
    parser.add_argument("--output")
    return parser


def main():
    args = build_parser().parse_args()
    result = analyze_lic_stability(args.report_directory)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
