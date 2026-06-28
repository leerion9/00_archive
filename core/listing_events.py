"""Build master/listing_events.json for Step G (pykrx listing + FDR delisting)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from core.archive_merge import load_symbols_active
from core.archive_schema import utc_now_iso
from core.delisted_universe import (
    build_yearly_report,
    fetch_fdr_delisting,
    filter_delisted_universe,
    normalize_market,
    records_from_dataframe,
)
from core.market_cap_fetch import refresh_krx_session

DATE_RE = re.compile(r"^\d{8}$")


def _col_by_hint(columns: List[str], *hints: str) -> Optional[str]:
    for col in columns:
        text = str(col)
        for hint in hints:
            if hint in text:
                return col
    return None


def fetch_pykrx_stock_listings(krx_id: str = "", krx_pw: str = "") -> Dict[str, Dict[str, Any]]:
    """Current KRX stock listings with listing_date from pykrx."""
    refresh_krx_session(krx_id, krx_pw)
    from pykrx import stock

    df = stock.get_market_ohlcv_by_market("ALL")
    if df.empty:
        return {}

    cols = [str(c) for c in df.columns]
    listing_col = _col_by_hint(cols, "상장일", "Listing")
    market_col = _col_by_hint(cols, "시장구분", "Market")
    name_col = _col_by_hint(cols, "한글종목명", "종목명", "Name") or cols[1]

    out: Dict[str, Dict[str, Any]] = {}
    for ticker, row in df.iterrows():
        sym = str(ticker).strip().zfill(6)
        listing_date = None
        if listing_col is not None:
            val = row[listing_col]
            if isinstance(val, pd.Timestamp):
                listing_date = val.strftime("%Y%m%d")
            else:
                digits = re.sub(r"\D", "", str(val))
                listing_date = digits[:8] if len(digits) >= 8 else None
        market = normalize_market(str(row[market_col])) if market_col else ""
        out[sym] = {
            "name": str(row[name_col]).strip(),
            "market": market,
            "listing_date": listing_date,
            "source": "pykrx_stock",
        }
    return out


def fetch_pykrx_etf_listings(krx_id: str = "", krx_pw: str = "") -> Dict[str, Dict[str, Any]]:
    """ETF/ETN listing dates from pykrx EtxTicker."""
    refresh_krx_session(krx_id, krx_pw)
    try:
        from pykrx.website.krx.etx.ticker import EtxTicker
    except Exception:
        return {}

    df = getattr(EtxTicker(), "df", None)
    if df is None or df.empty:
        return {}

    cols = [str(c) for c in df.columns]
    listing_col = cols[2] if len(cols) > 2 else None
    kind_col = cols[3] if len(cols) > 3 else None
    name_col = cols[1] if len(cols) > 1 else None

    out: Dict[str, Dict[str, Any]] = {}
    for ticker, row in df.iterrows():
        sym = str(ticker).strip().zfill(6)
        listing_raw = str(row[listing_col]).strip() if listing_col else ""
        listing_date = listing_raw if DATE_RE.match(listing_raw) else None
        kind = str(row[kind_col]).strip() if kind_col else "ETF"
        out[sym] = {
            "name": str(row[name_col]).strip() if name_col else "",
            "market": "etf외",
            "listing_date": listing_date,
            "source": "pykrx_etf",
            "kind": kind,
        }
    return out


def build_delisted_master(
    *,
    year_from: int = 2020,
    year_to: int = 2026,
    exclude_konex: bool = True,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw = fetch_fdr_delisting()
    filtered = filter_delisted_universe(
        raw,
        year_from=year_from,
        year_to=year_to,
        exclude_konex=exclude_konex,
    )
    records = records_from_dataframe(filtered)
    report = build_yearly_report(records, year_from=year_from, year_to=year_to)
    return records, report


def _event_delisted(rec: Dict[str, Any]) -> List[Dict[str, str]]:
    d = rec.get("delisting_date")
    if not d:
        return []
    return [
        {
            "type": "delisted",
            "date": d,
            "reason": str(rec.get("reason") or "").strip(),
            "note": "",
        }
    ]


def build_listing_events_payload(
    *,
    active_symbols: Dict[str, str],
    delisted_records: List[Dict[str, Any]],
    stock_listings: Dict[str, Dict[str, Any]],
    etf_listings: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    symbols: Dict[str, Dict[str, Any]] = {}

    for sym, name in sorted(active_symbols.items()):
        meta = stock_listings.get(sym) or etf_listings.get(sym) or {}
        symbols[sym] = {
            "name": meta.get("name") or name,
            "market": meta.get("market") or "",
            "listing_date": meta.get("listing_date"),
            "delisting_date": None,
            "status": "listed",
            "events": [],
            "listing_source": meta.get("source", ""),
        }

    for rec in delisted_records:
        sym = str(rec["symbol"]).strip().zfill(6)
        if sym in symbols and symbols[sym].get("status") == "listed":
            # Active snapshot should not overlap delisted universe; keep delisted if conflict.
            pass
        symbols[sym] = {
            "name": rec.get("name") or symbols.get(sym, {}).get("name", ""),
            "market": rec.get("market") or symbols.get(sym, {}).get("market", ""),
            "listing_date": rec.get("listing_date") or symbols.get(sym, {}).get("listing_date"),
            "delisting_date": rec.get("delisting_date"),
            "status": "delisted",
            "events": _event_delisted(rec),
            "listing_source": "fdr_delisting",
        }

    return {
        "schema_version": 1,
        "updated_at_iso": utc_now_iso(),
        "source": "pykrx_listing+fdr_delisting",
        "symbols": symbols,
    }


def validate_listing_events(
    payload: Dict[str, Any],
    *,
    expected_delisted: int,
    expected_total: int,
    delisted_symbols: Optional[set[str]] = None,
) -> List[str]:
    errors: List[str] = []
    symbols = payload.get("symbols") or {}
    if len(symbols) != expected_total:
        errors.append(f"symbol count {len(symbols)} != expected {expected_total}")

    delisted = [s for s, row in symbols.items() if row.get("status") == "delisted"]
    if len(delisted) != expected_delisted:
        errors.append(f"delisted count {len(delisted)} != expected {expected_delisted}")

    if delisted_symbols is not None:
        missing = delisted_symbols - set(delisted)
        extra = set(delisted) - delisted_symbols
        if missing:
            errors.append(f"delisted missing: {sorted(missing)[:5]}")
        if extra:
            errors.append(f"unexpected delisted: {sorted(extra)[:5]}")

    for sym, row in symbols.items():
        for field in ("listing_date", "delisting_date"):
            val = row.get(field)
            if val is not None and not DATE_RE.match(str(val)):
                errors.append(f"{sym}.{field} invalid: {val}")
                break

    return errors


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def delisted_master_path(base_dir: Path) -> Path:
    return base_dir / "master" / "symbols_delisted_joo_2020_2026.json"


def delisted_report_path(base_dir: Path) -> Path:
    return base_dir / "reports" / "delisting_joo_ex_spac_2020_2026_by_year.json"


def listing_events_path(base_dir: Path) -> Path:
    return base_dir / "master" / "listing_events.json"


def load_delisted_master(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw.get("symbols"), list):
        return raw["symbols"]
    return []


def save_delisted_master(
    base_dir: Path,
    records: List[Dict[str, Any]],
    *,
    year_from: int,
    year_to: int,
    exclude_konex: bool,
) -> Path:
    path = delisted_master_path(base_dir)
    payload = {
        "schema_version": 1,
        "updated_at_iso": utc_now_iso(),
        "source": "fdr_krx_delisting",
        "filters": {
            "delisting_year_from": int(year_from),
            "delisting_year_to": int(year_to),
            "secu_group": "주권",
            "exclude_spac": True,
            "exclude_konex": bool(exclude_konex),
            "six_digit_only": True,
        },
        "count": len(records),
        "symbols": records,
    }
    write_json(path, payload)
    return path


def save_delisted_report(base_dir: Path, report: Dict[str, Any]) -> Path:
    path = delisted_report_path(base_dir)
    payload = {
        "schema_version": 1,
        "updated_at_iso": utc_now_iso(),
        "source": "fdr_krx_delisting",
        **report,
    }
    write_json(path, payload)
    return path


def build_and_save_g1(
    base_dir: Path,
    *,
    year_from: int = 2020,
    year_to: int = 2026,
    exclude_konex: bool = True,
) -> Tuple[List[Dict[str, Any]], Path, Path]:
    records, report = build_delisted_master(
        year_from=year_from,
        year_to=year_to,
        exclude_konex=exclude_konex,
    )
    master_path = save_delisted_master(
        base_dir,
        records,
        year_from=year_from,
        year_to=year_to,
        exclude_konex=exclude_konex,
    )
    report_path = save_delisted_report(base_dir, report)
    return records, master_path, report_path


def build_and_save_g2(
    base_dir: Path,
    delisted_records: List[Dict[str, Any]],
    *,
    krx_id: str = "",
    krx_pw: str = "",
) -> Tuple[Dict[str, Any], Path, List[str]]:
    active = load_symbols_active(base_dir)
    if not active:
        raise FileNotFoundError(f"symbols_active missing under {base_dir / 'master'}")

    stock_listings = fetch_pykrx_stock_listings(krx_id, krx_pw)
    etf_listings = fetch_pykrx_etf_listings(krx_id, krx_pw)
    payload = build_listing_events_payload(
        active_symbols=active,
        delisted_records=delisted_records,
        stock_listings=stock_listings,
        etf_listings=etf_listings,
    )

    delisted_syms = {str(r["symbol"]).zfill(6) for r in delisted_records}
    errors = validate_listing_events(
        payload,
        expected_delisted=len(delisted_records),
        expected_total=len(active) + len(delisted_records),
        delisted_symbols=delisted_syms,
    )

    path = listing_events_path(base_dir)
    write_json(path, payload)
    return payload, path, errors
