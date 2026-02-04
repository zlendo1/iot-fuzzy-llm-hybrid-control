import json
import tempfile
from pathlib import Path

import pytest


@pytest.mark.unit
def test_load_json_reads_valid_file() -> None:
    from src.common.utils import load_json

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"key": "value"}, f)
        f.flush()
        result = load_json(f.name)

    assert result == {"key": "value"}


@pytest.mark.unit
def test_save_json_writes_atomic_by_default(tmp_path: Path) -> None:
    from src.common.utils import load_json, save_json

    file_path = tmp_path / "test.json"
    data = {"foo": "bar", "num": 123}

    save_json(file_path, data)

    assert file_path.exists()
    assert load_json(file_path) == data


@pytest.mark.unit
def test_ensure_directory_creates_nested_dirs(tmp_path: Path) -> None:
    from src.common.utils import ensure_directory

    nested = tmp_path / "a" / "b" / "c"
    result = ensure_directory(nested)

    assert result.exists()
    assert result.is_dir()


@pytest.mark.unit
def test_format_timestamp_returns_iso_format() -> None:
    from datetime import datetime, timezone

    from src.common.utils import format_timestamp

    dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = format_timestamp(dt)

    assert result == "2025-01-15T10:30:00+00:00"


@pytest.mark.unit
def test_format_timestamp_uses_current_time_if_none() -> None:
    from src.common.utils import format_timestamp

    result = format_timestamp()

    assert "T" in result
    assert len(result) > 10


@pytest.mark.unit
def test_generate_id_returns_unique_ids() -> None:
    from src.common.utils import generate_id

    id1 = generate_id()
    id2 = generate_id()

    assert id1 != id2
    assert len(id1) == 12


@pytest.mark.unit
def test_generate_id_with_prefix() -> None:
    from src.common.utils import generate_id

    result = generate_id("rule")

    assert result.startswith("rule_")
    assert len(result) == 17
