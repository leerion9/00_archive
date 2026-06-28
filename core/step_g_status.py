"""Step G status analysis — delisted universe + mcap task taxonomy."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.archive_merge import merged_path
from core.enrich_derived import features_path
from core.listing_events import delisted_master_path, listing_events_path, load_delisted_master
from core.mcap_taxonomy import G3_YEARS, analyze_mcap_taxonomy, load_latest_mcap_tasks
from core.post_delist_verify import run_post_delist_spot_check


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_delisted_symbols(base_dir: Path) -> List[str]:
    records = load_delisted_master(delisted_master_path(base_dir))
    return sorted({str(r["symbol"]).strip().zfill(6) for r in records})


def analyze_g2_tasks(base_dir: Path) -> Dict[str, Any]:
    path = base_dir / "manifest" / "tasks_delisted.jsonl"
    if not path.exists():
        return {"exists": False}
    counts: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        counts[str(row.get("status") or "unknown")] += 1
    return {"exists": True, "tasks_total": sum(counts.values()), "status_counts": dict(counts)}


def analyze_sidecar_coverage(base_dir: Path, symbols: Sequence[str]) -> Dict[str, int]:
    merged_n = features_n = 0
    for sym in symbols:
        s = str(sym).strip().zfill(6)
        if merged_path(base_dir, s).exists():
            merged_n += 1
        if features_path(base_dir, s).exists():
            features_n += 1
    return {
        "symbols": len(symbols),
        "merged": merged_n,
        "features": features_n,
    }


def load_g3_mcap_reports(base_dir: Path) -> List[Dict[str, Any]]:
    reports_dir = base_dir / "reports"
    if not reports_dir.exists():
        return []
    out: List[Dict[str, Any]] = []
    for path in sorted(reports_dir.glob("enrich_market_cap_g3_c*.json")):
        data = _load_json(path) or {}
        out.append(
            {
                "file": path.name,
                "chunk_id": data.get("chunk_id"),
                "at_iso": data.get("at_iso"),
                "done": data.get("done"),
                "failed": data.get("failed"),
                "skipped": data.get("skipped"),
                "skipped_expected": data.get("skipped_expected"),
                "expected_blank": data.get("expected_blank"),
                "methods": data.get("methods"),
            }
        )
    return out


def analyze_step_g(base_dir: Path) -> Dict[str, Any]:
    symbols = load_delisted_symbols(base_dir)
    listing = _load_json(listing_events_path(base_dir)) or {}
    listing_symbols = listing.get("symbols") or {}

    mcap = analyze_mcap_taxonomy(base_dir, symbols)
    post_delist = run_post_delist_spot_check(base_dir, symbols).to_dict()

    delisted_in_events = sum(
        1 for sym in symbols if (listing_symbols.get(sym) or {}).get("status") == "delisted"
    )

    return {
        "schema_version": 1,
        "delisted_symbols": len(symbols),
        "listing_events_delisted": delisted_in_events,
        "g2_tasks": analyze_g2_tasks(base_dir),
        "sidecar": analyze_sidecar_coverage(base_dir, symbols),
        "mcap_taxonomy": mcap,
        "g3_mcap_reports_legacy": load_g3_mcap_reports(base_dir),
        "post_delist_spot": {
            "ok": post_delist.get("ok"),
            "anomaly": post_delist.get("anomaly"),
            "skipped": post_delist.get("skipped"),
            "sample_size": post_delist.get("sample_size"),
        },
    }
