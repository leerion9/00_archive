"""Tests for core/market_fetch.py."""

from __future__ import annotations

from core.market_fetch import membership_lists_to_map, write_market_daily_cache, read_market_daily_cache


def test_membership_lists_to_map():
    m = membership_lists_to_map(["005930", "000020"], ["035720", "005930"])
    assert m["005930"] == "KOSPI"
    assert m["000020"] == "KOSPI"
    assert m["035720"] == "KOSDAQ"


def test_market_daily_cache_roundtrip(tmp_path):
    path = tmp_path / "20260102.json"
    write_market_daily_cache(path, "20260102", ["005930"], ["035720"])
    kospi, kosdaq = read_market_daily_cache(path)
    assert kospi == ["005930"]
    assert kosdaq == ["035720"]
