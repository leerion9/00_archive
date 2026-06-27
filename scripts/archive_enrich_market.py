"""
Step F: enrich daily market sidecar (KOSPI/KOSDAQ point-in-time).

  python -m scripts.archive_enrich_market
  python -m scripts.archive_enrich_market --years 2020 2021 2022 2023 2024 2025 2026
  python -m scripts.archive_enrich_market --chunk 0
  python -m scripts.archive_enrich_market --symbols 005930 035720 --years 2026
  python -m scripts.archive_enrich_market --etf-patch
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime

from config.settings import settings
from core.archive_merge import load_collection_plan_years
from core.enrich_market import enrich_all_market, list_merged_symbols, patch_etf_etn_market
from core.shard import chunk_config_path

_log = logging.getLogger("archive")


def _configure_logging(chunk_id: int | None) -> None:
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    chunk_tag = f"_c{chunk_id}" if chunk_id is not None else ""
    log_file = log_dir / f"archive_enrich_market{chunk_tag}_{date_tag}.log"

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
    print("\n=== enrich_market summary ===")
    print(
        f"years={report.years} dates={report.dates_total} symbols_total={report.symbols_total} "
        f"enriched={report.enriched} skipped={report.skipped} failed={report.failed} "
        f"unknown_rows={report.unknown_rows}"
    )
    if report.cache_stats:
        print(f"cache={report.cache_stats}")
    failed = [r for r in report.results if r.error and not r.skipped]
    if failed:
        print(f"failed ({len(failed)}):")
        for r in failed[:10]:
            print(f"  {r.symbol}: {r.error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich market sidecar (KOSPI/KOSDAQ) via pykrx")
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Years for trading calendar and feature rows (default: collection_plan.json)",
    )
    parser.add_argument("--symbols", nargs="+", help="Only these symbols")
    parser.add_argument("--chunk", type=int, help="Symbol chunk id (0..3)")
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=0,
        help="Max symbols to process (0 = all in scope)",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Re-fetch master/market_daily even if cache exists",
    )
    parser.add_argument(
        "--clear-failures",
        action="store_true",
        help="Truncate enrich_market_failures.jsonl before run",
    )
    parser.add_argument(
        "--etf-patch",
        action="store_true",
        help="Set market=etf외 for ETF/ETN symbols only (no KOSPI/KOSDAQ cache fetch)",
    )
    args = parser.parse_args()

    _configure_logging(args.chunk)
    base = settings.base_dir
    if args.clear_failures:
        fail_path = base / "manifest" / "enrich_market_failures.jsonl"
        if fail_path.exists():
            fail_path.write_text("", encoding="utf-8")
            _log.info("cleared %s", fail_path)

    if args.etf_patch:
        _log.info("archive_enrich_market etf-patch mode")
        report = patch_etf_etn_market(base)
        reports_dir = base / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        date_tag = datetime.now().strftime("%Y%m%d")
        report_path = reports_dir / f"enrich_market_etf_patch_{date_tag}.json"
        report_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        _print_summary(report)
        print(f"report: {report_path}")
        _log.info("etf-patch done enriched=%s failed=%s", report.enriched, report.failed)
        if report.failed and report.enriched == 0:
            raise SystemExit(1)
        return

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

    if settings.krx_id and settings.krx_pw:
        _log.info("KRX credentials configured")
    else:
        _log.warning("KRX_ID/KRX_PW not set - pykrx calls may fail")

    _log.info(
        "archive_enrich_market years=%s chunk=%s symbols=%s refresh_cache=%s",
        years,
        args.chunk,
        len(symbols),
        args.refresh_cache,
    )

    from core.throttle import RequestThrottler

    throttler = RequestThrottler(
        delay_sec=settings.delay_sec,
        jitter_sec=settings.jitter_sec,
        batch_size=settings.batch_size,
        batch_pause_sec=settings.batch_pause_sec,
    )

    report = enrich_all_market(
        base,
        years=years,
        symbols=symbols,
        krx_id=settings.krx_id,
        krx_pw=settings.krx_pw,
        throttler=throttler,
        refresh_cache=args.refresh_cache,
    )

    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    chunk_tag = f"_c{args.chunk}" if args.chunk is not None else ""
    report_path = reports_dir / f"enrich_market{chunk_tag}_{date_tag}.json"
    report_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    _print_summary(report)
    print(f"report: {report_path}")
    _log.info(
        "enrich_market done enriched=%s skipped=%s failed=%s unknown_rows=%s",
        report.enriched,
        report.skipped,
        report.failed,
        report.unknown_rows,
    )
    if report.failed and report.enriched == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
