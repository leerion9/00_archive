"use Step B derived sidecar fields from merged OHLCV bars."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from core.archive_merge import load_collection_plan_years, merged_path
from core.archive_schema import utc_now_iso
from core.bar_merge import normalize_date

DERIVED_STEP = "derived"
FEATURE_COLUMNS = ("trading_value", "value_ma5", "close_ma5")


def features_path(base_dir: Path, symbol: str) -> Path:
    return base_dir / "features" / f"{str(symbol).strip()}.parquet"


def enrich_tasks_path(base_dir: Path) -> Path:
    return base_dir / "manifest" / "enrich_tasks.jsonl"


def append_enrich_task(base_dir: Path, entry: Dict[str, Any]) -> None:
    path = enrich_tasks_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def filter_bars_by_years(bars: List[Dict[str, Any]], years: Sequence[int]) -> List[Dict[str, Any]]:
    prefixes = {str(int(y)) for y in years}
    return [
        b
        for b in bars
        if any(str(b.get("date", "")).startswith(prefix) for prefix in prefixes)
    ]


def bars_to_frame(bars: List[Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for bar in bars:
        date_key = normalize_date(str(bar.get("date", "") or ""))
        if not date_key:
            continue
        rows.append(
            {
                "date": date_key,
                "close": int(bar.get("close", 0) or 0),
                "volume": int(bar.get("volume", 0) or 0),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["date", "close", "volume"])
    df = pd.DataFrame(rows)
    return df.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)


def compute_derived_frame(bars: List[Dict[str, Any]]) -> pd.DataFrame:
    df = bars_to_frame(bars)
    if df.empty:
        return pd.DataFrame(columns=list(FEATURE_COLUMNS))

    df["trading_value"] = df["close"] * df["volume"]
    df["value_ma5"] = df["trading_value"].rolling(window=5, min_periods=5).mean()
    df["close_ma5"] = df["close"].rolling(window=5, min_periods=5).mean()
    return df[["date", *FEATURE_COLUMNS]]


def filter_frame_by_years(df: pd.DataFrame, years: Sequence[int]) -> pd.DataFrame:
    if df.empty or not years:
        return df
    prefixes = tuple(str(int(y)) for y in years)
    mask = df["date"].astype(str).str.startswith(prefixes)
    return df.loc[mask].reset_index(drop=True)


def write_features_parquet(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    if out.empty:
        out = pd.DataFrame(columns=["date", *FEATURE_COLUMNS])
    out = out.set_index("date")
    out.to_parquet(path, index=True)


def read_features_parquet(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if df.index.name == "date":
        df = df.reset_index()
    return df


def load_merged_bars(base_dir: Path, symbol: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    path = merged_path(base_dir, symbol)
    if not path.exists():
        return [], {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("bars") or []), payload


@dataclass
class EnrichSymbolResult:
    symbol: str
    ok: bool
    row_count: int = 0
    years: List[int] = field(default_factory=list)
    features_path: Optional[Path] = None
    skipped: bool = False
    skip_reason: str = ""
    error: str = ""


@dataclass
class EnrichDerivedReport:
    at_iso: str
    step: str = DERIVED_STEP
    years: List[int] = field(default_factory=list)
    symbols_total: int = 0
    enriched: int = 0
    skipped: int = 0
    failed: int = 0
    results: List[EnrichSymbolResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "at_iso": self.at_iso,
            "step": self.step,
            "years": self.years,
            "symbols_total": self.symbols_total,
            "enriched": self.enriched,
            "skipped": self.skipped,
            "failed": self.failed,
            "results": [
                {
                    "symbol": r.symbol,
                    "ok": r.ok,
                    "row_count": r.row_count,
                    "years": r.years,
                    "features_path": str(r.features_path) if r.features_path else None,
                    "skipped": r.skipped,
                    "skip_reason": r.skip_reason,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def enrich_symbol_derived(
    base_dir: Path,
    symbol: str,
    *,
    years: Optional[Sequence[int]] = None,
) -> EnrichSymbolResult:
    sym = str(symbol).strip()
    years_list = sorted({int(y) for y in years}, reverse=True) if years else []

    bars, merged_meta = load_merged_bars(base_dir, sym)
    if not merged_meta:
        result = EnrichSymbolResult(
            symbol=sym,
            ok=False,
            skipped=True,
            skip_reason="no_merged",
        )
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": DERIVED_STEP,
                "status": "skipped",
                "years": years_list,
                "row_count": 0,
                "error": result.skip_reason,
            },
        )
        return result

    if not bars:
        result = EnrichSymbolResult(
            symbol=sym,
            ok=False,
            skipped=True,
            skip_reason="empty_bars",
        )
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": DERIVED_STEP,
                "status": "skipped",
                "years": years_list,
                "row_count": 0,
                "error": result.skip_reason,
            },
        )
        return result

    try:
        full_df = compute_derived_frame(bars)
        out_df = filter_frame_by_years(full_df, years_list) if years_list else full_df
        out_path = features_path(base_dir, sym)
        write_features_parquet(out_path, out_df)
        result = EnrichSymbolResult(
            symbol=sym,
            ok=True,
            row_count=len(out_df),
            years=years_list or sorted(
                {int(str(d)[:4]) for d in out_df["date"].astype(str)},
                reverse=True,
            ),
            features_path=out_path,
        )
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": DERIVED_STEP,
                "status": "done",
                "years": result.years,
                "row_count": result.row_count,
                "merged_updated_at_iso": merged_meta.get("updated_at_iso"),
                "error": "",
            },
        )
        return result
    except Exception as exc:
        result = EnrichSymbolResult(
            symbol=sym,
            ok=False,
            skipped=False,
            error=str(exc),
        )
        append_enrich_task(
            base_dir,
            {
                "at_iso": utc_now_iso(),
                "symbol": sym,
                "step": DERIVED_STEP,
                "status": "failed",
                "years": years_list,
                "row_count": 0,
                "error": str(exc),
            },
        )
        return result


def list_merged_symbols(base_dir: Path) -> List[str]:
    merged_dir = base_dir / "merged"
    if not merged_dir.is_dir():
        return []
    return sorted(p.stem for p in merged_dir.glob("*.json"))


def enrich_all_derived(
    base_dir: Path,
    *,
    years: Optional[Sequence[int]] = None,
    symbols: Optional[Sequence[str]] = None,
    chunk_id: Optional[int] = None,
    chunk_bounds_path: Optional[Path] = None,
) -> EnrichDerivedReport:
    from core.chunk_bounds import assign_chunk

    years_list = sorted({int(y) for y in years}, reverse=True) if years else load_collection_plan_years(base_dir)
    target = list(symbols) if symbols is not None else list_merged_symbols(base_dir)

    if chunk_id is not None and chunk_bounds_path is not None:
        target = [s for s in target if assign_chunk(s, int(chunk_id), chunk_bounds_path)]

    report = EnrichDerivedReport(
        at_iso=utc_now_iso(),
        years=years_list,
        symbols_total=len(target),
    )

    for sym in target:
        result = enrich_symbol_derived(base_dir, sym, years=years_list if years_list else None)
        report.results.append(result)
        if result.skipped:
            report.skipped += 1
        elif result.ok:
            report.enriched += 1
        else:
            report.failed += 1

    return report
