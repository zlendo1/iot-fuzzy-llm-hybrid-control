from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        result: dict[str, Any] = json.load(f)
        return result


def save_json(
    path: str | Path,
    data: dict[str, Any],
    indent: int = 2,
    atomic: bool = True,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if atomic:
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=str)
            f.write("\n")
        os.replace(temp_path, path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=str)
            f.write("\n")


def ensure_directory(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def format_timestamp(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


def generate_id(prefix: str = "") -> str:
    short_uuid = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{short_uuid}"
    return short_uuid
