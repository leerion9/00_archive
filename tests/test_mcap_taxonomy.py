"""Tests for mcap taxonomy relabeling."""

from __future__ import annotations

import json
from pathlib import Path

from core.mcap_taxonomy import analyze_mcap_taxonomy, summarize_relabel_delta


def _setup(base: Path, symbols: dict, tasks: list[dict]) -> None:
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text("{}", encoding="utf-8")
    path = base / "master" / "listing_events.json"
    path.write_text(json.dumps({"symbols": symbols}, ensure_ascii=False), encoding="utf-8")
    (base / "merged").mkdir(parents=True)
    for sym in symbols:
        (base / "merged" / f"{sym}.json").write_text('{"bars": []}', encoding="utf-8")
    tasks_path = base / "manifest" / "enrich_tasks.jsonl"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text("\n".join(json.dumps(t) for t in tasks), encoding="utf-8")


def test_summarize_relabel_delta():
    legacy = {"complete_7yr": 5, "partial": 2, "none": 1}
    relabeled = {
        "symbol_tradable_complete": 6,
        "symbol_tradable_partial": 1,
        "symbol_tradable_none": 1,
        "symbol_skipped_only": 0,
        "task_counts": {"skipped_expected": 3, "failed": 1},
        "legacy_failed_reclassified_to_skipped_expected": 2,
    }
    delta = summarize_relabel_delta(legacy, relabeled)
    assert delta["legacy_partial"] == 2
    assert delta["relabeled_tradable_complete"] == 6
    assert delta["task_skipped_expected"] == 3


def test_analyze_mcap_taxonomy_skips_pre_listing_year(tmp_path: Path):
    base = tmp_path / "data"
    _setup(
        base,
        {
            "279570": {
                "listing_date": "20230101",
                "delisting_date": None,
                "status": "listed",
            }
        },
        [
            {"task_id": "279570:2022", "step": "market_cap", "status": "failed"},
            {"task_id": "279570:2023", "step": "market_cap", "status": "done", "method": "pykrx_mcap"},
        ],
    )
    out = analyze_mcap_taxonomy(base, ["279570"], years=[2022, 2023])
    assert out["task_counts"]["skipped_expected"] == 1
    assert out["task_counts"]["done"] == 1
    assert out["legacy_failed_reclassified_to_skipped_expected"] == 1
    assert out["symbol_tradable_complete"] == 1
