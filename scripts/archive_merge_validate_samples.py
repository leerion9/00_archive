"""
Validate merged output against raw chunks for a 10-symbol sample panel.

  python -m scripts.archive_merge_validate_samples
  python -m scripts.archive_merge_validate_samples --symbols 005930 000020

Operational rule: after merge/enrich steps, always run this default 10-symbol panel.
"""

from __future__ import annotations

import argparse
import sys

from config.settings import settings
from core.merge_validate import DEFAULT_SAMPLE_SYMBOLS, validate_sample_symbols


def _print_results(results, *, title: str = "merge sample validation", verbose: bool = True) -> int:
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed

    print(f"\n=== {title} ({len(results)} symbols) ===")
    show_all = verbose and len(results) <= 20
    for r in results:
        if r.ok and not show_all:
            continue
        status = "PASS" if r.ok else "FAIL"
        label = f"{r.symbol} {r.name}".strip()
        print(
            f"[{status}] {label}  bars={r.bar_count}  "
            f"years={len(r.years_complete)}/{len(r.years_complete) + len(r.years_pending)}  "
            f"range={r.date_range.get('from')}..{r.date_range.get('to')}"
        )
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
            label = f"{r.symbol} {r.name}".strip()
            print(
                f"[FAIL] {label}  bars={r.bar_count}  "
                f"years={len(r.years_complete)}/{len(r.years_complete) + len(r.years_pending)}"
            )
            for c in r.failures():
                print(f"       x {c.name}: {c.detail}")
            shown += 1

    print(f"\nresult: {passed}/{len(results)} passed")
    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate merged/{symbol}.json against raw (default 10-symbol panel)"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help=f"Symbols to validate (default: {', '.join(DEFAULT_SAMPLE_SYMBOLS)})",
    )
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
    if len(symbols) != 10 and not args.symbols and not args.all:
        print(f"warning: default panel has {len(symbols)} symbols", file=sys.stderr)

    results = validate_sample_symbols(settings.base_dir, symbols)
    title = "merge validation (all symbols)" if args.all else "merge sample validation"
    raise SystemExit(_print_results(results, title=title, verbose=not args.all))


if __name__ == "__main__":
    main()
