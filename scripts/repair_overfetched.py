"""
Find over-fetched 2025 chunks, reset tasks, delete bad raw files.

  python -m scripts.repair_overfetched --year 2025 --min-pages 35
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from config.settings import settings
from core.manifest import load_tasks_jsonl, save_tasks_jsonl, update_task_status
from core.page_cursor import save_cursor

_log = logging.getLogger("archive")


def _reset_cursor_from_2026(base: Path, worker_id: str, symbol: str) -> None:
    chunk = base / "raw" / worker_id / symbol / "2026.json"
    cursor_path = base / "manifest" / "cursors" / f"{symbol}.json"
    if chunk.exists():
        try:
            data = json.loads(chunk.read_text(encoding="utf-8"))
            pages = data.get("pages_fetched") or []
            bars = data.get("bars") or []
            dates = [str(b.get("date", "")) for b in bars if b.get("date")]
            if pages:
                save_cursor(
                    base,
                    symbol,
                    next_page=max(int(p) for p in pages) + 1,
                    oldest_date=min(dates) if dates else "",
                    last_completed_year=2026,
                )
                return
        except Exception:
            pass
    if cursor_path.exists():
        cursor_path.unlink()


def find_overfetched(
    base: Path,
    worker_id: str,
    year: int,
    *,
    min_pages: int,
) -> list[dict]:
    raw_root = base / "raw" / worker_id
    bad: list[dict] = []
    if not raw_root.exists():
        return bad
    for sym_dir in sorted(raw_root.iterdir()):
        if not sym_dir.is_dir():
            continue
        chunk = sym_dir / f"{year}.json"
        if not chunk.exists():
            continue
        try:
            data = json.loads(chunk.read_text(encoding="utf-8"))
        except Exception:
            continue
        pages = data.get("pages_fetched") or []
        bars = data.get("bars") or []
        unique = len({str(b.get("date", "")) for b in bars if b.get("date")})
        if len(pages) >= min_pages or len(bars) > unique * 2:
            bad.append(
                {
                    "symbol": sym_dir.name,
                    "pages": len(pages),
                    "bars": len(bars),
                    "unique_dates": unique,
                    "path": chunk,
                }
            )
    return bad


def reset_for_recollection(
    base: Path,
    year: int,
    symbols: list[str],
    *,
    delete_raw: bool = True,
) -> None:
    tasks_path = base / "manifest" / "tasks.jsonl"
    tasks = load_tasks_jsonl(tasks_path)
    sym_set = set(symbols)
    for sym in symbols:
        tid = f"{sym}:{year}"
        update_task_status(tasks, tid, "pending")
        _reset_cursor_from_2026(base, settings.worker_id, sym)
        if delete_raw:
            chunk = base / "raw" / settings.worker_id / sym / f"{year}.json"
            if chunk.exists():
                chunk.unlink()
    save_tasks_jsonl(tasks_path, tasks)
    _log.info("reset %s tasks to pending (year=%s)", len(sym_set), year)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Reset over-fetched year chunks")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--min-pages", type=int, default=35)
    parser.add_argument("--apply", action="store_true", help="Reset tasks and delete raw files")
    args = parser.parse_args()

    base = settings.base_dir
    bad = find_overfetched(base, settings.worker_id, args.year, min_pages=args.min_pages)
    print(f"over-fetched (>={args.min_pages} pages or heavy dup): {len(bad)}")
    for row in bad[:10]:
        print(
            f"  {row['symbol']} pages={row['pages']} bars={row['bars']} unique={row['unique_dates']}"
        )
    if len(bad) > 10:
        print(f"  ... and {len(bad) - 10} more")

    if args.apply and bad:
        symbols = [r["symbol"] for r in bad]
        reset_for_recollection(base, args.year, symbols)
        list_path = Path("data/last_repair_symbols.txt")
        list_path.parent.mkdir(parents=True, exist_ok=True)
        list_path.write_text("\n".join(symbols) + "\n", encoding="utf-8")
        print(f"reset {len(bad)} symbols to pending")
        print(f"symbol list: {list_path}")


if __name__ == "__main__":
    main()
