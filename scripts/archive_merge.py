"""
Merge raw year chunks into per-symbol merged JSON (Phase 1b / Step A).

  python -m scripts.archive_merge
  python -m scripts.archive_merge --years 2020 2021 2022 2023 2024 2025 2026
  python -m scripts.archive_merge --symbols 005930 000660
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime

from config.settings import settings
from core.archive_merge import load_collection_plan_years, merge_all

_log = logging.getLogger("archive")


def _configure_logging() -> None:
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"archive_merge_{date_tag}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )


def _print_summary(report) -> None:
    print("\n=== merge summary ===")
    print(
        f"years_planned={report.years_planned} "
        f"symbols_total={report.symbols_total} merged={report.merged} "
        f"skipped_no_raw={report.skipped_no_raw} warnings={len(report.warnings)}"
    )
    if report.skipped_no_raw:
        skipped = [s for s in report.symbols if s.skipped]
        print(f"skipped_no_raw ({len(skipped)}):")
        for s in skipped[:20]:
            print(f"  {s.symbol} ({s.name or '?'})")
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more")
    if report.warnings:
        print(f"duplicate worker warnings ({len(report.warnings)}):")
        for msg in report.warnings[:10]:
            print(f"  {msg}")
        if len(report.warnings) > 10:
            print(f"  ... and {len(report.warnings) - 10} more")

    merged = [s for s in report.symbols if not s.skipped]
    if merged:
        total_bars = sum(s.bar_count for s in merged)
        print(f"total_bars={total_bars} avg_bars={total_bars / len(merged):.1f}")


def main() -> None:
    _configure_logging()
    parser = argparse.ArgumentParser(description="Merge raw archive chunks into merged/{symbol}.json")
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Planned years for years_complete/pending (default: collection_plan.json)",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Merge only these symbols (default: symbols_active + raw)",
    )
    args = parser.parse_args()

    base = settings.base_dir
    years = sorted({int(y) for y in args.years}, reverse=True) if args.years else load_collection_plan_years(base)
    if not years:
        raise SystemExit(
            f"no years configured; pass --years or write {base / 'config' / 'collection_plan.json'}"
        )

    _log.info("archive_merge years=%s symbols=%s", years, args.symbols or "all")
    report = merge_all(
        base,
        years_planned=years,
        symbols=args.symbols,
    )

    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    report_path = reports_dir / f"merge_report_{date_tag}.json"
    report_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    _print_summary(report)
    print(f"report: {report_path}")
    _log.info(
        "merge done merged=%s skipped_no_raw=%s warnings=%s",
        report.merged,
        report.skipped_no_raw,
        len(report.warnings),
    )


if __name__ == "__main__":
    main()
