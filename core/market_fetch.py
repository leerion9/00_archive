"""Fetch daily KOSPI/KOSDAQ membership via pykrx (Step F)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from core.archive_schema import utc_now_iso
from core.market_cap_fetch import ensure_krx_env, refresh_krx_session
from core.throttle import RequestThrottler

_log = logging.getLogger("archive")

MARKET_DAILY_DIR = "master/market_daily"
KOSPI_INDEX = "1001"


def market_daily_path(base_dir: Path, date: str) -> Path:
    return base_dir / MARKET_DAILY_DIR / f"{str(date).strip()}.json"


def membership_lists_to_map(kospi: Sequence[str], kosdaq: Sequence[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    overlap: Set[str] = set()
    for sym in kospi:
        code = str(sym).strip()
        if code:
            out[code] = "KOSPI"
    for sym in kosdaq:
        code = str(sym).strip()
        if not code:
            continue
        if code in out:
            overlap.add(code)
            continue
        out[code] = "KOSDAQ"
    if overlap:
        _log.warning("market membership overlap (prefer KOSPI): %s", sorted(overlap)[:5])
    return out


def fetch_market_lists_for_date(date: str) -> tuple[List[str], List[str]]:
    from pykrx import stock

    date_key = str(date).strip()
    kospi = list(stock.get_market_ticker_list(date_key, market="KOSPI") or [])
    kosdaq = list(stock.get_market_ticker_list(date_key, market="KOSDAQ") or [])
    return kospi, kosdaq


def trading_dates_for_years(years: Sequence[int]) -> List[str]:
    from pykrx import stock

    dates: List[str] = []
    for year in sorted({int(y) for y in years}):
        fromdate = f"{year}0101"
        todate = f"{year}1231"
        df = stock.get_index_ohlcv_by_date(fromdate, todate, KOSPI_INDEX)
        if df is None or df.empty:
            continue
        for ts in df.index:
            dates.append(ts.strftime("%Y%m%d"))
    return sorted(set(dates))


def write_market_daily_cache(path: Path, date: str, kospi: Sequence[str], kosdaq: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "date": str(date).strip(),
        "fetched_at_iso": utc_now_iso(),
        "KOSPI": [str(s).strip() for s in kospi if str(s).strip()],
        "KOSDAQ": [str(s).strip() for s in kosdaq if str(s).strip()],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def read_market_daily_cache(path: Path) -> tuple[List[str], List[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    kospi = list(payload.get("KOSPI") or [])
    kosdaq = list(payload.get("KOSDAQ") or [])
    return kospi, kosdaq


def ensure_market_daily_cache(
    base_dir: Path,
    dates: Sequence[str],
    *,
    krx_id: str = "",
    krx_pw: str = "",
    throttler: Optional[RequestThrottler] = None,
    refresh: bool = False,
) -> Dict[str, int]:
    ensure_krx_env(krx_id, krx_pw)
    stats = {"cached": 0, "fetched": 0, "failed": 0}
    unique_dates = sorted({str(d).strip() for d in dates if str(d).strip()})

    for i, date_key in enumerate(unique_dates):
        if i > 0 and i % 500 == 0:
            refresh_krx_session(krx_id, krx_pw)

        cache_path = market_daily_path(base_dir, date_key)
        if cache_path.exists() and not refresh:
            stats["cached"] += 1
            continue

        try:
            kospi, kosdaq = fetch_market_lists_for_date(date_key)
            if throttler is not None:
                throttler.after_request()
                throttler.after_request()
            if not kospi and not kosdaq:
                stats["failed"] += 1
                _log.warning("empty market lists for date=%s", date_key)
                continue
            write_market_daily_cache(cache_path, date_key, kospi, kosdaq)
            stats["fetched"] += 1
        except Exception as exc:
            stats["failed"] += 1
            _log.warning("market fetch failed date=%s err=%s", date_key, exc)

    return stats


def load_market_membership_map(
    base_dir: Path,
    dates: Sequence[str],
) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for date_key in sorted({str(d).strip() for d in dates if str(d).strip()}):
        cache_path = market_daily_path(base_dir, date_key)
        if not cache_path.exists():
            continue
        kospi, kosdaq = read_market_daily_cache(cache_path)
        out[date_key] = membership_lists_to_map(kospi, kosdaq)
    return out
