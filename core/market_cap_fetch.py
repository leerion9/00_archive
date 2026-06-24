"""Fetch market cap / NAV via pykrx with Naver snapshot fallback."""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

_log = logging.getLogger("archive")

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}
_ITEM_COINO_URL = "https://finance.naver.com/item/coinfo.naver"


def ensure_krx_env(krx_id: str, krx_pw: str) -> None:
    if krx_id and krx_pw:
        os.environ.setdefault("KRX_ID", krx_id)
        os.environ.setdefault("KRX_PW", krx_pw)


def is_etf_like(name: str) -> bool:
    text = str(name or "").upper()
    keys = ("ETF", "ETN", "KODEX", "TIGER", "KOACT", "PLUS ", "ACE ", "ARIRANG", "SOL ")
    return any(k.strip() in text for k in keys if k.strip())


def fetch_pykrx_market_cap(symbol: str, fromdate: str, todate: str) -> pd.DataFrame:
    from pykrx import stock

    df = stock.get_market_cap_by_date(fromdate, todate, str(symbol).strip())
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    out = df.reset_index()
    date_col = out.columns[0]
    out = out.rename(columns={date_col: "date"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y%m%d")

    cap_col = next((c for c in out.columns if "cap" in str(c).lower() or "시가" in str(c)), None)
    shares_col = next((c for c in out.columns if "shrs" in str(c).lower() or "주식" in str(c)), None)
    if cap_col is None:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    result = pd.DataFrame(
        {
            "date": out["date"].astype(str),
            "market_cap": pd.to_numeric(out[cap_col], errors="coerce"),
            "shares_outstanding": pd.to_numeric(out[shares_col], errors="coerce")
            if shares_col
            else pd.NA,
        }
    )
    return result.dropna(subset=["market_cap"]).reset_index(drop=True)


def fetch_pykrx_etf_nav(symbol: str, fromdate: str, todate: str) -> pd.DataFrame:
    from pykrx import stock

    df = stock.get_etf_ohlcv_by_date(fromdate, todate, str(symbol).strip())
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "market_cap"])

    out = df.reset_index()
    date_col = out.columns[0]
    out = out.rename(columns={date_col: "date"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y%m%d")

    nav_col = None
    for col in out.columns:
        low = str(col).lower()
        if "nav" in low or "순자산" in str(col):
            nav_col = col
            break
    if nav_col is None and len(out.columns) > 5:
        nav_col = out.columns[5]

    if nav_col is None:
        return pd.DataFrame(columns=["date", "market_cap"])

    result = pd.DataFrame(
        {
            "date": out["date"].astype(str),
            "market_cap": pd.to_numeric(out[nav_col], errors="coerce"),
        }
    )
    return result.dropna(subset=["market_cap"]).reset_index(drop=True)


def fetch_naver_listed_shares(symbol: str, session: Optional[requests.Session] = None) -> Optional[int]:
    """Parse 상장주식수 from Naver item coinfo (snapshot)."""
    own_session = session is None
    if own_session:
        sess = requests.Session()
        sess.headers.update(_UA)
    else:
        sess = session  # type: ignore[assignment]
    try:
        resp = sess.get(_ITEM_COINO_URL, params={"code": str(symbol).strip()}, timeout=20)
        resp.encoding = "euc-kr"
        resp.raise_for_status()
        m = re.search(r"상장주식수[\s\S]{0,120}?<em>\s*([\d,]+)\s*</em>", resp.text)
        if m:
            return int(m.group(1).replace(",", ""))
        soup = BeautifulSoup(resp.text, "html.parser")
        for th in soup.select("th"):
            if "상장주식수" not in th.get_text(strip=True):
                continue
            td = th.find_next("td")
            if not td:
                continue
            em = td.select_one("em")
            text = (em or td).get_text(strip=True)
            m2 = re.search(r"([\d,]+)", text)
            if m2:
                return int(m2.group(1).replace(",", ""))
    except Exception as exc:
        _log.warning("naver shares fetch failed %s: %s", symbol, exc)
    return None


def build_shares_x_close_frame(bars: list[dict], shares: int) -> pd.DataFrame:
    rows = []
    for bar in bars:
        date_key = str(bar.get("date", "")).strip()
        if not date_key:
            continue
        close = int(bar.get("close", 0) or 0)
        rows.append(
            {
                "date": date_key,
                "market_cap": close * int(shares),
                "shares_outstanding": int(shares),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])
    return pd.DataFrame(rows)


def fetch_market_cap_for_year(
    symbol: str,
    year: int,
    bars: list[dict],
    *,
    name: str = "",
    krx_id: str = "",
    krx_pw: str = "",
    naver_shares_cache: dict[str, int],
    session: Optional[requests.Session] = None,
) -> tuple[pd.DataFrame, str]:
    """Return (dataframe[date, market_cap, shares_outstanding], method)."""
    year_bars = [b for b in bars if str(b.get("date", "")).startswith(str(int(year)))]
    if not year_bars:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]), "empty"

    dates = sorted(str(b["date"]) for b in year_bars if b.get("date"))
    fromdate, todate = dates[0], dates[-1]
    sym = str(symbol).strip()

    ensure_krx_env(krx_id, krx_pw)

    if is_etf_like(name):
        etf_df = fetch_pykrx_etf_nav(sym, fromdate, todate)
        if not etf_df.empty:
            etf_df["shares_outstanding"] = pd.NA
            return etf_df, "etf_nav"

    cap_df = fetch_pykrx_market_cap(sym, fromdate, todate)
    if not cap_df.empty:
        return cap_df, "pykrx_mcap"

    if sym not in naver_shares_cache:
        shares = fetch_naver_listed_shares(sym, session=session)
        if shares:
            naver_shares_cache[sym] = shares

    shares = naver_shares_cache.get(sym)
    if shares:
        fb = build_shares_x_close_frame(year_bars, shares)
        return fb, "shares_x_close"

    return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]), "failed"
