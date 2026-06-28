"""Post-delisting spot checks — data after delisting_date is an anomaly."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from core.archive_merge import merged_path
from core.archive_schema import utc_now_iso
from core.enrich_derived import features_path, read_features_parquet
from core.listing_events import listing_events_path, load_delisted_master


@dataclass
class PostDelistCheck:
    symbol: str
    name: str
    delisting_date: str
    status: str
    post_delist_bars: int = 0
    post_delist_mcap_rows: int = 0
    post_delist_bar_dates: List[str] = field(default_factory=list)
    post_delist_mcap_dates: List[str] = field(default_factory=list)
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "delisting_date": self.delisting_date,
            "status": self.status,
            "post_delist_bars": self.post_delist_bars,
            "post_delist_mcap_rows": self.post_delist_mcap_rows,
            "post_delist_bar_dates": self.post_delist_bar_dates,
            "post_delist_mcap_dates": self.post_delist_mcap_dates,
            "detail": self.detail,
        }


@dataclass
class PostDelistSpotReport:
    at_iso: str
    sample_size: int
    ok: int = 0
    anomaly: int = 0
    skipped: int = 0
    checks: List[PostDelistCheck] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "at_iso": self.at_iso,
            "sample_size": self.sample_size,
            "ok": self.ok,
            "anomaly": self.anomaly,
            "skipped": self.skipped,
            "checks": [c.to_dict() for c in self.checks],
        }


def _load_listing_events(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    path = listing_events_path(base_dir)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    symbols = payload.get("symbols") or {}
    return {str(k).zfill(6): v for k, v in symbols.items()}


def _post_delist_bar_dates(base_dir: Path, symbol: str, delisting_date: str) -> List[str]:
    path = merged_path(base_dir, symbol)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    out: List[str] = []
    for bar in payload.get("bars") or []:
        date_key = str(bar.get("date") or "").strip()
        if not date_key:
            continue
        if date_key > delisting_date:
            out.append(date_key)
    return sorted(set(out))


def _post_delist_mcap_dates(base_dir: Path, symbol: str, delisting_date: str) -> List[str]:
    path = features_path(base_dir, symbol)
    if not path.exists():
        return []
    df = read_features_parquet(path)
    if df.empty or "date" not in df.columns:
        return []
    if "market_cap" not in df.columns:
        return []

    dates = df["date"].astype(str)
    mcap = df["market_cap"]
    mask = dates.gt(delisting_date) & mcap.notna()
    return sorted(dates.loc[mask].unique().tolist())


def check_post_delist_symbol(
    base_dir: Path,
    symbol: str,
    *,
    delisting_date: Optional[str] = None,
    name: str = "",
    listing_events: Optional[Dict[str, Dict[str, Any]]] = None,
    max_sample_dates: int = 5,
) -> PostDelistCheck:
    sym = str(symbol).strip().zfill(6)
    events = listing_events if listing_events is not None else _load_listing_events(base_dir)
    rec = events.get(sym) or {}
    d_date = delisting_date or rec.get("delisting_date")
    display_name = name or str(rec.get("name") or "")

    if not d_date:
        return PostDelistCheck(
            symbol=sym,
            name=display_name,
            delisting_date="",
            status="skipped",
            detail="no_delisting_date",
        )

    bar_dates = _post_delist_bar_dates(base_dir, sym, d_date)
    mcap_dates = _post_delist_mcap_dates(base_dir, sym, d_date)
    has_anomaly = bool(bar_dates or mcap_dates)

    detail_parts: List[str] = []
    if bar_dates:
        detail_parts.append(f"bars_after_delist={len(bar_dates)}")
    if mcap_dates:
        detail_parts.append(f"mcap_after_delist={len(mcap_dates)}")

    return PostDelistCheck(
        symbol=sym,
        name=display_name,
        delisting_date=d_date,
        status="anomaly_post_delist" if has_anomaly else "ok",
        post_delist_bars=len(bar_dates),
        post_delist_mcap_rows=len(mcap_dates),
        post_delist_bar_dates=bar_dates[:max_sample_dates],
        post_delist_mcap_dates=mcap_dates[:max_sample_dates],
        detail="; ".join(detail_parts),
    )


def pick_spot_sample(symbols: Sequence[str], sample_size: int) -> List[str]:
    ordered = sorted({str(s).strip().zfill(6) for s in symbols if str(s).strip()})
    if sample_size <= 0 or len(ordered) <= sample_size:
        return ordered
    step = len(ordered) / float(sample_size)
    indices = {min(len(ordered) - 1, int(i * step)) for i in range(sample_size)}
    return [ordered[i] for i in sorted(indices)]


def load_delisted_spot_candidates(base_dir: Path, master_path: Path) -> List[Dict[str, Any]]:
    records = load_delisted_master(master_path)
    events = _load_listing_events(base_dir)
    out: List[Dict[str, Any]] = []
    for rec in records:
        sym = str(rec["symbol"]).strip().zfill(6)
        event = events.get(sym) or {}
        out.append(
            {
                "symbol": sym,
                "name": rec.get("name") or event.get("name") or "",
                "delisting_date": event.get("delisting_date") or rec.get("delisting_date"),
            }
        )
    return out


def run_post_delist_spot_check(
    base_dir: Path,
    symbols: Sequence[str],
    *,
    listing_events: Optional[Dict[str, Dict[str, Any]]] = None,
    names: Optional[Dict[str, str]] = None,
    delisting_dates: Optional[Dict[str, str]] = None,
) -> PostDelistSpotReport:
    events = listing_events if listing_events is not None else _load_listing_events(base_dir)
    names = names or {}
    delisting_dates = delisting_dates or {}
    report = PostDelistSpotReport(at_iso=utc_now_iso(), sample_size=len(symbols))

    for sym in symbols:
        s = str(sym).strip().zfill(6)
        check = check_post_delist_symbol(
            base_dir,
            s,
            delisting_date=delisting_dates.get(s) or (events.get(s) or {}).get("delisting_date"),
            name=names.get(s, ""),
            listing_events=events,
        )
        report.checks.append(check)
        if check.status == "ok":
            report.ok += 1
        elif check.status == "anomaly_post_delist":
            report.anomaly += 1
        else:
            report.skipped += 1

    return report
