"""Common primitives for the Profile research archive."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def new_uuid() -> str:
    return str(uuid.uuid4())


def make_archive_id(prefix: str) -> str:
    return f"{prefix}-{timestamp_id()}"


def make_record_id(prefix: str, value: str | None = None) -> str:
    token = value or uuid.uuid4().hex[:12]
    return f"{prefix}-{token}"


def valid_uuid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        uuid.UUID(value)
    except (TypeError, ValueError, AttributeError):
        return False
    return True


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def as_posix(path: str | Path, base: str | Path | None = None) -> str:
    value = Path(path)
    if base is not None:
        try:
            value = value.relative_to(Path(base))
        except ValueError:
            pass
    return value.as_posix()
