"""Experiment records for the Profile research archive."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from portrait_core.archive.common import current_utc_iso, make_archive_id, new_uuid, write_json

EXPERIMENT_SCHEMA = {"name": "profile-experiment", "version": "1.0"}


def create_experiment_record(
    output_dir: str | Path,
    *,
    datasets: list[str] | None = None,
    method: str = "custom",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    hypotheses: list[str] | None = None,
    notes: str = "",
    experiment_id: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    resolved_id = experiment_id or make_archive_id("EXP")
    experiment_dir = Path(output_dir)
    if experiment_dir.name != resolved_id:
        experiment_dir = experiment_dir / resolved_id
    (experiment_dir / "reports").mkdir(parents=True, exist_ok=True)
    record = {
        "schema": EXPERIMENT_SCHEMA,
        "id": resolved_id,
        "uuid": new_uuid(),
        "created_at": current_utc_iso(),
        "datasets": datasets or [],
        "method": method,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "hypotheses": hypotheses or [],
        "notes": notes,
    }
    write_json(experiment_dir / "experiment.json", record)
    notes_path = experiment_dir / "notes.md"
    if not notes_path.exists():
        notes_path.write_text(f"# {resolved_id}\n\n{notes}\n", encoding="utf-8")
    return experiment_dir, record
