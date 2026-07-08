"""Engine run manifest serialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from portrait_core.archive.common import current_utc_iso, write_json
from profile_engine.context import ProfileEngineContext


MANIFEST_SCHEMA = "profile.engine_run.v1"


def build_manifest(
    context: ProfileEngineContext,
    *,
    status: str,
    finished_at: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": MANIFEST_SCHEMA,
        "run_id": context.run_id,
        "dataset_id": context.dataset_id,
        "dataset_path": str(context.dataset_path),
        "started_at": context.started_at,
        "finished_at": finished_at or current_utc_iso(),
        "stages": context.stages,
        "artifacts": context.artifacts,
        "warnings": context.warnings,
        "errors": context.errors,
        "status": status,
        "config": context.config,
    }


def write_manifest(context: ProfileEngineContext, *, status: str) -> Path:
    target = context.dataset_path / "engine_run.json"
    context.add_artifact("engine_run_manifest", target)
    payload = build_manifest(context, status=status)
    write_json(target, payload)
    return target
