"""
Step G — listing events and delisted universe.

Step G phase: g0 (master) · g1 (listing_events) — see STEP_G_HANDOFF.md.

  python -m scripts.archive_listing_events --g0
  python -m scripts.archive_listing_events --g1
  python -m scripts.archive_listing_events --g0 --g1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config.settings import settings
from core.listing_events import (
    build_and_save_g1,
    build_and_save_g2,
    delisted_master_path,
    listing_events_path,
    load_delisted_master,
)


def _print_g0_summary(records: list, master_path: Path, report_path: Path) -> None:
    markets: dict[str, int] = {}
    for rec in records:
        m = rec.get("market") or "?"
        markets[m] = markets.get(m, 0) + 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    print("=== Step G g0 (delisted master + yearly report) ===")
    print(f"count: {len(records)}")
    print(f"markets: {markets}")
    print(f"counts_by_year: {report.get('counts_by_year')}")
    print(f"master: {master_path}")
    print(f"report: {report_path}")


def _print_g1_summary(payload: dict, path: Path, errors: list[str]) -> None:
    symbols = payload.get("symbols") or {}
    listed = sum(1 for row in symbols.values() if row.get("status") == "listed")
    delisted = sum(1 for row in symbols.values() if row.get("status") == "delisted")
    with_listing = sum(1 for row in symbols.values() if row.get("listing_date"))
    print("\n=== Step G g1 (listing_events.json) ===")
    print(f"total: {len(symbols)} (listed={listed}, delisted={delisted})")
    print(f"with listing_date: {with_listing}")
    print(f"path: {path}")
    if errors:
        print("validation errors:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("validation: OK")


def run_g0(*, year_from: int, year_to: int, exclude_konex: bool) -> list:
    records, master_path, report_path = build_and_save_g1(
        settings.base_dir,
        year_from=year_from,
        year_to=year_to,
        exclude_konex=exclude_konex,
    )
    _print_g0_summary(records, master_path, report_path)
    return records


def run_g1(records: list | None = None) -> int:
    if records is None:
        records = load_delisted_master(delisted_master_path(settings.base_dir))
    if not records:
        print("g1 requires g0 master; run --g0 first", file=sys.stderr)
        return 1

    payload, path, errors = build_and_save_g2(
        settings.base_dir,
        records,
        krx_id=settings.krx_id,
        krx_pw=settings.krx_pw,
    )
    _print_g1_summary(payload, path, errors)
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Step G g0/g1 — master + listing_events")
    parser.add_argument("--g0", action="store_true", help="g0: delisted master + yearly report")
    parser.add_argument("--g1", action="store_true", help="g1: listing_events.json")
    # 이전 CLI 호환 (같은 채팅에서 --g1/--g2 로 실행한 경우)
    parser.add_argument("--g2", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--year-from", type=int, default=2020)
    parser.add_argument("--year-to", type=int, default=2026)
    parser.add_argument(
        "--include-konex",
        action="store_true",
        help="Include KONEX (default: exclude 64 KONEX delisted)",
    )
    args = parser.parse_args()

    # legacy: --g1 only (old) → g0; --g2 (old) → g1
    if args.g2 and not args.g1:
        args.g1 = True
    if not args.g0 and not args.g1 and not args.g2:
        args.g0 = True
        args.g1 = True

    records: list | None = None
    if args.g0:
        records = run_g0(
            year_from=int(args.year_from),
            year_to=int(args.year_to),
            exclude_konex=not args.include_konex,
        )

    if args.g1:
        code = run_g1(records)
        if code:
            raise SystemExit(code)

    if args.g1 and listing_events_path(settings.base_dir).exists():
        print("\nNext (g2): python -m scripts.archive_plan_delisted --years 2020 2021 2022 2023 2024 2025 2026")
        print("Then: python -m scripts.archive_collect --tasks-file manifest/tasks_delisted.jsonl --chunk-config config/chunks_delisted.json --chunk 0")


if __name__ == "__main__":
    main()
