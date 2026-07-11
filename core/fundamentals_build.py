# -*- coding: utf-8 -*-
"""Build fundamentals event rows + daily as-of expansion."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd

from core.dart_client import REPRT_CODES

_ACCOUNT_MAP = {
    "revenue": ("매출액", "수익(매출액)", "매출", "영업수익"),
    "operating_income": ("영업이익", "영업이익(손실)"),
    "net_income": (
        "당기순이익",
        "당기순이익(손실)",
        "분기순이익",
        "분기순이익(손실)",
        "반기순이익",
        "반기순이익(손실)",
    ),
    "equity": ("자본총계",),
    "assets": ("자산총계",),
    "liabilities": ("부채총계",),
}


def _parse_amount(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s in ("-", "—"):
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "").replace(" ", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", "", (name or "").strip())


def _pick_fs_rows(rows: Sequence[dict]) -> List[dict]:
    """Prefer CFS; fallback OFS."""
    cfs = [r for r in rows if str(r.get("fs_div", "")).upper() == "CFS"]
    if cfs:
        return cfs
    ofs = [r for r in rows if str(r.get("fs_div", "")).upper() == "OFS"]
    return ofs if ofs else list(rows)


def _extract_accounts(rows: Sequence[dict]) -> Dict[str, Optional[float]]:
    by_name: Dict[str, dict] = {}
    for r in rows:
        nm = _norm_name(str(r.get("account_nm", "")))
        if nm and nm not in by_name:
            by_name[nm] = r

    out: Dict[str, Optional[float]] = {k: None for k in _ACCOUNT_MAP}
    for field, aliases in _ACCOUNT_MAP.items():
        for alias in aliases:
            hit = by_name.get(_norm_name(alias))
            if hit is None:
                continue
            # Prefer cumulative when present for income statement flow items
            amt = _parse_amount(hit.get("thstrm_add_amount"))
            if amt is None:
                amt = _parse_amount(hit.get("thstrm_amount"))
            out[field] = amt
            break
    return out


def accounts_to_event(
    *,
    symbol: str,
    corp_code: str,
    bsns_year: int,
    reprt_code: str,
    rows: Sequence[dict],
) -> Optional[Dict[str, Any]]:
    if not rows:
        return None
    picked = _pick_fs_rows(rows)
    if not picked:
        return None
    first = picked[0]
    rcept_no = str(first.get("rcept_no", "") or "").strip()
    if len(rcept_no) < 8:
        return None
    rcept_dt = rcept_no[:8]
    fiscal_end = str(first.get("thstrm_dt", "") or "").strip()
    fiscal_end = re.sub(r"[^0-9]", "", fiscal_end)[:8] or ""
    accts = _extract_accounts(picked)
    fs_div = str(first.get("fs_div", "") or "").upper() or "CFS"
    return {
        "symbol": str(symbol).zfill(6),
        "corp_code": corp_code,
        "bsns_year": int(bsns_year),
        "reprt_code": str(reprt_code),
        "reprt_name": REPRT_CODES.get(str(reprt_code), str(reprt_code)),
        "rcept_no": rcept_no,
        "rcept_dt": rcept_dt,
        "fiscal_end": fiscal_end,
        "fs_div": fs_div,
        "revenue": accts["revenue"],
        "operating_income": accts["operating_income"],
        "net_income": accts["net_income"],
        "equity": accts["equity"],
        "assets": accts["assets"],
        "liabilities": accts["liabilities"],
        "eps": None,  # filled later if available
        "source": "opendart_fnlttSinglAcnt",
        "fetched_at_iso": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def events_to_frame(events: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    rows = list(events)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.sort_values(["rcept_dt", "bsns_year", "reprt_code"]).reset_index(drop=True)
    return df


def expand_daily_asof(
    events: pd.DataFrame,
    *,
    daily: pd.DataFrame,
    close_col: str = "close",
    shares_col: str = "shares_outstanding",
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Forward-fill event fundamentals onto daily bars using rcept_dt as as-of.
    `daily` must have date, close, shares_outstanding.
    """
    if events.empty or daily.empty:
        return pd.DataFrame()

    d = daily.copy()
    if date_col in d.columns:
        d[date_col] = d[date_col].astype(str).str.replace(r"\D", "", regex=True).str[:8]
    else:
        d = d.reset_index()
        d[date_col] = d[date_col].astype(str).str.replace(r"\D", "", regex=True).str[:8]

    d = d.sort_values(date_col).reset_index(drop=True)
    d["_asof_key"] = d[date_col].astype(int)
    ev = events.copy()
    ev["rcept_dt"] = ev["rcept_dt"].astype(str).str[:8]
    ev = ev.sort_values("rcept_dt").drop_duplicates("rcept_dt", keep="last")
    ev["_asof_key"] = ev["rcept_dt"].astype(int)

    right = ev[
        [
            "_asof_key",
            "rcept_dt",
            "reprt_code",
            "revenue",
            "operating_income",
            "net_income",
            "equity",
            "eps",
        ]
    ].rename(
        columns={
            "rcept_dt": "fund_asof_date",
            "reprt_code": "fund_reprt_code",
            "revenue": "revenue_asof",
            "operating_income": "operating_income_asof",
            "net_income": "net_income_asof",
            "equity": "equity_asof",
            "eps": "eps_raw",
        }
    )

    merged = pd.merge_asof(
        d,
        right,
        on="_asof_key",
        direction="backward",
    )

    shares = pd.to_numeric(merged[shares_col], errors="coerce")
    close = pd.to_numeric(merged[close_col], errors="coerce")
    equity = pd.to_numeric(merged["equity_asof"], errors="coerce")
    ni = pd.to_numeric(merged["net_income_asof"], errors="coerce")
    eps_raw = pd.to_numeric(merged["eps_raw"], errors="coerce")

    eps = eps_raw.copy()
    method = pd.Series("dart_eps", index=merged.index)
    need = eps.isna() | (eps == 0)
    approx = ni / shares
    eps = eps.where(~need, approx)
    method = method.where(~need, "ni_over_shares")
    method = method.where(eps.notna() & shares.notna(), None)

    bps = equity / shares
    per = close / eps
    pbr = close / bps
    per = per.where((eps > 0) & close.notna())
    pbr = pbr.where((bps > 0) & close.notna())

    out = pd.DataFrame(
        {
            "date": merged[date_col],
            "fund_asof_date": merged["fund_asof_date"],
            "fund_reprt_code": merged["fund_reprt_code"],
            "revenue_asof": merged["revenue_asof"],
            "operating_income_asof": merged["operating_income_asof"],
            "net_income_asof": merged["net_income_asof"],
            "equity_asof": merged["equity_asof"],
            "eps_asof": eps,
            "bps_asof": bps,
            "per": per,
            "pbr": pbr,
            "eps_method": method,
        }
    )
    return out
