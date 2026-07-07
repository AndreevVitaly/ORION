"""Компактная упаковка серии portrait JSON в один исследовательский отчет."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from portrait_core.archive.common import current_utc_iso, make_record_id, new_uuid, read_json
from portrait_core.lic_experiment import analyze_lic_stability, _report_paths
from portrait_core.lic_stability_report import build_lic_stability_report


HEAVY_FRAME_FIELDS = {"mesh", "points", "dense_features", "features"}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _summary_rows(report_directory: Path) -> list[dict]:
    summary_path = report_directory / "summary.json"
    if not summary_path.exists() and (report_directory.parent / "summary.json").exists():
        summary_path = report_directory.parent / "summary.json"
    if not summary_path.exists():
        return []
    data = _load_json(summary_path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        rows = data.get("rows")
        if isinstance(rows, list):
            return rows
        items = data.get("items")
        if isinstance(items, list):
            return [
                {
                    "image": item.get("image_path"),
                    "report": item.get("pfr_path"),
                    "status": item.get("status"),
                    "issues": "; ".join(item.get("issues") or []),
                    "pfr_id": item.get("pfr_id"),
                    "pfr_uuid": item.get("pfr_uuid"),
                }
                for item in items
            ]
    return []


def _dataset_metadata(report_directory: Path) -> dict:
    dataset_path = report_directory / "dataset.json"
    if not dataset_path.exists() and report_directory.name == "pfr":
        dataset_path = report_directory.parent / "dataset.json"
    if not dataset_path.exists():
        return {}
    try:
        dataset = read_json(dataset_path)
    except Exception:  # noqa: BLE001
        return {}
    return {
        "dataset_id": dataset.get("id"),
        "dataset_uuid": dataset.get("uuid"),
    }


def _pfr_records(reports: list[dict], paths: list[Path]) -> list[dict]:
    records = []
    for path, report in zip(paths, reports):
        records.append(
            {
                "pfr_id": report.get("id") or report.get("metadata", {}).get("pfr_id"),
                "pfr_uuid": report.get("uuid") or report.get("metadata", {}).get("pfr_uuid"),
                "report": path.name,
                "image": Path(str(report.get("image", ""))).name or None,
            }
        )
    return records


def _split_issues(value: str | list | None) -> list[str]:
    if isinstance(value, list):
        return [str(part) for part in value if str(part)]
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def _status_index(rows: list[dict]) -> dict[str, dict]:
    index = {}
    for row in rows:
        report_name = row.get("report")
        image_name = row.get("image")
        if report_name:
            index[Path(str(report_name)).name] = row
        if image_name:
            index[Path(str(image_name)).name] = row
    return index


def _quality_summary(rows: list[dict], reports_count: int) -> dict:
    statuses = Counter(row.get("status", "unknown") for row in rows)
    issues = Counter()
    for row in rows:
        for issue in _split_issues(row.get("issues")):
            issues[issue] += 1

    return {
        "statuses": dict(sorted(statuses.items())),
        "reports_count": reports_count,
        "summary_rows_count": len(rows),
        "common_issues": [
            {"issue": issue, "count": count}
            for issue, count in issues.most_common()
        ],
    }


def _morphology_summary(reports: list[dict]) -> dict:
    counters: dict[str, Counter] = defaultdict(Counter)
    for report in reports:
        morphology = report.get("morphology") or {}
        for name, value in morphology.items():
            if value is not None:
                counters[name][str(value)] += 1
    return {name: dict(counter.most_common()) for name, counter in sorted(counters.items())}


def _measurement_value(report: dict, path: tuple[str, ...]) -> float | None:
    current: Any = report.get("measurements") or {}
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current if isinstance(current, (int, float)) else None


def _numeric_stats(values: list[float]) -> dict | None:
    if not values:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = variance ** 0.5
    return {"count": len(values), "mean": mean, "std": std, "min": min(values), "max": max(values)}


def _measurement_summary(reports: list[dict]) -> dict:
    selected = {
        "face_width_to_height_ratio": ("face", "face_width_to_height_ratio"),
        "lower_face_height_ratio": ("face", "lower_face_height_ratio"),
        "eye_distance_ratio": ("eyes", "eye_distance_ratio"),
        "nose_width_to_length_ratio": ("nose", "nose_width_to_length_ratio"),
        "mouth_width_ratio": ("mouth", "mouth_width_ratio"),
        "jaw_width_ratio": ("jaw", "jaw_width_ratio"),
        "symmetry_overall_score": ("symmetry", "overall_score"),
    }
    result = {}
    for name, path in selected.items():
        values = [float(value) for report in reports if (value := _measurement_value(report, path)) is not None]
        stats = _numeric_stats(values)
        if stats:
            result[name] = stats
    return result


def _candidate_brief(report: dict) -> dict:
    lic_core = report.get("lic_core") or report.get("lic") or {}
    candidates = lic_core.get("base_candidates") or {}
    brief = {}
    for name, candidate in candidates.items():
        if isinstance(candidate, dict):
            brief[name] = {"value": candidate.get("value"), "available": bool(candidate.get("available"))}
    return brief


def _frame_rows(reports: list[dict], paths: list[Path], rows: list[dict]) -> list[dict]:
    status_by_key = _status_index(rows)
    frames = []
    for path, report in zip(paths, reports):
        image_path = Path(str(report.get("image", path.stem)))
        image_name = image_path.name
        summary = status_by_key.get(path.name) or status_by_key.get(image_name) or {}
        lic_core = report.get("lic_core") or report.get("lic") or {}
        frames.append(
            {
                "report": path.name,
                "image": image_name,
                "pfr_id": report.get("id"),
                "pfr_uuid": report.get("uuid"),
                "status": summary.get("status"),
                "issues": _split_issues(summary.get("issues")),
                "morphology": report.get("morphology") or {},
                "lic_recommended_base": lic_core.get("recommended_base"),
                "lic_base_candidates": _candidate_brief(report),
                "lic_limitations": lic_core.get("limitations") or [],
            }
        )
    return frames


def build_report_pack(
    report_directory: str,
    include_frames: bool = True,
    top: int = 10,
    dataset_id: str | None = None,
    experiment_id: str | None = None,
) -> dict:
    """Собрать компактный исследовательский пакет из папки PFR или Dataset Archive."""
    source = Path(report_directory)
    paths = _report_paths(report_directory)
    reports = [_load_json(path) for path in paths]
    rows = _summary_rows(source)
    dataset_meta = _dataset_metadata(source)
    resolved_dataset_id = dataset_id or dataset_meta.get("dataset_id")
    lic_stability = analyze_lic_stability(report_directory)
    point_stability = build_lic_stability_report(report_directory, top=top)

    pack = {
        "schema": "portrait-report-pack/1",
        "id": make_record_id("RP"),
        "uuid": new_uuid(),
        "created_at": current_utc_iso(),
        "dataset_id": resolved_dataset_id,
        "dataset_uuid": dataset_meta.get("dataset_uuid"),
        "experiment_id": experiment_id,
        "pfr_records": _pfr_records(reports, paths),
        "source_directory": str(source),
        "reports_count": len(reports),
        "quality": _quality_summary(rows, len(reports)),
        "lic_stability": lic_stability,
        "point_stability": {
            "experiment": point_stability.get("experiment"),
            "reports_count": point_stability.get("reports_count"),
            "normalization_base": point_stability.get("normalization_base"),
            "top_10": point_stability.get("top_10", [])[:top],
        },
        "morphology": _morphology_summary(reports),
        "measurements": _measurement_summary(reports),
        "limitations": [
            "Пакет является геометрической исследовательской сводкой и не делает выводов о личности, характере, интеллекте, профессиональной пригодности или надежности человека.",
            "Сырые points и mesh.vertices намеренно исключены из кадровой части, чтобы файл оставался компактным.",
        ],
    }
    if include_frames:
        pack["frames"] = _frame_rows(reports, paths, rows)
    return pack


def render_markdown(pack: dict) -> str:
    """Сформировать короткую Markdown-сводку для вставки в чат."""
    lines = [
        "# Profile Report Pack",
        "",
        f"Источник: `{pack.get('source_directory')}`",
        f"Отчетов: {pack.get('reports_count')}",
        "",
        "## Качество",
    ]
    statuses = pack.get("quality", {}).get("statuses", {})
    for status, count in statuses.items():
        lines.append(f"- {status}: {count}")

    common_issues = pack.get("quality", {}).get("common_issues", [])[:10]
    if common_issues:
        lines.extend(["", "## Частые предупреждения"])
        for row in common_issues:
            lines.append(f"- {row['issue']}: {row['count']}")

    lic = pack.get("lic_stability", {})
    lines.extend(["", "## LIC", f"Лучший кандидат: `{lic.get('best_candidate')}`"])
    for row in lic.get("ranking", [])[:8]:
        cv = row.get("coefficient_of_variation")
        cv_text = f"{cv:.4f}" if isinstance(cv, (int, float)) else "n/a"
        lines.append(f"- {row.get('name')}: count={row.get('count')}, CV={cv_text}")

    lines.extend(["", "## TOP стабильных точек"])
    for row in pack.get("point_stability", {}).get("top_10", []):
        lines.append(
            f"- {row.get('name')}: detection={row.get('detection_rate'):.3f}, "
            f"mean_displacement={row.get('mean_displacement'):.4f}, "
            f"position_std={row.get('position_std'):.4f}"
        )

    lines.extend([
        "",
        "## Ограничение",
        "Это геометрическая исследовательская сводка. Она не является психологическим, HR, криминалистическим или биометрическим выводом о человеке.",
    ])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Упаковать серию portrait JSON в компактный исследовательский отчет")
    parser.add_argument("report_directory")
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown")
    parser.add_argument("--no-frames", action="store_true")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--dataset-id")
    parser.add_argument("--experiment-id")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pack = build_report_pack(
        args.report_directory,
        include_frames=not args.no_frames,
        top=args.top,
        dataset_id=args.dataset_id,
        experiment_id=args.experiment_id,
    )
    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(pack), encoding="utf-8")


if __name__ == "__main__":
    main()
