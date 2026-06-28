"""Tests for Step G status analysis."""

from __future__ import annotations

import json
from pathlib import Path

from core.mcap_taxonomy import analyze_mcap_taxonomy, classify_mcap_task


def _write_listing_events(base: Path) -> None:
    path = base / "master" / "listing_events.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "symbols": {
                    "036490": {
                        "listing_date": "20100101",
                        "delisting_date": "20211227",
                        "status": "delisted",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_classify_mcap_task_reclassifies_skipped_expected(tmp_path: Path):
    planned = {"task_id": "036490:2022", "status": "skipped_expected"}
    latest = {
        "036490:2022": {"status": "failed", "step": "market_cap"},
    }
    assert classify_mcap_task(planned, latest) == "skipped_expected"


def test_analyze_mcap_taxonomy_counts(tmp_path: Path):
    base = tmp_path / "data"
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text("{}", encoding="utf-8")
    _write_listing_events(base)
    (base / "merged").mkdir(parents=True)
    (base / "merged" / "036490.json").write_text('{"bars": []}', encoding="utf-8")

    tasks_path = base / "manifest" / "enrich_tasks.jsonl"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"task_id": "036490:2021", "step": "market_cap", "status": "done", "method": "pykrx_mcap"},
        {"task_id": "036490:2022", "step": "market_cap", "status": "failed"},
    ]
    tasks_path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    out = analyze_mcap_taxonomy(base, ["036490"], years=[2021, 2022])
    assert out["tasks_total"] == 2
    assert out["task_counts"]["done"] == 1
    assert out["task_counts"]["skipped_expected"] == 1
    assert out["legacy_failed_reclassified_to_skipped_expected"] == 1
