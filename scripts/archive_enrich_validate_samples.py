"""
Validate Step B derived features for the default 10-symbol panel.

  python -m scripts.archive_enrich_validate_samples
"""

from __future__ import annotations

import argparse
import sys

from config.settings import settings
from core.enrich_validate import validate_derived_samples
from core.merge_validate import DEFAULT_SAMPLE_SYMBOLS


def _print_results(results) -> int:
    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed

    print("\n=== enrich_derived sample validation (10 symbols) ===")
    for r in results:
        status = "PASS" if r.ok else "FAIL"
        print(f"[{status}] {r.symbol}  rows={r.row_count}")
        if not r.ok:
            for c in r.failures():
                print(f"       x {c.name}: {c.detail}")

    print(f"\nresult: {passed}/{len(results)} passed")
    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate derived features parquet (10-symbol panel)")
    parser.add_argument("--symbols", nargs="+", help="Override sample symbols")
    args = parser.parse_args()

    symbols = args.symbols if args.symbols else list(DEFAULT_SAMPLE_SYMBOLS)
    results = validate_derived_samples(settings.base_dir, symbols)
    raise SystemExit(_print_results(results))


if __name__ == "__main__":
    main()
