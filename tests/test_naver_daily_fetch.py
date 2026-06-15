"""Tests for fetch dedup / stale stop helpers via fetch_pages_for_year."""

from __future__ import annotations

from unittest.mock import patch

from core.naver_daily import fetch_pages_for_year


def _bars(*dates: str):
    return [
        {
            "date": d,
            "open": 1,
            "high": 1,
            "low": 1,
            "close": 1,
            "volume": 1,
        }
        for d in dates
    ]


def test_stale_page_stops_without_duplicates():
    pages = {
        1: _bars("20251230", "20251229"),
        2: _bars("20251230", "20251229"),  # repeat -> stale
    }

    def fake_fetch(session, symbol, page, timeout=15.0):
        return pages.get(page, [])

    with patch("core.naver_daily.fetch_daily_page", side_effect=fake_fetch):
        result = fetch_pages_for_year(
            "005930",
            2025,
            start_page=1,
            max_pages_per_task=30,
        )
    assert result is not None
    assert len(result.bars) == 2
    assert len(result.pages_fetched) == 2
    assert result.aborted is True
    assert result.abort_reason.startswith("stale_page")


def test_page_budget_stops():
    def fake_fetch(session, symbol, page, timeout=15.0):
        d = f"2025{page:04d}"[:8]
        if page > 40:
            return _bars("20240102")
        return _bars(f"2025{min(page, 12):02d}01")

    with patch("core.naver_daily.fetch_daily_page", side_effect=fake_fetch):
        result = fetch_pages_for_year(
            "005930",
            2025,
            start_page=1,
            max_pages_per_task=5,
        )
    assert result is not None
    assert len(result.pages_fetched) == 5
    assert result.aborted is True
    assert "page_budget" in result.abort_reason
