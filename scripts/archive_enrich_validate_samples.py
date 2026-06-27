"""
Validate Step B derived features for the default 10-symbol panel.

  python -m scripts.archive_enrich_validate_samples
  python -m scripts.archive_enrich_validate_samples --all
"""

from __future__ import annotations

import argparse
import sys

from config.settings import settings
from core.enrich_validate import validate_derived_samples
from core.merge_validate import DEFAULT_SAMPLE_SYMBOLS


def _print_results(results, *, title: str = "enrich_derived sample validation", verbose: bool = True) -> int:
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed

    print(f"\n=== {title} ({len(results)} symbols) ===")
    show_all = verbose and len(results) <= 20
    for r in results:
        if r.ok and not show_all:
            continue
        status = "PASS" if r.ok else "FAIL"
        print(f"[{status}] {r.symbol}  rows={r.row_count}")
        if not r.ok:
            for c in r.failures():
                print(f"       x {c.name}: {c.detail}")

    if not show_all and failed:
        print(f"... {failed} failed (showing failures only)")
        shown = 0
        for r in results:
            if r.ok:
                continue
            if shown >= 30:
                print(f"... and {failed - shown} more failures")
                break
            status = "FAIL"
            print(f"[{status}] {r.symbol}  rows={r.row_count}")
            for c in r.failures():
                print(f"       x {c.name}: {c.detail}")
            shown += 1

    print(f"\nresult: {passed}/{len(results)} passed")
    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate derived features parquet (10-symbol panel)")
    parser.add_argument("--symbols", nargs="+", help="Override sample symbols")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all merged symbols (Step D option C)",
    )
    args = parser.parse_args()

    if args.all:
        from core.enrich_derived import list_merged_symbols

        symbols = list_merged_symbols(settings.base_dir)
        print(f"validating {len(symbols)} merged symbols...")
    else:
        symbols = args.symbols if args.symbols else list(DEFAULT_SAMPLE_SYMBOLS)

    results = validate_derived_samples(settings.base_dir, symbols)
    title = "enrich_derived validation (all symbols)" if args.all else "enrich_derived sample validation"
    raise SystemExit(_print_results(results, title=title, verbose=not args.all))


if __name__ == "__main__":
    main()
