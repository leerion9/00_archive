"""
Generate archive task manifest (symbols_active + tasks.jsonl).

  python -m scripts.archive_plan --years 2025
  python -m scripts.archive_plan --years 2025 --append
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from config.settings import settings
from core.archive_schema import utc_now_iso
from core.chunk_bounds import write_chunk_config
from core.manifest import load_tasks_jsonl, merge_tasks, save_tasks_jsonl
from core.naver_symbol_master import load_symbol_master
from core.shard import chunk_config_path, task_id

_log = logging.getLogger("archive")


def _parse_years(args: argparse.Namespace) -> list[int]:
    if args.years:
        return sorted({int(y) for y in args.years}, reverse=True)
    return list(range(int(settings.year_to), int(settings.year_from) - 1, -1))


def build_tasks(symbols: dict[str, str], years: list[int]) -> list[dict]:
    tasks: list[dict] = []
    for symbol in sorted(symbols.keys()):
        for year in years:
            tasks.append(
                {
                    "task_id": task_id(symbol, year),
                    "symbol": symbol,
                    "name": symbols[symbol],
                    "year": year,
                    "priority": year,
                    "status": "pending",
                }
            )
    return tasks


def write_symbols_active(path: Path, symbols: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "updated_at_iso": utc_now_iso(),
        "source": "kr_symbol_master",
        "count": len(symbols),
        "symbols": [
            {"symbol": code, "name": name} for code, name in sorted(symbols.items())
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_collection_plan(path: Path, years: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_years: list[int] = []
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            existing_years = [int(y) for y in raw.get("years", [])]
        except Exception:
            pass
    merged_years = sorted(set(existing_years + years), reverse=True)
    payload = {
        "schema_version": 1,
        "updated_at_iso": utc_now_iso(),
        "year_from": min(merged_years),
        "year_to": max(merged_years),
        "years": merged_years,
        "end_date": settings.end_date,
        "price_basis": "adjusted",
        "volume_basis": "raw",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parser = argparse.ArgumentParser(description="Generate archive task manifest")
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Years to plan (default: year_to..year_from from settings)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Merge new tasks into existing tasks.jsonl (keep done statuses)",
    )
    parser.add_argument(
        "--num-chunks",
        type=int,
        default=4,
        help="Symbol chunks for config/chunks.json (default: 4)",
    )
    args = parser.parse_args()

    symbols = load_symbol_master(settings.symbol_master_path)
    if not symbols:
        raise SystemExit(
            f"symbol master empty or missing: {settings.symbol_master_path}\n"
            "Run: python -m scripts.update_symbol_master"
        )

    years = _parse_years(args)
    new_tasks = build_tasks(symbols, years)
    base = settings.base_dir
    tasks_path = base / "manifest" / "tasks.jsonl"

    if args.append and tasks_path.exists():
        existing = load_tasks_jsonl(tasks_path)
        tasks = merge_tasks(existing, new_tasks)
    else:
        tasks = new_tasks

    sorted_syms = sorted(symbols.keys())
    chunks = write_chunk_config(
        chunk_config_path(base),
        sorted_syms,
        num_chunks=int(args.num_chunks),
    )

    write_symbols_active(base / "master" / "symbols_active.json", symbols)
    write_collection_plan(base / "config" / "collection_plan.json", years)
    save_tasks_jsonl(tasks_path, tasks)

    print(f"symbols: {len(symbols)}")
    print(f"years added/planned: {years}")
    print(f"tasks total: {len(tasks)}")
    print(f"chunks: {len(chunks)}")
    for c in chunks:
        print(f"  chunk {c['chunk_id']}: {c['from_symbol']}..{c['to_symbol']} ({c['count']})")
    print(f"written: {tasks_path}")


if __name__ == "__main__":
    main()
