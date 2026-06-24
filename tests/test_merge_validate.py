"use Tests for core/merge_validate.py."""

from __future__ import annotations

import json

from core.archive_merge import merge_symbol
from core.archive_schema import build_chunk_payload, write_chunk
from core.merge_validate import DEFAULT_SAMPLE_SYMBOLS, validate_merged_symbol


def _write_chunk(base, worker, symbol, year, bars, fetched_at):
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


def test_validate_merged_symbol_passes(tmp_path):
    base = tmp_path
    (base / "config").mkdir(parents=True)
    (base / "config" / "collection_plan.json").write_text(
        json.dumps({"years": [2025, 2024]}),
        encoding="utf-8",
    )
    bar = {"date": "20251230", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 100}
    _write_chunk(base, "pc", "005930", 2025, [bar], "2026-06-01T00:00:00+00:00")
    merge_symbol(base, "005930", "삼성전자", years_planned=[2025, 2024])

    result = validate_merged_symbol(base, "005930", years_planned=[2025, 2024])
    assert result.ok, result.failures()
    assert result.bar_count == 1


def test_default_sample_panel_has_ten_symbols():
    assert len(DEFAULT_SAMPLE_SYMBOLS) == 10
