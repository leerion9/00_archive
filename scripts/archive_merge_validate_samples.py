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


def _print_results(results) -> int:
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed

    print("\n=== merge sample validation (10 symbols) ===")
    for r in results:
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
    args = parser.parse_args()

    symbols = args.symbols if args.symbols else list(DEFAULT_SAMPLE_SYMBOLS)
    if len(symbols) != 10 and not args.symbols:
        print(f"warning: default panel has {len(symbols)} symbols", file=sys.stderr)

    results = validate_sample_symbols(settings.base_dir, symbols)
    raise SystemExit(_print_results(results))


if __name__ == "__main__":
    main()
