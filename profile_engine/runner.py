"""Profile Engine runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from profile_engine.context import ProfileEngineContext
from profile_engine.manifest import write_manifest
from profile_engine.stages import StageFatalError, default_stages


def run_profile_engine(
    dataset_path: str | Path,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = ProfileEngineContext(Path(dataset_path), config=config or {})
    status = "completed"

    try:
        for stage in default_stages():
            try:
                result = stage.run(context)
            except StageFatalError as error:
                context.add_error(str(error))
                result = {
                    "name": stage.name,
                    "status": "failed",
                    "actions": [],
                    "warnings": [],
                    "errors": [str(error)],
                    "stats": {},
                    "artifacts": [],
                }
                context.add_stage_result(result)
                status = "failed"
                break
            except Exception as error:  # noqa: BLE001 - record and continue.
                context.add_warning(f"{stage.name} failed non-fatally: {error}")
                result = {
                    "name": stage.name,
                    "status": "warning",
                    "actions": [],
                    "warnings": [str(error)],
                    "errors": [],
                    "stats": {},
                    "artifacts": [],
                }
            context.add_stage_result(result)
            if result.get("status") == "warning" and status == "completed":
                status = "completed_with_warnings"
    finally:
        manifest_path = write_manifest(context, status=status)

    return {
        "status": status,
        "run_id": context.run_id,
        "dataset_id": context.dataset_id,
        "manifest_path": str(manifest_path),
        "warnings": context.warnings,
        "errors": context.errors,
        "artifacts": context.artifacts,
        "stages": context.stages,
    }
