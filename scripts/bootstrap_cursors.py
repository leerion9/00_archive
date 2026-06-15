"""
Bootstrap page cursors from completed 2026 raw chunks.

  python -m scripts.bootstrap_cursors
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from config.settings import settings
from core.page_cursor import save_cursor

_log = logging.getLogger("archive")


def bootstrap_from_raw(base: Path, worker_id: str = "pc", year: int = 2026) -> int:
    raw_root = base / "raw" / worker_id
    if not raw_root.exists():
        return 0
    count = 0
    for sym_dir in sorted(raw_root.iterdir()):
        if not sym_dir.is_dir():
            continue
        chunk_file = sym_dir / f"{year}.json"
        if not chunk_file.exists():
            continue
        try:
            data = json.loads(chunk_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        pages = data.get("pages_fetched") or []
        if not pages:
            continue
        bars = data.get("bars") or []
        dates = [str(b.get("date", "")) for b in bars if b.get("date")]
        oldest = min(dates) if dates else ""
        save_cursor(
            base,
            sym_dir.name,
            next_page=max(int(p) for p in pages) + 1,
            oldest_date=oldest,
            last_completed_year=year,
        )
        count += 1
    return count


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    n = bootstrap_from_raw(settings.base_dir, settings.worker_id, 2026)
    print(f"bootstrapped cursors: {n}")


if __name__ == "__main__":
    main()
