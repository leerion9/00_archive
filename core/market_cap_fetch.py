"""Fetch market cap via pykrx (stocks) or NAV x listed units AUM (ETF/ETN)."""

from __future__ import annotations

import logging
import os
from typing import Optional, Set

import pandas as pd

_log = logging.getLogger("archive")

# Step F listing_events market tag for ETF/ETN (same as enrich_market.MARKET_ETF_ETN).
MARKET_ETF_ETN = "etf외"

_NAME_ETF_HINTS = (
    "KODEX",
    "TIGER",
    "KOACT",
    "KIWOOM",
    "RISE",
    "TREX",
    "HANARO",
    "KBSTAR",
    "KINDEX",
    "ARIRANG",
    " ACE ",
    " SOL ",
    "FOCUS",
    "TIME ",
    "WON ",
    "VITA",
    "1Q ",
    "마이티",
    "파워 ",
)


def ensure_krx_env(krx_id: str, krx_pw: str) -> None:
    if krx_id and krx_pw:
        os.environ.setdefault("KRX_ID", krx_id)
        os.environ.setdefault("KRX_PW", krx_pw)


def refresh_krx_session(krx_id: str = "", krx_pw: str = "") -> None:
    """Ensure pykrx KRX auth session is active (auto re-login if expired)."""
    lid = krx_id or os.getenv("KRX_ID", "")
    lpw = krx_pw or os.getenv("KRX_PW", "")
    if not (lid and lpw):
        return
    ensure_krx_env(lid, lpw)
    try:
        from pykrx.website.comm.auth import get_auth_session

        get_auth_session()
    except Exception as exc:
        _log.debug("krx session refresh failed: %s", exc)


def load_etf_etn_symbol_set(as_of: str) -> Set[str]:
    """pykrx ETF/ETN ticker lists (best-effort; empty if KRX auth missing)."""
    from pykrx import stock

    out: Set[str] = set()
    ymd = str(as_of).strip()[:8]
    for loader_name in ("get_etf_ticker_list", "get_etn_ticker_list"):
        loader = getattr(stock, loader_name, None)
        if loader is None:
            continue
        try:
            tickers = loader(ymd)
            if tickers is not None:
                out.update(str(t).strip().zfill(6) for t in tickers)
        except Exception as exc:
            _log.debug("%s failed: %s", loader_name, exc)
    return out


def is_etf_or_etn(symbol: str, name: str = "", *, known: Optional[Set[str]] = None) -> bool:
    sym = str(symbol).strip().zfill(6)
    if known and sym in known:
        return True
    text = str(name or "").upper()
    if "ETF" in text or "ETN" in text:
        return True
    return any(h.upper() in text for h in _NAME_ETF_HINTS)


def should_use_etf_aum(
    symbol: str,
    name: str = "",
    *,
    known: Optional[Set[str]] = None,
    listing_market: str = "",
) -> bool:
    """True when ETF/ETN AUM path applies (listing_events etf외 or heuristics)."""
    if str(listing_market or "").strip() == MARKET_ETF_ETN:
        return True
    return is_etf_or_etn(symbol, name, known=known)


def is_etf_like(name: str) -> bool:
    """Backward-compatible name check (prefer is_etf_or_etn with pykrx set)."""
    return is_etf_or_etn("", name)


def _parse_krx_number(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return float("nan")
    text = str(value).strip().replace(",", "")
    if not text or text == "-":
        return float("nan")
    return float(pd.to_numeric(text, errors="coerce"))


def _find_column(columns, *patterns: str) -> Optional[str]:
    for col in columns:
        text = str(col).lower()
        for pat in patterns:
            p = pat.lower()
            if p in text or pat in str(col):
                return col
    return None


def fetch_pykrx_market_cap(symbol: str, fromdate: str, todate: str) -> pd.DataFrame:
    from pykrx import stock

    df = stock.get_market_cap_by_date(fromdate, todate, str(symbol).strip())
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    out = df.reset_index()
    date_col = out.columns[0]
    out = out.rename(columns={date_col: "date"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y%m%d")

    cap_col = _find_column(out.columns, "cap", "시가")
    shares_col = _find_column(out.columns, "shrs", "주식", "좌")
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


def get_etx_kind(symbol: str) -> str:
    """Return ETF/ETN kind from pykrx EtxTicker (empty if unknown)."""
    try:
        from pykrx.website.krx.etx.ticker import EtxTicker

        df = EtxTicker().df
        sym = str(symbol).strip().zfill(6)
        if sym not in df.index:
            return ""
        row = df.loc[sym]
        kind_col = None
        for col in row.index:
            if str(col) in ("종류", "kind") or "종류" in str(col):
                kind_col = col
                break
        kind = row[kind_col] if kind_col is not None else row.iloc[3]
        return str(kind).strip().upper()
    except Exception as exc:
        _log.debug("get_etx_kind failed %s: %s", symbol, exc)
        return ""


def fetch_pykrx_etn_aum_krx(symbol: str, fromdate: str, todate: str) -> pd.DataFrame:
    """
    ETN AUM from KRX 개별종목 시세 (MDCSTAT06601).

    Uses PER1SECU_INDIC_VAL x LIST_SHRS; falls back to INDIC_VAL_AMT or MKTCAP.
    """
    from pykrx.website.krx.etx.ticker import get_etx_isin
    from pykrx.website.krx.krxio import KrxWebIo

    class _개별종목시세_ETN(KrxWebIo):
        @property
        def bld(self):
            return "dbms/MDC/STAT/standard/MDCSTAT06601"

        def fetch(self, strtDd: str, endDd: str, isin: str) -> pd.DataFrame:
            result = self.read(isuCd=isin, strtDd=strtDd, endDd=endDd)
            return pd.DataFrame(result.get("output") or [])

    try:
        isin = get_etx_isin(str(symbol).strip())
    except Exception as exc:
        _log.debug("get_etx_isin failed %s: %s", symbol, exc)
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    raw = _개별종목시세_ETN().fetch(fromdate, todate, isin)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    rows: list[dict] = []
    for _, row in raw.iterrows():
        date_key = pd.to_datetime(str(row.get("TRD_DD", "")).replace("/", "-"), errors="coerce")
        if pd.isna(date_key):
            continue
        nav = _parse_krx_number(row.get("PER1SECU_INDIC_VAL"))
        shares = _parse_krx_number(row.get("LIST_SHRS"))
        official_aum = _parse_krx_number(row.get("INDIC_VAL_AMT"))
        mktcap = _parse_krx_number(row.get("MKTCAP"))

        market_cap = float("nan")
        if pd.notna(nav) and pd.notna(shares) and nav > 0 and shares > 0:
            market_cap = nav * shares
        elif pd.notna(official_aum) and official_aum > 0:
            market_cap = official_aum
        elif pd.notna(mktcap) and mktcap > 0:
            market_cap = mktcap

        if pd.isna(market_cap) or market_cap <= 0:
            continue

        rows.append(
            {
                "date": date_key.strftime("%Y%m%d"),
                "market_cap": market_cap,
                "shares_outstanding": shares if pd.notna(shares) and shares > 0 else pd.NA,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])
    return pd.DataFrame(rows).reset_index(drop=True)


def fetch_pykrx_etf_aum_krx(symbol: str, fromdate: str, todate: str) -> pd.DataFrame:
    """
    ETF/ETN AUM from KRX 개별종목시세_ETF: daily NAV(LST_NAV) x LIST_SHRS.

    Falls back to INVSTASST_NETASST_TOTAMT when product is zero but official AUM exists.
    """
    from pykrx.website.krx.etx.core import 개별종목시세_ETF
    from pykrx.website.krx.etx.ticker import get_etx_isin

    try:
        isin = get_etx_isin(str(symbol).strip())
    except Exception as exc:
        _log.debug("get_etx_isin failed %s: %s", symbol, exc)
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    raw = 개별종목시세_ETF().fetch(fromdate, todate, isin)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    rows: list[dict] = []
    for _, row in raw.iterrows():
        date_key = pd.to_datetime(str(row.get("TRD_DD", "")).replace("/", "-"), errors="coerce")
        if pd.isna(date_key):
            continue
        nav = _parse_krx_number(row.get("LST_NAV"))
        shares = _parse_krx_number(row.get("LIST_SHRS"))
        official_aum = _parse_krx_number(row.get("INVSTASST_NETASST_TOTAMT"))

        market_cap = float("nan")
        if pd.notna(nav) and pd.notna(shares) and nav > 0 and shares > 0:
            market_cap = nav * shares
        elif pd.notna(official_aum) and official_aum > 0:
            market_cap = official_aum

        if pd.isna(market_cap) or market_cap <= 0:
            continue

        rows.append(
            {
                "date": date_key.strftime("%Y%m%d"),
                "market_cap": market_cap,
                "shares_outstanding": shares if pd.notna(shares) and shares > 0 else pd.NA,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])
    return pd.DataFrame(rows).reset_index(drop=True)


def fetch_pykrx_etx_aum_krx(symbol: str, fromdate: str, todate: str) -> pd.DataFrame:
    """Route ETF -> 개별종목시세_ETF, ETN -> MDCSTAT06601; fallback try both."""
    kind = get_etx_kind(symbol)
    if kind == "ETN":
        df = fetch_pykrx_etn_aum_krx(symbol, fromdate, todate)
        if not df.empty:
            return df
        return fetch_pykrx_etf_aum_krx(symbol, fromdate, todate)
    if kind == "ETF":
        df = fetch_pykrx_etf_aum_krx(symbol, fromdate, todate)
        if not df.empty:
            return df
        return fetch_pykrx_etn_aum_krx(symbol, fromdate, todate)
    df = fetch_pykrx_etf_aum_krx(symbol, fromdate, todate)
    if not df.empty:
        return df
    return fetch_pykrx_etn_aum_krx(symbol, fromdate, todate)


def build_etf_aum_frame(nav_df: pd.DataFrame, shares_df: pd.DataFrame) -> pd.DataFrame:
    if nav_df.empty or shares_df.empty:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    nav = nav_df.copy()
    nav["date"] = nav["date"].astype(str)
    shares = shares_df.copy()
    shares["date"] = shares["date"].astype(str)
    merged = nav.merge(shares, on="date", how="inner")
    if merged.empty:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"])

    merged["market_cap"] = merged["nav"] * merged["shares_outstanding"]
    return merged[["date", "market_cap", "shares_outstanding"]].reset_index(drop=True)


def fetch_market_cap_for_year(
    symbol: str,
    year: int,
    bars: list[dict],
    *,
    name: str = "",
    listing_market: str = "",
    krx_id: str = "",
    krx_pw: str = "",
    etf_symbols: Optional[Set[str]] = None,
) -> tuple[pd.DataFrame, str]:
    """Return (dataframe[date, market_cap, shares_outstanding], method)."""
    year_bars = [b for b in bars if str(b.get("date", "")).startswith(str(int(year)))]
    if not year_bars:
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]), "empty"

    dates = sorted(str(b["date"]) for b in year_bars if b.get("date"))
    fromdate, todate = dates[0], dates[-1]
    sym = str(symbol).strip()

    refresh_krx_session(krx_id, krx_pw)

    if should_use_etf_aum(sym, name, known=etf_symbols, listing_market=listing_market):
        aum_df = fetch_pykrx_etx_aum_krx(sym, fromdate, todate)
        if not aum_df.empty:
            return aum_df, "etf_aum"
        return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]), "failed"

    cap_df = fetch_pykrx_market_cap(sym, fromdate, todate)
    if not cap_df.empty:
        return cap_df, "pykrx_mcap"

    return pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]), "failed"
