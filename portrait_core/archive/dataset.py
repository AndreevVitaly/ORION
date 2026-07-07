"""Dataset archive creation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from portrait_core.archive.common import current_utc_iso, make_archive_id, new_uuid, write_json

DATASET_SCHEMA = {"name": "profile-dataset", "version": "1.0"}


def create_dataset_archive(
    output_root: str | Path,
    *,
    source: str | None = None,
    settings: dict[str, Any] | None = None,
    dataset_id: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Create an empty DS-* archive and return its path and metadata."""
    root = Path(output_root)
    resolved_id = dataset_id or (root.name if root.name.startswith("DS-") else make_archive_id("DS"))
    dataset_dir = root if root.name == resolved_id else root / resolved_id
    (dataset_dir / "images").mkdir(parents=True, exist_ok=True)
    (dataset_dir / "pfr").mkdir(parents=True, exist_ok=True)
    (dataset_dir / "experiments").mkdir(parents=True, exist_ok=True)

    dataset = {
        "schema": DATASET_SCHEMA,
        "id": resolved_id,
        "uuid": new_uuid(),
        "created_at": current_utc_iso(),
        "source": source,
        "settings": settings or {},
        "items": [],
        "summary": {
            "total_items": 0,
            "created_pfr": 0,
            "statuses": {"passed": 0, "warning": 0, "rejected": 0},
        },
    }
    write_dataset_files(dataset_dir, dataset)
    return dataset_dir, dataset


def summarize_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {"passed": 0, "warning": 0, "rejected": 0}
    for item in items:
        status = item.get("status") or "warning"
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "total_items": len(items),
        "created_pfr": sum(1 for item in items if item.get("pfr_path")),
        "statuses": statuses,
    }


def write_dataset_files(dataset_dir: str | Path, dataset: dict[str, Any]) -> None:
    """Persist dataset.json and a compact summary.json."""
    target = Path(dataset_dir)
    dataset["summary"] = summarize_items(list(dataset.get("items") or []))
    write_json(target / "dataset.json", dataset)
    summary = {
        "schema": "profile-dataset-summary/1",
        "dataset_id": dataset.get("id"),
        "dataset_uuid": dataset.get("uuid"),
        "source": dataset.get("source"),
        "settings": dataset.get("settings") or {},
        **dataset["summary"],
        "items": dataset.get("items") or [],
    }
    write_json(target / "summary.json", summary)
