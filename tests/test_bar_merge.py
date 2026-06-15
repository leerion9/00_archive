"""Tests for core/bar_merge.py."""

from __future__ import annotations

from core.bar_merge import filter_bars_by_year, merge_bars, normalize_date


def test_normalize_date():
    assert normalize_date("2026.06.12") == "20260612"
    assert normalize_date("20260612") == "20260612"


def test_merge_bars_dedup_and_newest_first():
    existing = [
        {"date": "20260520", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 100},
        {"date": "20260519", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 100},
    ]
    incoming = [
        {"date": "2026.06.21", "open": 3, "high": 4, "low": 3, "close": 4, "volume": 200},
        {"date": "2026.05.20", "open": 9, "high": 9, "low": 9, "close": 9, "volume": 999},
    ]
    merged = merge_bars(existing, incoming)
    assert [b["date"] for b in merged] == ["20260621", "20260520", "20260519"]
    assert merged[1]["close"] == 9


def test_filter_bars_by_year():
    bars = [
        {"date": "20251230", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        {"date": "20241230", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
    ]
    assert len(filter_bars_by_year(bars, 2025)) == 1
