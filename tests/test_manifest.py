"""Tests for core/manifest.py."""

from __future__ import annotations

from core.manifest import pick_pending_tasks, update_task_status


def _tasks():
    return [
        {"task_id": "005930:2026", "symbol": "005930", "year": 2026, "status": "pending"},
        {"task_id": "005931:2026", "symbol": "005931", "year": 2026, "status": "done"},
        {"task_id": "005932:2015", "symbol": "005932", "year": 2015, "status": "pending"},
    ]


def test_pick_pending_pc_only():
    picked = pick_pending_tasks(_tasks(), "pc", max_tasks=10, pc_year_min=None)
    assert [t["task_id"] for t in picked] == ["005930:2026", "005932:2015"]


def test_pick_pending_year_split():
    picked = pick_pending_tasks(_tasks(), "laptop", max_tasks=10, pc_year_min=2016)
    assert [t["task_id"] for t in picked] == ["005932:2015"]


def test_pick_pending_by_chunk(tmp_path):
    cfg = tmp_path / "chunks.json"
    cfg.write_text(
        """
{
  "chunks": [
    {"chunk_id": 0, "from_symbol": "005930", "to_symbol": "005930", "count": 1},
    {"chunk_id": 1, "from_symbol": "005931", "to_symbol": "005931", "count": 1}
  ]
}
""".strip(),
        encoding="utf-8",
    )
    tasks = [
        {"task_id": "005930:2025", "symbol": "005930", "year": 2025, "status": "pending"},
        {"task_id": "005931:2025", "symbol": "005931", "year": 2025, "status": "pending"},
    ]
    picked = pick_pending_tasks(
        tasks, "pc", max_tasks=10, chunk_id=0, chunk_bounds_path=cfg
    )
    assert len(picked) == 1
    assert picked[0]["symbol"] == "005930"


def test_update_task_status():
    tasks = _tasks()
    update_task_status(tasks, "005930:2026", "failed", error="timeout")
    assert tasks[0]["status"] == "failed"
    assert tasks[0]["error"] == "timeout"
