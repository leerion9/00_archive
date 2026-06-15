"""Per-symbol Naver pagination cursor (resume after newer years)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.archive_schema import utc_now_iso


def cursor_path(base_dir: Path, symbol: str) -> Path:
    return base_dir / "manifest" / "cursors" / f"{str(symbol).strip()}.json"


def load_cursor(base_dir: Path, symbol: str) -> Optional[Dict[str, Any]]:
    path = cursor_path(base_dir, symbol)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_cursor(
    base_dir: Path,
    symbol: str,
    *,
    next_page: int,
    oldest_date: str = "",
    last_completed_year: int = 0,
) -> None:
    path = cursor_path(base_dir, symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "symbol": str(symbol).strip(),
        "next_page": max(1, int(next_page)),
        "oldest_date": str(oldest_date or "").strip(),
        "last_completed_year": int(last_completed_year),
        "updated_at_iso": utc_now_iso(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def start_page_for_fetch(base_dir: Path, symbol: str) -> int:
    cur = load_cursor(base_dir, symbol)
    if not cur:
        return 1
    return max(1, int(cur.get("next_page", 1) or 1))


def update_cursor_after_fetch(
    base_dir: Path,
    symbol: str,
    year: int,
    pages_fetched: list[int],
    bars: list[dict],
) -> None:
    if not pages_fetched:
        return
    dates = [str(b.get("date", "")) for b in bars if b.get("date")]
    oldest = min(dates) if dates else ""
    save_cursor(
        base_dir,
        symbol,
        next_page=max(pages_fetched) + 1,
        oldest_date=oldest,
        last_completed_year=int(year),
    )
