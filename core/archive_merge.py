"""Merge raw year chunks into per-symbol merged JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from core.archive_schema import (
    PRICE_BASIS,
    SCHEMA_VERSION,
    SOURCE,
    VOLUME_BASIS,
    read_chunk,
    utc_now_iso,
)
from core.bar_merge import merge_bars
from core.shard import WORKER_IDS

try:
    from core.listing_events import delisted_master_path, load_delisted_master
except ImportError:
    delisted_master_path = None  # type: ignore
    load_delisted_master = None  # type: ignore


def merged_path(base_dir: Path, symbol: str) -> Path:
    return base_dir / "merged" / f"{str(symbol).strip()}.json"


def load_collection_plan_years(base_dir: Path) -> List[int]:
    path = base_dir / "config" / "collection_plan.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return sorted({int(y) for y in raw.get("years", [])}, reverse=True)


def load_symbols_active(base_dir: Path) -> Dict[str, str]:
    path = base_dir / "master" / "symbols_active.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: Dict[str, str] = {}
    for item in raw.get("symbols", []):
        sym = str(item.get("symbol", "")).strip()
        if sym:
            out[sym] = str(item.get("name", "") or "")
    return out


def discover_raw_workers(base_dir: Path) -> List[str]:
    raw_root = base_dir / "raw"
    if not raw_root.is_dir():
        return []
    workers = []
    for child in sorted(raw_root.iterdir()):
        if child.is_dir() and child.name.lower() in WORKER_IDS:
            workers.append(child.name.lower())
    return workers


def collect_year_chunk_paths(base_dir: Path, symbol: str, workers: Sequence[str]) -> Dict[int, List[Path]]:
    sym = str(symbol).strip()
    by_year: Dict[int, List[Path]] = {}
    for worker_id in workers:
        sym_dir = base_dir / "raw" / worker_id / sym
        if not sym_dir.is_dir():
            continue
        for path in sym_dir.glob("*.json"):
            try:
                year = int(path.stem)
            except ValueError:
                continue
            by_year.setdefault(year, []).append(path)
    return by_year


def pick_newest_chunk(paths: List[Path]) -> tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []
    loaded: List[tuple[str, Dict[str, Any]]] = []
    for path in paths:
        payload = read_chunk(path)
        fetched = str(payload.get("fetched_at_iso", "") or "")
        loaded.append((fetched, payload))

    if len(loaded) > 1:
        workers = sorted({str(p.get("worker_id", "")) for _, p in loaded})
        years = sorted({int(p.get("year", 0)) for _, p in loaded})
        year = years[0] if years else 0
        sym = str(loaded[0][1].get("symbol", ""))
        warnings.append(
            f"duplicate chunk {sym}:{year} across workers {workers}; "
            f"using newest fetched_at_iso"
        )

    loaded.sort(key=lambda item: item[0])
    return loaded[-1][1], warnings


def empty_fields_meta() -> Dict[str, Dict[str, Optional[str]]]:
    empty = {"status": "empty", "source": None, "updated_at": None}
    return {
        "market_cap": dict(empty),
        "shares_outstanding": dict(empty),
        "trading_value": dict(empty),
    }


def build_merged_payload(
    *,
    symbol: str,
    name: str,
    bars: List[Dict[str, Any]],
    years_complete: List[int],
    years_pending: List[int],
    chunk_sources: List[Dict[str, Any]],
) -> Dict[str, Any]:
    dates = [str(b.get("date", "")) for b in bars if b.get("date")]
    date_range: Dict[str, Optional[str]] = {"from": None, "to": None}
    if dates:
        date_range = {"from": min(dates), "to": max(dates)}

    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": str(symbol).strip(),
        "name": str(name or ""),
        "source": SOURCE,
        "price_basis": PRICE_BASIS,
        "volume_basis": VOLUME_BASIS,
        "updated_at_iso": utc_now_iso(),
        "years_complete": sorted(years_complete, reverse=True),
        "years_pending": sorted(years_pending, reverse=True),
        "bar_count": len(bars),
        "date_range": date_range,
        "chunk_sources": chunk_sources,
        "bars": bars,
        "fields": empty_fields_meta(),
    }


def write_merged(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class SymbolMergeResult:
    symbol: str
    name: str
    merged_path: Optional[Path] = None
    bar_count: int = 0
    years_complete: List[int] = field(default_factory=list)
    years_pending: List[int] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class MergeRunReport:
    at_iso: str
    years_planned: List[int]
    symbols_total: int
    merged: int = 0
    skipped_no_raw: int = 0
    warnings: List[str] = field(default_factory=list)
    symbols: List[SymbolMergeResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "at_iso": self.at_iso,
            "years_planned": self.years_planned,
            "symbols_total": self.symbols_total,
            "merged": self.merged,
            "skipped_no_raw": self.skipped_no_raw,
            "warning_count": len(self.warnings),
            "warnings": self.warnings[:200],
            "symbols": [
                {
                    "symbol": s.symbol,
                    "name": s.name,
                    "merged_path": str(s.merged_path) if s.merged_path else None,
                    "bar_count": s.bar_count,
                    "years_complete": s.years_complete,
                    "years_pending": s.years_pending,
                    "skipped": s.skipped,
                    "skip_reason": s.skip_reason,
                    "warnings": s.warnings,
                }
                for s in self.symbols
            ],
        }


def merge_symbol(
    base_dir: Path,
    symbol: str,
    name: str,
    *,
    years_planned: Sequence[int],
    workers: Optional[Sequence[str]] = None,
) -> SymbolMergeResult:
    sym = str(symbol).strip()
    worker_ids = list(workers) if workers is not None else discover_raw_workers(base_dir)
    by_year = collect_year_chunk_paths(base_dir, sym, worker_ids)

    if not by_year:
        return SymbolMergeResult(
            symbol=sym,
            name=name,
            skipped=True,
            skip_reason="no_raw_chunks",
            years_pending=sorted(years_planned, reverse=True),
        )

    planned = {int(y) for y in years_planned}
    years_complete: List[int] = []
    warnings: List[str] = []
    selected_chunks: List[Dict[str, Any]] = []
    chunk_sources: List[Dict[str, Any]] = []

    for year in sorted(by_year.keys(), reverse=True):
        paths = by_year[year]
        chunk, chunk_warnings = pick_newest_chunk(paths)
        warnings.extend(chunk_warnings)
        selected_chunks.append(chunk)
        if year in planned:
            years_complete.append(year)
        chunk_sources.append(
            {
                "year": year,
                "worker_id": chunk.get("worker_id"),
                "fetched_at_iso": chunk.get("fetched_at_iso"),
                "bar_count": chunk.get("bar_count", 0),
                "path": str(paths[0].relative_to(base_dir)) if len(paths) == 1 else None,
            }
        )

    bars: List[Dict[str, Any]] = []
    for chunk in sorted(selected_chunks, key=lambda c: str(c.get("fetched_at_iso", ""))):
        bars = merge_bars(bars, list(chunk.get("bars") or []))

    years_pending = sorted(planned - set(years_complete), reverse=True)
    payload = build_merged_payload(
        symbol=sym,
        name=name,
        bars=bars,
        years_complete=years_complete,
        years_pending=years_pending,
        chunk_sources=chunk_sources,
    )
    out_path = merged_path(base_dir, sym)
    write_merged(out_path, payload)

    return SymbolMergeResult(
        symbol=sym,
        name=name,
        merged_path=out_path,
        bar_count=len(bars),
        years_complete=years_complete,
        years_pending=years_pending,
        warnings=warnings,
    )


def _delisted_name_map(base_dir: Path) -> Dict[str, str]:
    if load_delisted_master is None or delisted_master_path is None:
        return {}
    path = delisted_master_path(base_dir)
    if not path.exists():
        return {}
    return {str(r["symbol"]).zfill(6): str(r.get("name") or "") for r in load_delisted_master(path)}


def merge_all(
    base_dir: Path,
    *,
    years_planned: Optional[Sequence[int]] = None,
    symbols: Optional[Sequence[str]] = None,
) -> MergeRunReport:
    years = list(years_planned) if years_planned is not None else load_collection_plan_years(base_dir)
    if not years:
        raise ValueError("years_planned is empty; pass --years or write config/collection_plan.json")

    active = load_symbols_active(base_dir)
    delisted_names = _delisted_name_map(base_dir)
    workers = discover_raw_workers(base_dir)

    raw_symbols: set[str] = set()
    for worker_id in workers:
        worker_dir = base_dir / "raw" / worker_id
        if worker_dir.is_dir():
            raw_symbols.update(p.name for p in worker_dir.iterdir() if p.is_dir())

    if symbols is not None:
        target_symbols = sorted({str(s).strip() for s in symbols if str(s).strip()})
    else:
        target_symbols = sorted(set(active.keys()) | raw_symbols)

    report = MergeRunReport(
        at_iso=utc_now_iso(),
        years_planned=sorted(years, reverse=True),
        symbols_total=len(target_symbols),
    )

    for sym in target_symbols:
        name = active.get(sym, "") or delisted_names.get(sym, "")
        result = merge_symbol(
            base_dir,
            sym,
            name,
            years_planned=years,
            workers=workers,
        )
        report.symbols.append(result)
        if result.skipped:
            report.skipped_no_raw += 1
        else:
            report.merged += 1
            report.warnings.extend(result.warnings)

    return report
