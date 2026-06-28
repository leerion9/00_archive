"""
Step C: enrich market_cap sidecar via pykrx (chunk 0 test = 50 symbols).

  python -m scripts.archive_enrich_market_cap --chunk 0
  python -m scripts.archive_enrich_market_cap --chunk 1 --years 2025
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime

from config.settings import settings
from core.archive_merge import load_collection_plan_years
from core.chunk_bounds import enrich_chunk_config_path
from core.enrich_market_cap import build_mcap_tasks, ensure_enrich_chunk_config, run_mcap_enrich
from core.throttle import RequestThrottler

_log = logging.getLogger("archive")


def _configure_logging(chunk_id: int | None) -> None:
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    chunk_tag = f"_c{chunk_id}" if chunk_id is not None else ""
    log_file = log_dir / f"archive_enrich_market_cap{chunk_tag}_{date_tag}.log"

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
    print("\n=== enrich_market_cap summary ===")
    print(
        f"chunk={report.chunk_id} years={report.years} tasks={report.tasks_total} "
        f"done={report.done} failed={report.failed} skipped={report.skipped} "
        f"skipped_expected={report.skipped_expected} expected_blank={report.expected_blank}"
    )
    if report.methods:
        print(f"methods={report.methods}")
    failed = [r for r in report.results if r.status == "failed"]
    if failed:
        print(f"failed sample ({min(10, len(failed))}):")
        for r in failed[:10]:
            print(f"  {r.task_id}: {r.error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich market_cap via pykrx (chunked)")
    parser.add_argument("--chunk", type=int, required=True, help="Enrich chunk id (0=test, 1-8=prod)")
    parser.add_argument("--years", type=int, nargs="+", help="Years (default: collection_plan.json)")
    parser.add_argument("--symbols", nargs="+", help="Optional symbol override")
    parser.add_argument("--clear-failures", action="store_true", help="Truncate enrich_mcap_failures.jsonl before run")
    args = parser.parse_args()

    _configure_logging(args.chunk)
    base = settings.base_dir
    if args.clear_failures:
        fail_path = base / "manifest" / "enrich_mcap_failures.jsonl"
        if fail_path.exists():
            fail_path.write_text("", encoding="utf-8")
            _log.info("cleared %s", fail_path)
    chunks = ensure_enrich_chunk_config(base)
    chunk_rows = [c for c in chunks if int(c["chunk_id"]) == int(args.chunk)]
    if not chunk_rows:
        raise SystemExit(f"unknown enrich chunk id: {args.chunk}")

    years = sorted({int(y) for y in args.years}, reverse=True) if args.years else load_collection_plan_years(base)
    bounds = enrich_chunk_config_path(base)
    tasks = build_mcap_tasks(
        base,
        years=years,
        chunk_id=args.chunk,
        chunk_bounds_path=bounds,
        symbols=args.symbols,
    )
    if not tasks:
        raise SystemExit(f"no tasks for chunk={args.chunk}")

    if settings.krx_id and settings.krx_pw:
        _log.info("KRX credentials configured")
    else:
        _log.warning("KRX_ID/KRX_PW not set - pykrx calls may fail; failures logged to enrich_mcap_failures.jsonl")

    _log.info(
        "archive_enrich_market_cap chunk=%s role=%s symbols~=%s tasks=%s pending=%s skipped_expected=%s years=%s",
        args.chunk,
        chunk_rows[0].get("role"),
        chunk_rows[0].get("count"),
        len(tasks),
        sum(1 for t in tasks if t.get("status") == "pending"),
        sum(1 for t in tasks if t.get("status") == "skipped_expected"),
        years,
    )

    throttler = RequestThrottler(
        delay_sec=settings.delay_sec,
        jitter_sec=settings.jitter_sec,
        batch_size=settings.batch_size,
        batch_pause_sec=settings.batch_pause_sec,
    )

    report = run_mcap_enrich(
        base,
        tasks,
        chunk_id=args.chunk,
        krx_id=settings.krx_id,
        krx_pw=settings.krx_pw,
        throttler=throttler,
    )

    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    report_path = reports_dir / f"enrich_market_cap_c{args.chunk}_{date_tag}.json"
    report_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    _print_summary(report)
    print(f"report: {report_path}")
    _log.info("enrich_market_cap done done=%s failed=%s", report.done, report.failed)
    if report.failed and report.done == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
