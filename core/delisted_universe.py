"""FDR KRX-DELISTING universe filters for Step G (상폐 주권, KONEX 제외)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

SECU_GROUP_JOO = "주권"
MARKET_KONEX = "KONEX"
SPAC_RE = re.compile(r"SPAC|스팩", re.IGNORECASE)
SYMBOL_RE = re.compile(r"^\d{6}$")


def fetch_fdr_delisting() -> pd.DataFrame:
    import FinanceDataReader as fdr

    return fdr.StockListing("KRX-DELISTING")


def is_spac_name(name: str) -> bool:
    return bool(SPAC_RE.search(str(name or "")))


def normalize_market(market: str) -> str:
    m = str(market or "").strip().upper()
    if m in {"KOSPI", "KOSDAQ", "KONEX"}:
        return m
    return m or ""


def date_to_ymd(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y%m%d")
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    text = str(value).strip()
    if not text or text.lower() in {"nat", "none"}:
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 8:
        return digits[:8]
    return None


def _resolve_joo_label(df: pd.DataFrame) -> str:
    if "SecuGroup" not in df.columns:
        return SECU_GROUP_JOO
    groups = df["SecuGroup"].astype(str)
    if (groups == SECU_GROUP_JOO).any():
        return SECU_GROUP_JOO
    counts = groups.value_counts()
    return str(counts.index[0])


def filter_delisted_universe(
    df: pd.DataFrame,
    *,
    year_from: int = 2020,
    year_to: int = 2026,
    exclude_spac: bool = True,
    exclude_konex: bool = True,
    six_digit_only: bool = True,
) -> pd.DataFrame:
    """Return filtered delisted 주권 rows (FDR KRX-DELISTING)."""
    if df.empty:
        return df.copy()

    work = df.copy()
    joo = _resolve_joo_label(work)
    work = work[work["SecuGroup"].astype(str) == joo]

    work["DelistingDate"] = pd.to_datetime(work["DelistingDate"], errors="coerce")
    start = pd.Timestamp(f"{int(year_from)}-01-01")
    end = pd.Timestamp(f"{int(year_to)}-12-31")
    work = work[(work["DelistingDate"] >= start) & (work["DelistingDate"] <= end)]

    if exclude_spac:
        work = work[~work["Name"].map(is_spac_name)]

    if six_digit_only:
        work = work[work["Symbol"].astype(str).str.match(SYMBOL_RE)]

    if exclude_konex and "Market" in work.columns:
        work = work[work["Market"].astype(str).str.upper() != MARKET_KONEX]

    work = work.sort_values(["DelistingDate", "Symbol"], ascending=[True, True])
    return work.reset_index(drop=True)


def row_to_record(row: pd.Series) -> Dict[str, Any]:
    symbol = str(row["Symbol"]).strip().zfill(6)
    return {
        "symbol": symbol,
        "name": str(row.get("Name", "") or "").strip(),
        "market": normalize_market(str(row.get("Market", "") or "")),
        "listing_date": date_to_ymd(row.get("ListingDate")),
        "delisting_date": date_to_ymd(row.get("DelistingDate")),
        "reason": str(row.get("Reason", "") or "").strip(),
        "secu_group": str(row.get("SecuGroup", "") or SECU_GROUP_JOO).strip(),
        "industry": str(row.get("Industry", "") or "").strip(),
    }


def records_from_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return [row_to_record(row) for _, row in df.iterrows()]


def build_yearly_report(
    records: List[Dict[str, Any]],
    *,
    year_from: int = 2020,
    year_to: int = 2026,
) -> Dict[str, Any]:
    by_year: Dict[str, List[Dict[str, Any]]] = {}
    counts: Dict[str, int] = {}
    reason_counts: Dict[str, Dict[str, int]] = {}

    for rec in records:
        ymd = rec.get("delisting_date") or ""
        if len(ymd) < 4:
            continue
        year = ymd[:4]
        if int(year) < int(year_from) or int(year) > int(year_to):
            continue
        by_year.setdefault(year, []).append(rec)
        counts[year] = counts.get(year, 0) + 1
        reason = rec.get("reason") or "(empty)"
        reason_counts.setdefault(year, {})
        reason_counts[year][reason] = reason_counts[year].get(reason, 0) + 1

    for year in by_year:
        by_year[year] = sorted(by_year[year], key=lambda r: (r.get("delisting_date", ""), r["symbol"]))

    return {
        "year_from": int(year_from),
        "year_to": int(year_to),
        "total": len(records),
        "counts_by_year": {str(y): counts.get(str(y), 0) for y in range(int(year_from), int(year_to) + 1)},
        "reason_counts_by_year": reason_counts,
        "symbols_by_year": by_year,
    }
