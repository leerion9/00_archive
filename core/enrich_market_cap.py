"""Step C: enrich features sidecar with daily market_cap via pykrx."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from core.archive_merge import load_collection_plan_years, load_symbols_active, merged_path
from core.archive_schema import utc_now_iso
from core.chunk_bounds import assign_chunk, enrich_chunk_config_path, write_enrich_chunk_config
from core.enrich_derived import append_enrich_task, features_path, read_features_parquet, write_features_parquet
from core.market_cap_fetch import fetch_market_cap_for_year, load_etf_etn_symbol_set, refresh_krx_session
from core.shard import task_id
from core.throttle import RequestThrottler

MCAP_STEP = "market_cap"
MCAP_FAILURES_PATH = "manifest/enrich_mcap_failures.jsonl"


def build_mcap_tasks(
    base_dir: Path,
    *,
    years: Sequence[int],
    chunk_id: Optional[int] = None,
    chunk_bounds_path: Optional[Path] = None,
    symbols: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    active = load_symbols_active(base_dir)
    if symbols is not None:
        syms = sorted({str(s).strip() for s in symbols if str(s).strip()})
    else:
        syms = sorted(p.stem for p in (base_dir / "merged").glob("*.json"))

    if chunk_id is not None and chunk_bounds_path is not None:
        syms = [s for s in syms if assign_chunk(s, int(chunk_id), chunk_bounds_path)]

    tasks: List[Dict[str, Any]] = []
    for sym in syms:
        for year in years:
            tasks.append(
                {
                    "task_id": task_id(sym, year),
                    "symbol": sym,
                    "name": active.get(sym, ""),
                    "year": int(year),
                    "step": MCAP_STEP,
                    "status": "pending",
                }
            )
    return tasks


def _merge_mcap_into_features(existing: pd.DataFrame, mcap_df: pd.DataFrame, method: str) -> pd.DataFrame:
    base = existing.copy()
    if "date" not in base.columns:
        base = base.reset_index()
        if "date" not in base.columns and len(base.columns):
            base = base.rename(columns={base.columns[0]: "date"})
    base["date"] = base["date"].astype(str)

    for col, default in (
        ("market_cap", pd.NA),
        ("shares_outstanding", pd.NA),
        ("market_cap_method", None),
    ):
        if col not in base.columns:
            base[col] = default

    add = mcap_df.copy()
    add["date"] = add["date"].astype(str)
    add["market_cap_method"] = method
    by_date = add.set_index("date")

    for date_key, row in by_date.iterrows():
        mask = base["date"] == str(date_key)
        if not mask.any():
            continue
        base.loc[mask, "market_cap"] = row.get("market_cap")
        if "shares_outstanding" in row.index:
            base.loc[mask, "shares_outstanding"] = row.get("shares_outstanding")
        base.loc[mask, "market_cap_method"] = method

    return base.sort_values("date").reset_index(drop=True)


def _clear_mcap_for_year(features: pd.DataFrame, year: int) -> pd.DataFrame:
    base = features.copy()
    if "date" not in base.columns:
        return base
    prefix = str(int(year))
    mask = base["date"].astype(str).str.startswith(prefix)
    for col in ("market_cap", "shares_outstanding", "market_cap_method"):
        if col in base.columns:
            base.loc[mask, col] = pd.NA if col != "market_cap_method" else None
    return base


def append_mcap_failure(base_dir: Path, entry: Dict[str, Any]) -> None:
    path = base_dir / MCAP_FAILURES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


@dataclass
class McapTaskResult:
    task_id: str
    symbol: str
    year: int
    ok: bool
    rows: int = 0
    method: str = ""
    error: str = ""


@dataclass
class EnrichMcapReport:
    at_iso: str
    chunk_id: Optional[int]
    years: List[int]
    tasks_total: int
    done: int = 0
    failed: int = 0
    skipped: int = 0
    methods: Dict[str, int] = field(default_factory=dict)
    results: List[McapTaskResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "at_iso": self.at_iso,
            "step": MCAP_STEP,
            "chunk_id": self.chunk_id,
            "years": self.years,
            "tasks_total": self.tasks_total,
            "done": self.done,
            "failed": self.failed,
            "skipped": self.skipped,
            "methods": self.methods,
            "results": [
                {
                    "task_id": r.task_id,
                    "symbol": r.symbol,
                    "year": r.year,
                    "ok": r.ok,
                    "rows": r.rows,
                    "method": r.method,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def run_mcap_enrich(
    base_dir: Path,
    tasks: List[Dict[str, Any]],
    *,
    chunk_id: Optional[int] = None,
    krx_id: str = "",
    krx_pw: str = "",
    throttler: Optional[RequestThrottler] = None,
) -> EnrichMcapReport:
    years = sorted({int(t["year"]) for t in tasks}, reverse=True)
    report = EnrichMcapReport(
        at_iso=utc_now_iso(),
        chunk_id=chunk_id,
        years=years,
        tasks_total=len(tasks),
    )

    max_year = max(int(t["year"]) for t in tasks)
    etf_symbols = load_etf_etn_symbol_set(f"{max_year}1231")
    feature_cache: dict[str, pd.DataFrame] = {}

    for i, task in enumerate(tasks):
        if i > 0 and i % 500 == 0:
            refresh_krx_session(krx_id, krx_pw)

        tid = str(task["task_id"])
        sym = str(task["symbol"])
        year = int(task["year"])
        name = str(task.get("name", "") or "")

        merged_file = merged_path(base_dir, sym)
        if not merged_file.exists():
            result = McapTaskResult(task_id=tid, symbol=sym, year=year, ok=False, error="no_merged")
            report.results.append(result)
            report.skipped += 1
            append_enrich_task(
                base_dir,
                {
                    "at_iso": utc_now_iso(),
                    "task_id": tid,
                    "symbol": sym,
                    "year": year,
                    "step": MCAP_STEP,
                    "status": "skipped",
                    "error": result.error,
                },
            )
            continue

        payload = json.loads(merged_file.read_text(encoding="utf-8"))
        bars = list(payload.get("bars") or [])
        feat_file = features_path(base_dir, sym)

        try:
            mcap_df, method = fetch_market_cap_for_year(
                sym,
                year,
                bars,
                name=name,
                krx_id=krx_id,
                krx_pw=krx_pw,
                etf_symbols=etf_symbols,
            )
            if throttler is not None:
                throttler.after_request()

            if mcap_df.empty or method in ("empty", "failed"):
                err = f"no market cap ({method})"
                result = McapTaskResult(
                    task_id=tid, symbol=sym, year=year, ok=False, method=method, error=err
                )
                report.results.append(result)
                report.failed += 1
                fail_entry = {
                    "at_iso": utc_now_iso(),
                    "task_id": tid,
                    "symbol": sym,
                    "name": name,
                    "year": year,
                    "step": MCAP_STEP,
                    "status": "failed",
                    "method": method,
                    "row_count": 0,
                    "error": err,
                }
                append_enrich_task(base_dir, fail_entry)
                append_mcap_failure(base_dir, fail_entry)
                continue

            if sym not in feature_cache:
                if feat_file.exists():
                    feature_cache[sym] = read_features_parquet(feat_file)
                else:
                    feature_cache[sym] = pd.DataFrame(columns=["date"])

            feature_cache[sym] = _clear_mcap_for_year(feature_cache[sym], year)
            feature_cache[sym] = _merge_mcap_into_features(feature_cache[sym], mcap_df, method)
            write_features_parquet(feat_file, feature_cache[sym])

            result = McapTaskResult(
                task_id=tid,
                symbol=sym,
                year=year,
                ok=True,
                rows=len(mcap_df),
                method=method,
            )
            report.results.append(result)
            report.done += 1
            report.methods[method] = report.methods.get(method, 0) + 1
            append_enrich_task(
                base_dir,
                {
                    "at_iso": utc_now_iso(),
                    "task_id": tid,
                    "symbol": sym,
                    "year": year,
                    "step": MCAP_STEP,
                    "status": "done",
                    "method": method,
                    "row_count": len(mcap_df),
                    "error": "",
                },
            )
        except Exception as exc:
            result = McapTaskResult(
                task_id=tid, symbol=sym, year=year, ok=False, error=str(exc)
            )
            report.results.append(result)
            report.failed += 1
            fail_entry = {
                "at_iso": utc_now_iso(),
                "task_id": tid,
                "symbol": sym,
                "name": name,
                "year": year,
                "step": MCAP_STEP,
                "status": "failed",
                "row_count": 0,
                "error": str(exc),
            }
            append_enrich_task(base_dir, fail_entry)
            append_mcap_failure(base_dir, fail_entry)

    return report


def ensure_enrich_chunk_config(base_dir: Path) -> List[Dict[str, Any]]:
    path = enrich_chunk_config_path(base_dir)
    active = load_symbols_active(base_dir)
    syms = sorted(active.keys())
    return write_enrich_chunk_config(path, syms, test_count=50, prod_chunks=8)
