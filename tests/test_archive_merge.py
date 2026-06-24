"""Tests for core/archive_merge.py."""

from __future__ import annotations

import json
from pathlib import Path

from core.archive_merge import (
    merge_all,
    merge_symbol,
    pick_newest_chunk,
    write_merged,
)
from core.archive_schema import build_chunk_payload, write_chunk


def _write_chunk(base: Path, worker: str, symbol: str, year: int, bars: list, fetched_at: str) -> Path:
    path = base / "raw" / worker / symbol / f"{year}.json"
    payload = build_chunk_payload(
        symbol=symbol,
        year=year,
        worker_id=worker,
        bars=bars,
        pages_fetched=[1],
    )
    payload["fetched_at_iso"] = fetched_at
    write_chunk(path, payload)
    return path


def test_pick_newest_chunk(tmp_path: Path):
    bars_a = [{"date": "20250102", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}]
    bars_b = [{"date": "20250103", "open": 2, "high": 2, "low": 2, "close": 2, "volume": 2}]
    path_a = _write_chunk(tmp_path, "pc", "005930", 2025, bars_a, "2026-06-01T00:00:00+00:00")
    path_b = _write_chunk(tmp_path, "laptop", "005930", 2025, bars_b, "2026-06-02T00:00:00+00:00")

    payload, warnings = pick_newest_chunk([path_a, path_b])
    assert payload["bars"][0]["date"] == "20250103"
    assert warnings


def test_merge_symbol_dedup_across_years(tmp_path: Path):
    base = tmp_path
    (base / "master").mkdir(parents=True)
    (base / "config").mkdir(parents=True)
    (base / "config" / "collection_plan.json").write_text(
        json.dumps({"years": [2025, 2024]}),
        encoding="utf-8",
    )
    _write_chunk(
        base,
        "pc",
        "005930",
        2025,
        [{"date": "20251230", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}],
        "2026-06-01T00:00:00+00:00",
    )
    _write_chunk(
        base,
        "pc",
        "005930",
        2024,
        [{"date": "20241230", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}],
        "2026-06-01T00:00:00+00:00",
    )

    result = merge_symbol(base, "005930", "삼성전자", years_planned=[2025, 2024])
    assert not result.skipped
    assert result.bar_count == 2
    assert result.years_complete == [2025, 2024]
    assert result.years_pending == []

    merged = json.loads(result.merged_path.read_text(encoding="utf-8"))
    assert merged["name"] == "삼성전자"
    assert merged["fields"]["market_cap"]["status"] == "empty"
    assert [b["date"] for b in merged["bars"]] == ["20251230", "20241230"]


def test_merge_all_skips_missing_raw(tmp_path: Path):
    base = tmp_path
    (base / "master").mkdir(parents=True)
    (base / "config").mkdir(parents=True)
    (base / "config" / "collection_plan.json").write_text(
        json.dumps({"years": [2025]}),
        encoding="utf-8",
    )
    (base / "master" / "symbols_active.json").write_text(
        json.dumps(
            {
                "symbols": [
                    {"symbol": "005930", "name": "삼성전자"},
                    {"symbol": "999999", "name": "없음"},
                ]
            }
        ),
        encoding="utf-8",
    )
    _write_chunk(
        base,
        "pc",
        "005930",
        2025,
        [{"date": "20251230", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}],
        "2026-06-01T00:00:00+00:00",
    )

    report = merge_all(base, years_planned=[2025])
    assert report.merged == 1
    assert report.skipped_no_raw == 1
    assert (base / "merged" / "005930.json").exists()
    assert not (base / "merged" / "999999.json").exists()
