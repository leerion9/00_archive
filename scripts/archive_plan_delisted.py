"""
Generate OHLCV task manifest for Step G delisted symbols (g2 plan).

  python -m scripts.archive_plan_delisted --years 2020 2021 2022 2023 2024 2025 2026
  python -m scripts.archive_plan_delisted --years 2020 2021 2022 2023 2024 2025 2026 --num-chunks 4
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from config.settings import settings
from core.archive_schema import utc_now_iso
from core.chunk_bounds import write_chunk_config
from core.listing_events import delisted_master_path, load_delisted_master
from core.listing_window import legacy_skip_tag, year_skip_reason
from core.manifest import load_tasks_jsonl, merge_tasks, save_tasks_jsonl
from core.shard import task_id

_log = logging.getLogger("archive")


def _parse_years(args: argparse.Namespace) -> list[int]:
    if args.years:
        return sorted({int(y) for y in args.years}, reverse=True)
    return list(range(2026, 2019, -1))


def _should_skip_year(rec: dict, year: int) -> str:
    reason = year_skip_reason(rec.get("listing_date"), rec.get("delisting_date"), year)
    return legacy_skip_tag(reason, year)


def build_delisted_tasks(records: list[dict], years: list[int]) -> list[dict]:
    tasks: list[dict] = []
    for rec in sorted(records, key=lambda r: r["symbol"]):
        symbol = str(rec["symbol"]).strip().zfill(6)
        name = str(rec.get("name") or "")
        for year in years:
            skip_reason = _should_skip_year(rec, int(year))
            status = "skipped" if skip_reason else "pending"
            task = {
                "task_id": task_id(symbol, year),
                "symbol": symbol,
                "name": name,
                "year": int(year),
                "priority": int(year),
                "status": status,
                "universe": "delisted_g3",
            }
            if skip_reason:
                task["error"] = skip_reason
            tasks.append(task)
    return tasks


def delisted_tasks_path(base_dir: Path) -> Path:
    return base_dir / "manifest" / "tasks_delisted.jsonl"


def delisted_chunk_config_path(base_dir: Path) -> Path:
    return base_dir / "config" / "chunks_delisted.json"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Plan delisted OHLCV tasks (Step G g2)")
    parser.add_argument("--years", type=int, nargs="+", help="Years (default 2020..2026)")
    parser.add_argument("--append", action="store_true", help="Merge into existing tasks_delisted.jsonl")
    parser.add_argument("--num-chunks", type=int, default=4)
    args = parser.parse_args()

    records = load_delisted_master(delisted_master_path(settings.base_dir))
    if not records:
        raise SystemExit(
            f"no delisted master at {delisted_master_path(settings.base_dir)}; run archive_listing_events --g1"
        )

    years = _parse_years(args)
    new_tasks = build_delisted_tasks(records, years)
    base = settings.base_dir
    tasks_path = delisted_tasks_path(base)

    if args.append and tasks_path.exists():
        tasks = merge_tasks(load_tasks_jsonl(tasks_path), new_tasks)
    else:
        tasks = new_tasks

    symbols = sorted({str(r["symbol"]).zfill(6) for r in records})
    chunks = write_chunk_config(
        delisted_chunk_config_path(base),
        symbols,
        num_chunks=int(args.num_chunks),
    )
    save_tasks_jsonl(tasks_path, tasks)

    pending = sum(1 for t in tasks if t.get("status") == "pending")
    skipped = sum(1 for t in tasks if t.get("status") == "skipped")
    print(f"delisted symbols: {len(symbols)}")
    print(f"years: {years}")
    print(f"tasks total: {len(tasks)} (pending={pending}, skipped={skipped})")
    print(f"chunks: {len(chunks)}")
    for c in chunks:
        print(f"  chunk {c['chunk_id']}: {c['from_symbol']}..{c['to_symbol']} ({c['count']})")
    print(f"written: {tasks_path}")
    print(f"chunk config: {delisted_chunk_config_path(base)}")


if __name__ == "__main__":
    main()
