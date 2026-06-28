"""
Step G spot check — post-delisting bars/mcap should be empty (data = anomaly).

  python -m scripts.verify_post_delist_spot
  python -m scripts.verify_post_delist_spot --sample-size 20
  python -m scripts.verify_post_delist_spot --symbols 036490 123456
  python -m scripts.verify_post_delist_spot --all-delisted
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from config.settings import settings
from core.listing_events import delisted_master_path
from core.post_delist_verify import (
    load_delisted_spot_candidates,
    pick_spot_sample,
    run_post_delist_spot_check,
)


def _print_report(report, *, verbose: bool) -> int:
    print(f"\n=== post-delist spot check ({report.sample_size} symbols) ===")
    for check in report.checks:
        if check.ok and not verbose:
            continue
        label = f"{check.symbol} {check.name}".strip()
        if check.status == "ok":
            print(f"[OK] {label}  delist={check.delisting_date}  post_bars=0 post_mcap=0")
        elif check.status == "anomaly_post_delist":
            print(
                f"[ANOMALY] {label}  delist={check.delisting_date}  "
                f"post_bars={check.post_delist_bars} post_mcap={check.post_delist_mcap_rows}"
            )
            if check.post_delist_bar_dates:
                print(f"         bar_dates={check.post_delist_bar_dates}")
            if check.post_delist_mcap_dates:
                print(f"         mcap_dates={check.post_delist_mcap_dates}")
        else:
            print(f"[SKIP] {label}  {check.detail}")

    if not verbose and report.anomaly == 0 and report.skipped == 0:
        print(f"... {report.ok} ok (use --verbose to list all)")

    print(
        f"\nresult: ok={report.ok} anomaly={report.anomaly} skipped={report.skipped} "
        f"total={report.sample_size}"
    )
    return 1 if report.anomaly else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Spot-check post-delisting OHLCV/mcap anomalies")
    parser.add_argument("--symbols", nargs="+", help="Explicit symbols to check")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=15,
        help="Default sample count from delisted master (default: 15)",
    )
    parser.add_argument(
        "--all-delisted",
        action="store_true",
        help="Check all delisted symbols in master (190)",
    )
    parser.add_argument("--verbose", action="store_true", help="Print every symbol result")
    parser.add_argument(
        "--report",
        type=Path,
        help="Write JSON report path (default: reports/post_delist_spot_YYYYMMDD.json)",
    )
    args = parser.parse_args()

    base = settings.base_dir
    master = delisted_master_path(base)
    candidates = load_delisted_spot_candidates(base, master)
    if not candidates:
        raise SystemExit(f"no delisted master at {master}; run archive_listing_events --g0 first")

    if args.symbols:
        symbols = [str(s).strip().zfill(6) for s in args.symbols]
    elif args.all_delisted:
        symbols = [c["symbol"] for c in candidates]
    else:
        all_syms = [c["symbol"] for c in candidates]
        symbols = pick_spot_sample(all_syms, int(args.sample_size))

    names = {c["symbol"]: str(c.get("name") or "") for c in candidates}
    delisting_dates = {
        c["symbol"]: str(c.get("delisting_date") or "") for c in candidates if c.get("delisting_date")
    }

    report = run_post_delist_spot_check(
        base,
        symbols,
        names=names,
        delisting_dates=delisting_dates,
    )

    date_tag = datetime.now().strftime("%Y%m%d")
    report_path = args.report or (base / "reports" / f"post_delist_spot_{date_tag}.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {report_path}")

    raise SystemExit(_print_report(report, verbose=args.verbose or len(symbols) <= 20))


if __name__ == "__main__":
    main()
