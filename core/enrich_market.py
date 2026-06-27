"""Step F: enrich features sidecar with daily market (KOSPI/KOSDAQ) via pykrx."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

import pandas as pd

from core.archive_merge import load_collection_plan_years, load_symbols_active, merged_path
from core.market_cap_fetch import is_etf_or_etn, load_etf_etn_symbol_set
from core.archive_schema import utc_now_iso
from core.enrich_derived import (
    append_enrich_task,
    features_path,
    filter_frame_by_years,
    read_features_parquet,
    write_features_parquet,
)
from core.market_fetch import (
    ensure_market_daily_cache,
    load_market_membership_map,
    trading_dates_for_years,
)
from core.throttle import RequestThrottler

MARKET_STEP = "market"
MARKET_ETF_ETN = "etf외"
MARKET_FAILURES_PATH = "manifest/enrich_market_failures.jsonl"


def append_market_failure(base_dir: Path, entry: Dict[str, Any]) -> None:
    path = base_dir / MARKET_FAILURES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def list_merged_symbols(base_dir: Path) -> List[str]:
    merged_dir = base_dir / "merged"
    if not merged_dir.is_dir():
        return []
    return sorted(p.stem for p in merged_dir.glob("*.json"))


def build_etf_etn_symbol_set(base_dir: Path, as_of: str) -> Set[str]:
    """Merged-universe ETF/ETN symbols (pykrx lists + name hints)."""
    known = load_etf_etn_symbol_set(as_of)
    active = load_symbols_active(base_dir)
    out: Set[str] = set(known)
    for sym in list_merged_symbols(base_dir):
        if is_etf_or_etn(sym, active.get(sym, ""), known=known):
            out.add(str(sym).strip())
    return out


def _merge_market_into_features(
    existing: pd.DataFrame,
    symbol: str,
    membership_by_date: Dict[str, Dict[str, str]],
    *,
    etf_etn: bool = False,
) -> tuple[pd.DataFrame, int]:
    base = existing.copy()
    if "date" not in base.columns:
        base = base.reset_index()
        if "date" not in base.columns and len(base.columns):
            base = base.rename(columns={base.columns[0]: "date"})
    base["date"] = base["date"].astype(str)

    if etf_etn:
        base["market"] = MARKET_ETF_ETN
        return base.sort_values("date").reset_index(drop=True), 0

    if "market" not in base.columns:
        base["market"] = None

    sym = str(symbol).strip()
    unknown = 0

    def _lookup(date_key: str) -> Optional[str]:
        nonlocal unknown
        market = membership_by_date.get(date_key, {}).get(sym)
        if market is None and date_key in membership_by_date:
            unknown += 1
        return market

    base["market"] = base["date"].map(_lookup)
    return base.sort_values("date").reset_index(drop=True), unknown


@dataclass
class MarketSymbolResult:
    symbol: str
    ok: bool
    row_count: int = 0
    market_rows: int = 0
    unknown_rows: int = 0
    skipped: bool = False
    skip_reason: str = ""
    error: str = ""


@dataclass
class EnrichMarketReport:
    at_iso: str
    years: List[int]
    dates_total: int = 0
    cache_stats: Dict[str, int] = field(default_factory=dict)
    symbols_total: int = 0
    enriched: int = 0
    skipped: int = 0
    failed: int = 0
    unknown_rows: int = 0
    results: List[MarketSymbolResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "at_iso": self.at_iso,
            "step": MARKET_STEP,
            "years": self.years,
            "dates_total": self.dates_total,
            "cache_stats": self.cache_stats,
            "symbols_total": self.symbols_total,
            "enriched": self.enriched,
            "skipped": self.skipped,
            "failed": self.failed,
            "unknown_rows": self.unknown_rows,
            "results": [
                {
                    "symbol": r.symbol,
                    "ok": r.ok,
                    "row_count": r.row_count,
                    "market_rows": r.market_rows,
                    "unknown_rows": r.unknown_rows,
                    "skipped": r.skipped,
                    "skip_reason": r.skip_reason,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def enrich_symbol_market(
    base_dir: Path,
    symbol: str,
    *,
    years: Sequence[int],
    membership_by_date: Optional[Dict[str, Dict[str, str]]] = None,
    etf_etn_symbols: Optional[Set[str]] = None,
) -> MarketSymbolResult:
    sym = str(symbol).strip()
    years_list = sorted({int(y) for y in years}, reverse=True)
    feat_file = features_path(base_dir, sym)

    if not merged_path(base_dir, sym).exists():
        result = MarketSymbolResult(symbol=sym, ok=False, skipped=True, skip_reason="no_merged")
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": MARKET_STEP,
                "status": "skipped",
                "years": years_list,
                "error": result.skip_reason,
            },
        )
        return result

    if not feat_file.exists():
        result = MarketSymbolResult(symbol=sym, ok=False, skipped=True, skip_reason="no_features")
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": MARKET_STEP,
                "status": "skipped",
                "years": years_list,
                "error": result.skip_reason,
            },
        )
        return result

    try:
        existing = read_features_parquet(feat_file)
        scoped = filter_frame_by_years(existing, years_list)
        if scoped.empty:
            result = MarketSymbolResult(symbol=sym, ok=False, skipped=True, skip_reason="empty_features")
            append_enrich_task(
                base_dir,
                {
                    "at_iso": utc_now_iso(),
                    "symbol": sym,
                    "step": MARKET_STEP,
                    "status": "skipped",
                    "years": years_list,
                    "error": result.skip_reason,
                },
            )
            return result

        etf_etn = bool(etf_etn_symbols and sym in etf_etn_symbols)
        merged_df, unknown = _merge_market_into_features(
            existing,
            sym,
            membership_by_date or {},
            etf_etn=etf_etn,
        )
        write_features_parquet(feat_file, merged_df)

        out_scoped = filter_frame_by_years(merged_df, years_list)
        market_rows = int(out_scoped["market"].notna().sum()) if "market" in out_scoped.columns else 0

        result = MarketSymbolResult(
            symbol=sym,
            ok=True,
            row_count=len(out_scoped),
            market_rows=market_rows,
            unknown_rows=unknown,
        )
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": MARKET_STEP,
                "status": "done",
                "years": years_list,
                "row_count": result.row_count,
                "market_rows": market_rows,
                "unknown_rows": unknown,
                "error": "",
            },
        )
        if unknown > 0:
            append_market_failure(
                base_dir,
                {
                    "at_iso": utc_now_iso(),
                    "symbol": sym,
                    "step": MARKET_STEP,
                    "years": years_list,
                    "unknown_rows": unknown,
                    "error": "symbol_not_in_market_lists",
                },
            )
        return result
    except Exception as exc:
        result = MarketSymbolResult(symbol=sym, ok=False, error=str(exc))
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": MARKET_STEP,
                "status": "failed",
                "years": years_list,
                "error": str(exc),
            },
        )
        append_market_failure(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": MARKET_STEP,
                "years": years_list,
                "error": str(exc),
            },
        )
        return result


def patch_etf_etn_market(
    base_dir: Path,
    *,
    symbols: Optional[Sequence[str]] = None,
    as_of: str = "20261231",
) -> EnrichMarketReport:
    """Set market=etf외 for ETF/ETN symbols (no pykrx cache fetch)."""
    years_list = load_collection_plan_years(base_dir)
    etf_set = build_etf_etn_symbol_set(base_dir, as_of)
    target = [s for s in (symbols or list_merged_symbols(base_dir)) if str(s).strip() in etf_set]

    report = EnrichMarketReport(
        at_iso=utc_now_iso(),
        years=years_list,
        symbols_total=len(target),
    )

    for sym in target:
        result = enrich_symbol_market(
            base_dir,
            sym,
            years=years_list,
            membership_by_date={},
            etf_etn_symbols=etf_set,
        )
        report.results.append(result)
        report.unknown_rows += result.unknown_rows
        if result.skipped:
            report.skipped += 1
        elif result.ok:
            report.enriched += 1
        else:
            report.failed += 1

    return report


def enrich_all_market(
    base_dir: Path,
    *,
    years: Optional[Sequence[int]] = None,
    symbols: Optional[Sequence[str]] = None,
    chunk_id: Optional[int] = None,
    chunk_bounds_path: Optional[Path] = None,
    krx_id: str = "",
    krx_pw: str = "",
    throttler: Optional[RequestThrottler] = None,
    refresh_cache: bool = False,
) -> EnrichMarketReport:
    from core.chunk_bounds import assign_chunk

    years_list = sorted({int(y) for y in years}, reverse=True) if years else load_collection_plan_years(base_dir)
    target = list(symbols) if symbols is not None else list_merged_symbols(base_dir)

    if chunk_id is not None and chunk_bounds_path is not None:
        target = [s for s in target if assign_chunk(s, int(chunk_id), chunk_bounds_path)]

    trading_dates = trading_dates_for_years(years_list)
    cache_stats = ensure_market_daily_cache(
        base_dir,
        trading_dates,
        krx_id=krx_id,
        krx_pw=krx_pw,
        throttler=throttler,
        refresh=refresh_cache,
    )
    membership_by_date = load_market_membership_map(base_dir, trading_dates)
    max_year = max(years_list)
    etf_set = build_etf_etn_symbol_set(base_dir, f"{max_year}1231")

    report = EnrichMarketReport(
        at_iso=utc_now_iso(),
        years=years_list,
        dates_total=len(trading_dates),
        cache_stats=cache_stats,
        symbols_total=len(target),
    )

    for sym in target:
        result = enrich_symbol_market(
            base_dir,
            sym,
            years=years_list,
            membership_by_date=membership_by_date,
            etf_etn_symbols=etf_set,
        )
        report.results.append(result)
        report.unknown_rows += result.unknown_rows
        if result.skipped:
            report.skipped += 1
        elif result.ok:
            report.enriched += 1
        else:
            report.failed += 1

    return report
