"""Tests for core/page_cursor.py."""

from __future__ import annotations

from core.page_cursor import load_cursor, save_cursor, start_page_for_fetch


def test_cursor_roundtrip(tmp_path):
    save_cursor(tmp_path, "005930", next_page=12, oldest_date="20260102", last_completed_year=2026)
    assert start_page_for_fetch(tmp_path, "005930") == 12
    cur = load_cursor(tmp_path, "005930")
    assert cur["last_completed_year"] == 2026


def test_start_page_default(tmp_path):
    assert start_page_for_fetch(tmp_path, "005930") == 1
