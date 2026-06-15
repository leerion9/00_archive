"""OHLCV bar merge utilities (from moa core/history_cache.py, no bar count cap)."""

from __future__ import annotations

import re
from typing import Dict, List


def normalize_date(value: str) -> str:
    """Normalize YYYY.MM.DD or YYYYMMDD to YYYYMMDD."""
    text = str(value or "").strip()
    if re.match(r"^\d{4}\.\d{2}\.\d{2}$", text):
        return text.replace(".", "")
    if re.match(r"^\d{8}$", text):
        return text
    return text


def merge_bars(existing: List[Dict], incoming: List[Dict]) -> List[Dict]:
    """Merge OHLCV bars by date, newest-first. Later entries win on duplicate dates."""
    by_date: Dict[str, Dict] = {}
    for bar in existing + incoming:
        date_key = normalize_date(str(bar.get("date", "") or ""))
        if not date_key:
            continue
        by_date[date_key] = {
            "date": date_key,
            "open": int(bar.get("open", 0) or 0),
            "high": int(bar.get("high", 0) or 0),
            "low": int(bar.get("low", 0) or 0),
            "close": int(bar.get("close", 0) or 0),
            "volume": int(bar.get("volume", 0) or 0),
        }
    return sorted(by_date.values(), key=lambda b: b["date"], reverse=True)


def filter_bars_by_year(bars: List[Dict], year: int) -> List[Dict]:
    prefix = str(int(year))
    return [b for b in bars if str(b.get("date", "")).startswith(prefix)]


def year_bounds(year: int) -> tuple[str, str]:
    return f"{year}0101", f"{year}1231"
