"""Validation for Dataset Archives."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from portrait_core.archive.common import read_json, valid_uuid


def _dataset_json_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        return candidate / "dataset.json"
    return candidate


def validate_dataset_archive(path: str | Path) -> dict[str, Any]:
    dataset_path = _dataset_json_path(path)
    errors: list[str] = []
    warnings: list[str] = []
    if not dataset_path.exists():
        return {"valid": False, "errors": [f"dataset.json not found: {dataset_path}"], "warnings": [], "items_checked": 0}

    dataset = read_json(dataset_path)
    dataset_dir = dataset_path.parent
    dataset_uuid = dataset.get("uuid")
    if not valid_uuid(dataset_uuid):
        errors.append("dataset.uuid is missing or invalid")
    if not dataset.get("id"):
        errors.append("dataset.id is missing")

    items = dataset.get("items") or []
    if not isinstance(items, list):
        errors.append("dataset.items must be a list")
        items = []

    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        pfr_uuid = item.get("pfr_uuid")
        if pfr_uuid is not None and not valid_uuid(pfr_uuid):
            errors.append(f"{prefix}.pfr_uuid is invalid")
        pfr_path = item.get("pfr_path")
        if pfr_path:
            resolved = dataset_dir / pfr_path
            if not resolved.exists():
                errors.append(f"{prefix}.pfr_path does not exist: {pfr_path}")
            else:
                try:
                    pfr = read_json(resolved)
                except Exception as error:  # noqa: BLE001
                    errors.append(f"{prefix}.pfr_path is not readable JSON: {error}")
                    continue
                if pfr.get("uuid") and not valid_uuid(pfr.get("uuid")):
                    errors.append(f"{prefix}.PFR uuid is invalid")
                if pfr_uuid and pfr.get("uuid") and pfr_uuid != pfr.get("uuid"):
                    errors.append(f"{prefix}.pfr_uuid does not match PFR uuid")
        elif item.get("status") != "rejected":
            warnings.append(f"{prefix} has no pfr_path")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "items_checked": len(items),
        "dataset_id": dataset.get("id"),
        "dataset_uuid": dataset_uuid,
    }
