"""
Phase 0: cross-validate Naver sise_day close vs pykrx adjusted close.

  python -m scripts.archive_validate_adjusted
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone

import pandas as pd
from pykrx import stock

from config.settings import settings
from core.naver_daily import fetch_pages_for_year
from core.naver_symbol_master import load_symbol_master
from core.throttle import RequestThrottler

_log = logging.getLogger("archive")

DEFAULT_SYMBOLS = (
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
    "051910",  # LG화학
    "006400",  # 삼성SDI
    "035720",  # 카카오
    "105560",  # KB금융
    "028260",  # 삼성물산
    "012330",  # HD현대모비스
    "066570",  # LG전자
)


def _end_date_for_year(year: int) -> str:
    cap = str(settings.end_date or "").strip()
    if cap.startswith(str(year)):
        return cap
    return f"{year}1231"


def _year_start_for_compare(year: int) -> str:
    return f"{year}0101"


def fetch_naver_bars(symbol: str, year: int, throttler: RequestThrottler) -> list[dict]:
    result = fetch_pages_for_year(
        symbol,
        year,
        end_date=settings.end_date,
        on_page=lambda _page: throttler.after_request(),
    )
    if result is None:
        return []
    return result.bars


def fetch_pykrx_closes(symbol: str, from_ymd: str, to_ymd: str) -> pd.Series:
    df = stock.get_market_ohlcv_by_date(from_ymd, to_ymd, symbol, adjusted=True)
    if df is None or df.empty:
        return pd.Series(dtype=float)
    idx = pd.to_datetime(df.index)
    closes = df["종가"].astype(float)
    closes.index = idx.strftime("%Y%m%d")
    return closes


def compare_symbol(symbol: str, name: str, year: int, throttler: RequestThrottler) -> dict:
    from_ymd = _year_start_for_compare(year)
    to_ymd = _end_date_for_year(year)

    naver_bars = fetch_naver_bars(symbol, year, throttler)
    naver_by_date = {str(b["date"]): int(b["close"]) for b in naver_bars}

    pykrx = fetch_pykrx_closes(symbol, from_ymd, to_ymd)
    common_dates = sorted(set(naver_by_date.keys()) & set(pykrx.index.astype(str)))
    diffs: list[dict] = []
    for d in common_dates:
        n_close = naver_by_date[d]
        p_close = int(round(float(pykrx.loc[d])))
        if n_close != p_close:
            diffs.append(
                {
                    "date": d,
                    "naver_close": n_close,
                    "pykrx_close": p_close,
                    "diff": n_close - p_close,
                }
            )

    return {
        "symbol": symbol,
        "name": name,
        "year": year,
        "from": from_ymd,
        "to": to_ymd,
        "naver_bar_count": len(naver_bars),
        "pykrx_bar_count": int(len(pykrx)),
        "common_dates": len(common_dates),
        "mismatch_count": len(diffs),
        "mismatches": diffs[:20],
        "passed": len(diffs) == 0 and len(common_dates) > 0,
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parser = argparse.ArgumentParser(description="Naver vs pykrx adjusted close validation")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args()

    master = load_symbol_master(settings.symbol_master_path)
    throttler = RequestThrottler(
        delay_sec=settings.delay_sec,
        jitter_sec=settings.jitter_sec,
        batch_size=settings.batch_size,
        batch_pause_sec=settings.batch_pause_sec,
    )

    results: list[dict] = []
    for symbol in args.symbols:
        name = master.get(symbol, symbol)
        _log.info("validate %s %s year=%s", symbol, name, args.year)
        results.append(compare_symbol(symbol, name, args.year, throttler))

    passed = sum(1 for r in results if r["passed"])
    report = {
        "schema_version": 1,
        "validated_at_iso": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "year": args.year,
        "end_date_cap": settings.end_date,
        "price_basis_expected": "adjusted",
        "summary": {
            "symbols": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "all_passed": passed == len(results),
        },
        "results": results,
    }

    report_path = settings.base_dir / "reports" / f"validate_adjusted_{args.year}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Naver vs pykrx adjusted close ===")
    print(f"year={args.year}  end_cap={settings.end_date}")
    for row in results:
        status = "PASS" if row["passed"] else "FAIL"
        print(
            f"  [{status}] {row['symbol']} {row['name']}: "
            f"common={row['common_dates']} mismatch={row['mismatch_count']}"
        )
        for mm in row["mismatches"][:3]:
            print(f"         {mm['date']} naver={mm['naver_close']} pykrx={mm['pykrx_close']}")
    print(f"\npassed {passed}/{len(results)}")
    print(f"report: {report_path}")

    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
