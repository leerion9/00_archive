"""
Step B: compute derived sidecar fields (trading_value, value_ma5, close_ma5).

  python -m scripts.archive_enrich_derived
  python -m scripts.archive_enrich_derived --years 2020 2021 2022 2023 2024 2025 2026
  python -m scripts.archive_enrich_derived --chunk 0
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime

from config.settings import settings
from core.archive_merge import load_collection_plan_years
from core.enrich_derived import enrich_all_derived, list_merged_symbols
from core.shard import chunk_config_path

_log = logging.getLogger("archive")


def _configure_logging(chunk_id: int | None) -> None:
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    chunk_tag = f"_c{chunk_id}" if chunk_id is not None else ""
    log_file = log_dir / f"archive_enrich_derived{chunk_tag}_{date_tag}.log"

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
    print("\n=== enrich_derived summary ===")
    print(
        f"years={report.years} symbols_total={report.symbols_total} "
        f"enriched={report.enriched} skipped={report.skipped} failed={report.failed}"
    )
    enriched = [r for r in report.results if r.ok]
    if enriched:
        rows = sum(r.row_count for r in enriched)
        print(f"feature_rows={rows} avg_rows={rows / len(enriched):.1f}")
    failed = [r for r in report.results if r.error and not r.skipped]
    if failed:
        print(f"failed ({len(failed)}):")
        for r in failed[:10]:
            print(f"  {r.symbol}: {r.error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich derived sidecar fields from merged bars")
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Limit output rows to these years (MA computed on full merged bars)",
    )
    parser.add_argument("--symbols", nargs="+", help="Only these symbols")
    parser.add_argument("--chunk", type=int, help="Symbol chunk id (0..3)")
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=0,
        help="Max symbols to process (0 = all in scope)",
    )
    args = parser.parse_args()

    _configure_logging(args.chunk)
    base = settings.base_dir
    years = sorted({int(y) for y in args.years}, reverse=True) if args.years else load_collection_plan_years(base)

    symbols = list(args.symbols) if args.symbols else None
    if symbols is None:
        symbols = list_merged_symbols(base)
        if args.chunk is not None:
            from core.chunk_bounds import assign_chunk

            bounds = chunk_config_path(base)
            symbols = [s for s in symbols if assign_chunk(s, int(args.chunk), bounds)]
        if args.max_symbols > 0:
            symbols = symbols[: args.max_symbols]
    elif args.max_symbols > 0:
        symbols = symbols[: args.max_symbols]

    _log.info(
        "archive_enrich_derived years=%s chunk=%s symbols=%s",
        years,
        args.chunk,
        len(symbols),
    )

    report = enrich_all_derived(
        base,
        years=years,
        symbols=symbols,
        chunk_id=args.chunk,
        chunk_bounds_path=chunk_config_path(base) if args.chunk is not None else None,
    )

    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    chunk_tag = f"_c{args.chunk}" if args.chunk is not None else ""
    report_path = reports_dir / f"enrich_derived_report{chunk_tag}_{date_tag}.json"
    report_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    _print_summary(report)
    print(f"report: {report_path}")
    _log.info(
        "enrich_derived done enriched=%s skipped=%s failed=%s",
        report.enriched,
        report.skipped,
        report.failed,
    )
    if report.failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
