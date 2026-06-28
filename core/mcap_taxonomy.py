"""Market cap task taxonomy using listing_window + enrich_tasks manifest."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.enrich_market_cap import build_mcap_tasks
from core.archive_merge import merged_path
from core.listing_events import listing_events_path

G3_YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]
PHASE1_YEARS = list(G3_YEARS)
GOOD_MCAP_METHODS = frozenset({"pykrx_mcap", "etf_aum"})
TRADABLE_SUCCESS = frozenset({"done", "expected_blank"})


def load_latest_mcap_tasks(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    path = base_dir / "manifest" / "enrich_tasks.jsonl"
    latest: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return latest
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("step") != "market_cap":
            continue
        latest[str(row["task_id"])] = row
    return latest


def _year_has_bars(base_dir: Path, symbol: str, year: int) -> bool:
    path = merged_path(base_dir, str(symbol).strip().zfill(6))
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    prefix = str(int(year))
    return any(str(b.get("date", "")).startswith(prefix) for b in payload.get("bars") or [])


def classify_mcap_task(
    planned: Dict[str, Any],
    latest: Dict[str, Dict[str, Any]],
    *,
    base_dir: Path | None = None,
) -> str:
    if planned.get("status") == "skipped_expected":
        return "skipped_expected"
    tid = str(planned["task_id"])
    row = latest.get(tid)
    if not row:
        return "pending"
    status = str(row.get("status") or "")
    method = row.get("method")
    error = str(row.get("error") or "")
    if (
        base_dir is not None
        and status == "failed"
        and ("empty" in error or method == "empty")
        and not _year_has_bars(base_dir, str(planned["symbol"]), int(planned["year"]))
    ):
        return "expected_blank"
    if status == "done" and method in GOOD_MCAP_METHODS:
        return "done"
    if status in {"skipped_expected", "expected_blank"}:
        return status
    if status == "done":
        return "done"
    if status == "failed":
        return "failed"
    return status or "pending"


def _symbol_tradable_summary(
    symbols: Sequence[str],
    planned_tasks: Sequence[Dict[str, Any]],
    latest: Dict[str, Dict[str, Any]],
    *,
    base_dir: Path | None = None,
) -> Dict[str, Any]:
    tradable_by_symbol: Dict[str, List[str]] = defaultdict(list)
    for planned in planned_tasks:
        sym = str(planned["symbol"]).strip().zfill(6)
        if planned.get("status") == "skipped_expected":
            continue
        tradable_by_symbol[sym].append(
            classify_mcap_task(planned, latest, base_dir=base_dir)
        )

    complete_n = partial_n = none_n = skipped_only_n = 0
    partial_symbols: List[Dict[str, Any]] = []
    none_symbols: List[str] = []

    for sym in symbols:
        s = str(sym).strip().zfill(6)
        classes = tradable_by_symbol.get(s, [])
        if not classes:
            skipped_only_n += 1
            continue
        done_n = sum(1 for c in classes if c in TRADABLE_SUCCESS)
        failed_n = sum(1 for c in classes if c == "failed")
        pending_n = sum(1 for c in classes if c == "pending")
        if done_n == len(classes):
            complete_n += 1
        elif done_n == 0:
            none_n += 1
            none_symbols.append(s)
        else:
            partial_n += 1
            partial_symbols.append(
                {
                    "symbol": s,
                    "tradable_years": len(classes),
                    "done": done_n,
                    "failed": failed_n,
                    "pending": pending_n,
                }
            )

    return {
        "symbol_tradable_complete": complete_n,
        "symbol_tradable_partial": partial_n,
        "symbol_tradable_none": none_n,
        "symbol_skipped_only": skipped_only_n,
        "partial_symbols": partial_symbols,
        "none_symbols": none_symbols,
    }


def analyze_mcap_taxonomy(
    base_dir: Path,
    symbols: Sequence[str],
    *,
    years: Sequence[int] = G3_YEARS,
    open_task_limit: int = 30,
    partial_limit: int = 20,
    none_limit: int = 20,
) -> Dict[str, Any]:
    planned_tasks = build_mcap_tasks(base_dir, years=years, symbols=symbols)
    latest = load_latest_mcap_tasks(base_dir)

    task_counts: Counter[str] = Counter()
    legacy_failed_reclassified = 0
    per_task: List[Dict[str, Any]] = []

    for planned in planned_tasks:
        tid = str(planned["task_id"])
        classified = classify_mcap_task(planned, latest, base_dir=base_dir)
        task_counts[classified] += 1
        actual = latest.get(tid) or {}
        if classified == "skipped_expected" and str(actual.get("status") or "") == "failed":
            legacy_failed_reclassified += 1
        if (
            classified == "expected_blank"
            and str(actual.get("status") or "") == "failed"
        ):
            legacy_failed_reclassified += 1
        if classified in {"failed", "pending"}:
            per_task.append(
                {
                    "task_id": tid,
                    "symbol": planned["symbol"],
                    "year": planned["year"],
                    "classified": classified,
                    "logged_status": actual.get("status"),
                    "method": actual.get("method"),
                    "error": actual.get("error"),
                }
            )

    sym_summary = _symbol_tradable_summary(symbols, planned_tasks, latest, base_dir=base_dir)
    return {
        "years": list(years),
        "listing_events": listing_events_path(base_dir).exists(),
        "tasks_total": len(planned_tasks),
        "task_counts": dict(task_counts),
        "legacy_failed_reclassified_to_skipped_expected": legacy_failed_reclassified,
        "open_tasks": per_task[:open_task_limit],
        **sym_summary,
        "partial_symbols": sym_summary["partial_symbols"][:partial_limit],
        "none_symbols": sym_summary["none_symbols"][:none_limit],
        "open_tasks_sample": per_task[:open_task_limit],
    }


def summarize_relabel_delta(legacy: Dict[str, int], relabeled: Dict[str, Any]) -> Dict[str, Any]:
    """Compare legacy 7yr partial/none vs listing_window tradable taxonomy."""
    task_counts = relabeled.get("task_counts") or {}
    return {
        "legacy_complete_7yr": legacy.get("complete_7yr", 0),
        "legacy_partial": legacy.get("partial", 0),
        "legacy_none": legacy.get("none", 0),
        "relabeled_tradable_complete": relabeled.get("symbol_tradable_complete", 0),
        "relabeled_tradable_partial": relabeled.get("symbol_tradable_partial", 0),
        "relabeled_tradable_none": relabeled.get("symbol_tradable_none", 0),
        "relabeled_skipped_only": relabeled.get("symbol_skipped_only", 0),
        "task_skipped_expected": task_counts.get("skipped_expected", 0),
        "task_failed_tradable": task_counts.get("failed", 0),
        "legacy_failed_reclassified": relabeled.get(
            "legacy_failed_reclassified_to_skipped_expected", 0
        ),
    }
