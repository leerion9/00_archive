"""Validate merged/{symbol}.json against raw chunks (sample QA)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from core.archive_merge import (
    collect_year_chunk_paths,
    discover_raw_workers,
    load_collection_plan_years,
    load_symbols_active,
    merged_path,
    pick_newest_chunk,
)
from core.bar_merge import merge_bars


# Default 10-symbol panel: chunk 0~3, ETF, partial years, large cap, tail symbol.
DEFAULT_SAMPLE_SYMBOLS: tuple[str, ...] = (
    "005930",  # chunk0, full 7y, large cap
    "000020",  # chunk0 start
    "051910",  # chunk1
    "247540",  # chunk2
    "433880",  # chunk3 start
    "069500",  # ETF (KODEX 200)
    "279570",  # partial years (recent listing)
    "373220",  # LG에너지솔루션
    "214680",  # chunk2 mid
    "950210",  # chunk3 tail
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class SymbolValidation:
    symbol: str
    name: str
    ok: bool
    checks: List[CheckResult] = field(default_factory=list)
    bar_count: int = 0
    years_complete: List[int] = field(default_factory=list)
    years_pending: List[int] = field(default_factory=list)
    date_range: Dict[str, Optional[str]] = field(default_factory=dict)

    def failures(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.ok]


def _bar_key(bar: Dict[str, Any]) -> tuple:
    return (
        str(bar.get("date", "")),
        int(bar.get("open", 0) or 0),
        int(bar.get("high", 0) or 0),
        int(bar.get("low", 0) or 0),
        int(bar.get("close", 0) or 0),
        int(bar.get("volume", 0) or 0),
    )


def recompute_bars_from_raw(
    base_dir: Path,
    symbol: str,
    *,
    workers: Optional[Sequence[str]] = None,
) -> tuple[List[Dict[str, Any]], List[int], List[str]]:
    worker_ids = list(workers) if workers is not None else discover_raw_workers(base_dir)
    by_year = collect_year_chunk_paths(base_dir, symbol, worker_ids)
    warnings: List[str] = []
    selected: List[Dict[str, Any]] = []

    for year in sorted(by_year.keys()):
        chunk, chunk_warnings = pick_newest_chunk(by_year[year])
        warnings.extend(chunk_warnings)
        selected.append(chunk)

    bars: List[Dict[str, Any]] = []
    for chunk in sorted(selected, key=lambda c: str(c.get("fetched_at_iso", ""))):
        bars = merge_bars(bars, list(chunk.get("bars") or []))

    years_with_raw = sorted(by_year.keys(), reverse=True)
    return bars, years_with_raw, warnings


def validate_merged_symbol(
    base_dir: Path,
    symbol: str,
    *,
    years_planned: Optional[Sequence[int]] = None,
    name: str = "",
) -> SymbolValidation:
    sym = str(symbol).strip()
    years = list(years_planned) if years_planned is not None else load_collection_plan_years(base_dir)
    planned_set = {int(y) for y in years}

    if not name:
        name = load_symbols_active(base_dir).get(sym, "")

    checks: List[CheckResult] = []
    path = merged_path(base_dir, sym)

    if not path.exists():
        checks.append(CheckResult("merged_exists", False, f"missing {path}"))
        return SymbolValidation(symbol=sym, name=name, ok=False, checks=checks)

    merged = json.loads(path.read_text(encoding="utf-8"))
    checks.append(CheckResult("merged_exists", True, str(path)))

    checks.append(
        CheckResult(
            "symbol_match",
            str(merged.get("symbol", "")) == sym,
            f"merged={merged.get('symbol')} expected={sym}",
        )
    )
    checks.append(
        CheckResult(
            "schema_version",
            int(merged.get("schema_version", 0)) == 1,
            f"schema_version={merged.get('schema_version')}",
        )
    )
    checks.append(
        CheckResult(
            "price_volume_basis",
            merged.get("price_basis") == "adjusted" and merged.get("volume_basis") == "raw",
            f"price={merged.get('price_basis')} volume={merged.get('volume_basis')}",
        )
    )

    bars = list(merged.get("bars") or [])
    checks.append(
        CheckResult(
            "bar_count_match",
            int(merged.get("bar_count", -1)) == len(bars),
            f"header={merged.get('bar_count')} actual={len(bars)}",
        )
    )

    dates = [str(b.get("date", "")) for b in bars if b.get("date")]
    dr = merged.get("date_range") or {}
    if dates:
        expected_dr = {"from": min(dates), "to": max(dates)}
        checks.append(
            CheckResult(
                "date_range",
                dr.get("from") == expected_dr["from"] and dr.get("to") == expected_dr["to"],
                f"header={dr} expected={expected_dr}",
            )
        )
    else:
        checks.append(
            CheckResult(
                "date_range",
                dr.get("from") is None and dr.get("to") is None,
                f"header={dr}",
            )
        )

    years_complete = [int(y) for y in merged.get("years_complete") or []]
    years_pending = [int(y) for y in merged.get("years_pending") or []]
    complete_set = set(years_complete)
    pending_set = set(years_pending)

    checks.append(
        CheckResult(
            "years_partition",
            not (complete_set & pending_set)
            and (complete_set | pending_set) <= planned_set,
            f"complete={years_complete} pending={years_pending} planned={sorted(planned_set, reverse=True)}",
        )
    )

    _, years_with_raw, _ = recompute_bars_from_raw(base_dir, sym)
    expected_complete = sorted(set(years_with_raw) & planned_set, reverse=True)
    checks.append(
        CheckResult(
            "years_complete_vs_raw",
            years_complete == expected_complete,
            f"merged={years_complete} raw={expected_complete}",
        )
    )

    expected_pending = sorted(planned_set - set(expected_complete), reverse=True)
    checks.append(
        CheckResult(
            "years_pending_vs_raw",
            years_pending == expected_pending,
            f"merged={years_pending} expected={expected_pending}",
        )
    )

    recomputed, _, recompute_warnings = recompute_bars_from_raw(base_dir, sym)
    stored_keys = [_bar_key(b) for b in bars]
    recomputed_keys = [_bar_key(b) for b in recomputed]
    checks.append(
        CheckResult(
            "bars_match_raw",
            stored_keys == recomputed_keys,
            f"stored={len(stored_keys)} recomputed={len(recomputed_keys)}",
        )
    )

    fields = merged.get("fields") or {}
    for field_name in ("market_cap", "shares_outstanding", "trading_value"):
        meta = fields.get(field_name) or {}
        checks.append(
            CheckResult(
                f"fields_{field_name}_empty",
                meta.get("status") == "empty",
                f"status={meta.get('status')}",
            )
        )

    if recompute_warnings:
        checks.append(
            CheckResult(
                "no_duplicate_worker_chunks",
                False,
                "; ".join(recompute_warnings[:3]),
            )
        )
    else:
        checks.append(CheckResult("no_duplicate_worker_chunks", True, "none"))

    ok = all(c.ok for c in checks)
    return SymbolValidation(
        symbol=sym,
        name=name,
        ok=ok,
        checks=checks,
        bar_count=len(bars),
        years_complete=years_complete,
        years_pending=years_pending,
        date_range=dict(dr),
    )


def validate_sample_symbols(
    base_dir: Path,
    symbols: Sequence[str],
    *,
    years_planned: Optional[Sequence[int]] = None,
) -> List[SymbolValidation]:
    active = load_symbols_active(base_dir)
    return [
        validate_merged_symbol(
            base_dir,
            sym,
            years_planned=years_planned,
            name=active.get(str(sym).strip(), ""),
        )
        for sym in symbols
    ]
