"""
Step G g3 — delisted 190종 merge + derived + market_cap + market.

  python -m scripts.archive_g3_delisted
  python -m scripts.archive_g3_delisted --chunk 0   # market_cap only (chunk 0~3)
  python -m scripts.archive_g3_delisted --skip-mcap # merge + derived + market only
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from config.settings import settings
from core.archive_merge import load_collection_plan_years, merge_all, merged_path
from core.chunk_bounds import assign_chunk, load_chunk_config
from core.enrich_derived import enrich_all_derived
from core.enrich_market import enrich_all_market
from core.enrich_market_cap import build_mcap_tasks, run_mcap_enrich
from core.listing_events import delisted_master_path, load_delisted_master
from core.throttle import RequestThrottler

_log = logging.getLogger("archive")
G3_YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]


def _configure_logging(tag: str = "") -> None:
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    suffix = f"_{tag}" if tag else ""
    log_file = log_dir / f"archive_g3_delisted{suffix}_{date_tag}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )


def load_delisted_symbols(base_dir: Path) -> list[str]:
    records = load_delisted_master(delisted_master_path(base_dir))
    if not records:
        raise SystemExit(f"no delisted master at {delisted_master_path(base_dir)}; run g0 first")
    return sorted({str(r["symbol"]).strip().zfill(6) for r in records})


def merged_delisted_symbols(base_dir: Path, symbols: list[str]) -> list[str]:
    out: list[str] = []
    for sym in symbols:
        path = merged_path(base_dir, sym)
        if path.exists():
            out.append(sym)
    return out


def delisted_chunk_config_path(base_dir: Path) -> Path:
    return base_dir / "config" / "chunks_delisted.json"


def run_merge(base_dir: Path, symbols: list[str], years: list[int]) -> dict:
    report = merge_all(base_dir, years_planned=years, symbols=symbols)
    payload = report.to_dict()
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    path = reports_dir / f"merge_report_g3_{date_tag}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== g3 merge ===")
    print(f"merged={report.merged} skipped_no_raw={report.skipped_no_raw} warnings={len(report.warnings)}")
    print(f"report: {path}")
    return payload


def run_derived(base_dir: Path, symbols: list[str], years: list[int]) -> dict:
    report = enrich_all_derived(base_dir, years=years, symbols=symbols)
    payload = report.to_dict()
    date_tag = datetime.now().strftime("%Y%m%d")
    path = base_dir / "reports" / f"enrich_derived_g3_{date_tag}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== g3 derived ===")
    print(f"enriched={report.enriched} skipped={report.skipped} failed={report.failed}")
    print(f"report: {path}")
    if report.failed:
        raise SystemExit(1)
    return payload


def run_mcap_chunk(base_dir: Path, symbols: list[str], years: list[int], chunk_id: int) -> dict:
    bounds = delisted_chunk_config_path(base_dir)
    cfg = load_chunk_config(bounds)
    if not cfg:
        raise SystemExit(f"missing chunk config: {bounds}")
    chunk_syms = [s for s in symbols if assign_chunk(s, chunk_id, bounds)]
    tasks = build_mcap_tasks(
        base_dir,
        years=years,
        chunk_id=chunk_id,
        chunk_bounds_path=bounds,
        symbols=chunk_syms,
    )
    if not tasks:
        print(f"\n=== g3 market_cap chunk {chunk_id} === no tasks")
        return {"chunk_id": chunk_id, "tasks": 0}

    throttler = RequestThrottler(
        delay_sec=settings.delay_sec,
        jitter_sec=settings.jitter_sec,
        batch_size=settings.batch_size,
        batch_pause_sec=settings.batch_pause_sec,
    )
    report = run_mcap_enrich(
        base_dir,
        tasks,
        chunk_id=chunk_id,
        krx_id=settings.krx_id,
        krx_pw=settings.krx_pw,
        throttler=throttler,
    )
    payload = report.to_dict()
    date_tag = datetime.now().strftime("%Y%m%d")
    path = base_dir / "reports" / f"enrich_market_cap_g3_c{chunk_id}_{date_tag}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== g3 market_cap chunk {chunk_id} ===")
    print(
        f"tasks={report.tasks_total} done={report.done} failed={report.failed} "
        f"skipped_expected={report.skipped_expected} expected_blank={report.expected_blank} "
        f"methods={report.methods}"
    )
    print(f"report: {path}")
    return payload


def run_market(base_dir: Path, symbols: list[str], years: list[int]) -> dict:
    throttler = RequestThrottler(
        delay_sec=settings.delay_sec,
        jitter_sec=settings.jitter_sec,
        batch_size=settings.batch_size,
        batch_pause_sec=settings.batch_pause_sec,
    )
    report = enrich_all_market(
        base_dir,
        years=years,
        symbols=symbols,
        krx_id=settings.krx_id,
        krx_pw=settings.krx_pw,
        throttler=throttler,
        refresh_cache=False,
    )
    payload = report.to_dict()
    date_tag = datetime.now().strftime("%Y%m%d")
    path = base_dir / "reports" / f"enrich_market_g3_{date_tag}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== g3 market ===")
    print(
        f"enriched={report.enriched} skipped={report.skipped} failed={report.failed} "
        f"unknown_rows={report.unknown_rows}"
    )
    print(f"report: {path}")
    if report.failed and report.enriched == 0:
        raise SystemExit(1)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Step G g3 — delisted merge + enrich")
    parser.add_argument("--years", type=int, nargs="+", help="Years (default 2020..2026)")
    parser.add_argument("--chunk", type=int, help="market_cap chunk only (0..3)")
    parser.add_argument("--skip-merge", action="store_true")
    parser.add_argument("--skip-derived", action="store_true")
    parser.add_argument("--skip-mcap", action="store_true")
    parser.add_argument("--skip-market", action="store_true")
    args = parser.parse_args()

    _configure_logging(f"c{args.chunk}" if args.chunk is not None else "all")
    base = settings.base_dir
    years = sorted({int(y) for y in args.years}, reverse=True) if args.years else G3_YEARS
    if not years:
        years = load_collection_plan_years(base) or G3_YEARS

    symbols = load_delisted_symbols(base)
    _log.info("g3 delisted symbols=%s years=%s", len(symbols), years)

    mcap_only = args.chunk is not None
    if not mcap_only and not args.skip_merge:
        run_merge(base, symbols, years)

    merged = merged_delisted_symbols(base, symbols)
    _log.info("g3 merged symbols=%s", len(merged))
    if not merged:
        raise SystemExit("no merged delisted symbols; run merge first")

    if mcap_only:
        run_mcap_chunk(base, merged, years, int(args.chunk))
        return

    if not args.skip_derived:
        run_derived(base, merged, years)

    if not args.skip_mcap:
        for cid in range(4):
            run_mcap_chunk(base, merged, years, cid)

    if not args.skip_market:
        run_market(base, merged, years)

    print("\n=== g3 complete ===")


if __name__ == "__main__":
    main()
