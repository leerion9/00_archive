"""
Naver Finance sise_day daily bar fetch (adapted from moa core/naver_universe.py).

No moa/KIS dependencies. Returns plain OHLCV dicts with YYYYMMDD dates.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup

from core.bar_merge import normalize_date

_log = logging.getLogger("archive")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}
DAY_URL = "https://finance.naver.com/item/sise_day.naver"
FETCH_RETRIES = 4
RETRY_BACKOFF_SEC = (5.0, 15.0, 30.0, 60.0)


class FetchAborted(Exception):
    """Fetch stopped early (stale pages, page budget, etc.)."""


@dataclass(frozen=True)
class FetchResult:
    symbol: str
    bars: List[Dict]
    pages_fetched: List[int]
    aborted: bool = False
    abort_reason: str = ""


def parse_daily_bars_html(html: str) -> List[Dict]:
    """Parse Naver sise_day HTML into OHLCV dicts (date still dot format)."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.type2")
    if not table:
        return []
    bars: List[Dict] = []
    for tr in table.select("tr"):
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        d0 = tds[0].get_text(strip=True)
        if not re.match(r"\d{4}\.\d{2}\.\d{2}", d0):
            continue
        close_txt = tds[1].get_text(strip=True).replace(",", "")
        open_txt = tds[3].get_text(strip=True).replace(",", "")
        high_txt = tds[4].get_text(strip=True).replace(",", "")
        low_txt = tds[5].get_text(strip=True).replace(",", "")
        vol_txt = tds[6].get_text(strip=True).replace(",", "")
        if not all(
            x.isdigit()
            for x in (close_txt, open_txt, high_txt, low_txt, vol_txt)
        ):
            continue
        bars.append(
            {
                "date": normalize_date(d0),
                "open": int(open_txt),
                "high": int(high_txt),
                "low": int(low_txt),
                "close": int(close_txt),
                "volume": int(vol_txt),
            }
        )
    return bars


def fetch_daily_page(
    session: requests.Session,
    symbol: str,
    page: int,
    *,
    timeout: float = 15.0,
) -> List[Dict]:
    resp = session.get(DAY_URL, params={"code": symbol, "page": page}, timeout=timeout)
    resp.encoding = "euc-kr"
    resp.raise_for_status()
    return parse_daily_bars_html(resp.text)


def fetch_pages_for_year(
    symbol: str,
    year: int,
    *,
    session: Optional[requests.Session] = None,
    max_pages: int = 800,
    max_pages_per_task: int = 30,
    end_date: str = "",
    start_page: int = 1,
    on_page=None,
) -> Optional[FetchResult]:
    """
    Fetch Naver daily bars until bars are older than `year` or pages exhausted.

    start_page: resume pagination (page cursor cache).
    max_pages_per_task: hard cap on HTTP pages this call (stale-loop guard).
    on_page: optional callback(page: int) after each successful page (for throttle).
    """
    own = session is None
    s = session or requests.Session()
    if own:
        s.headers.update(UA)

    year_start = f"{int(year)}0101"
    year_end = f"{int(year)}1231"
    cap = str(end_date or "").strip()
    if cap and cap.startswith(str(year)):
        year_end = min(year_end, cap)

    collected: List[Dict] = []
    pages_done: List[int] = []
    seen_dates: Set[str] = set()
    abort_reason = ""

    page_budget = max(1, int(max_pages_per_task))

    for page in range(max(1, int(start_page)), max_pages + 1):
        if len(pages_done) >= page_budget:
            abort_reason = f"page_budget_exceeded:{page_budget}"
            _log.warning(
                "%s year=%s page budget %s reached at page=%s",
                symbol,
                year,
                page_budget,
                page,
            )
            break

        page_bars: Optional[List[Dict]] = None
        for attempt in range(FETCH_RETRIES):
            try:
                page_bars = fetch_daily_page(s, symbol, page)
                break
            except Exception as exc:
                backoff = RETRY_BACKOFF_SEC[min(attempt, len(RETRY_BACKOFF_SEC) - 1)]
                _log.warning(
                    "fetch fail %s page=%s attempt=%s: %s (sleep %.0fs)",
                    symbol,
                    page,
                    attempt + 1,
                    exc,
                    backoff,
                )
                if attempt + 1 >= FETCH_RETRIES:
                    page_bars = None
                else:
                    import time

                    time.sleep(backoff)
        if on_page is not None:
            on_page(page)
        if not page_bars:
            break
        pages_done.append(page)

        stop = False
        new_in_year = 0
        for bar in page_bars:
            d = str(bar.get("date", ""))
            if d < year_start:
                stop = True
                break
            if not (year_start <= d <= year_end):
                continue
            if d in seen_dates:
                continue
            seen_dates.add(d)
            collected.append(bar)
            new_in_year += 1
        if stop:
            break
        if new_in_year == 0:
            abort_reason = f"stale_page:{page}"
            _log.warning(
                "%s year=%s stale page %s (no new dates); stopping",
                symbol,
                year,
                page,
            )
            break

    if not collected and not pages_done:
        return None
    return FetchResult(
        symbol=symbol,
        bars=collected,
        pages_fetched=pages_done,
        aborted=bool(abort_reason),
        abort_reason=abort_reason,
    )
