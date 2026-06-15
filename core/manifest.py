"""Task manifest load/save and task picking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from core.chunk_bounds import assign_chunk
from core.shard import assign_worker


def load_tasks_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    tasks: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        tasks.append(json.loads(line))
    return tasks


def save_tasks_jsonl(path: Path, tasks: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(t, ensure_ascii=False) for t in tasks]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def append_progress(path: Path, entry: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def update_task_status(
    tasks: List[Dict[str, Any]],
    tid: str,
    status: str,
    *,
    error: str = "",
) -> None:
    for task in tasks:
        if str(task.get("task_id", "")) == tid:
            task["status"] = status
            if error:
                task["error"] = error
            elif "error" in task:
                del task["error"]
            return


def pick_pending_tasks(
    tasks: List[Dict[str, Any]],
    worker_id: str,
    *,
    max_tasks: int,
    pc_year_min: Optional[int] = None,
    chunk_id: Optional[int] = None,
    chunk_bounds_path: Optional[Path] = None,
    symbols_only: Optional[set[str]] = None,
    retry_failed: bool = False,
) -> List[Dict[str, Any]]:
    allowed = {"pending"}
    if retry_failed:
        allowed.add("failed")

    def _match(task: Dict[str, Any]) -> bool:
        if str(task.get("status", "")) not in allowed:
            return False
        sym = str(task.get("symbol", ""))
        if symbols_only is not None and sym not in symbols_only:
            return False
        year = int(task.get("year", 0))
        if not assign_worker(sym, year, worker_id, pc_year_min=pc_year_min):
            return False
        if chunk_id is not None and chunk_bounds_path is not None:
            return assign_chunk(sym, int(chunk_id), chunk_bounds_path)
        return True

    pending = [t for t in tasks if _match(t)]
    pending.sort(key=lambda t: int(t.get("priority", t.get("year", 0))), reverse=True)
    if max_tasks <= 0:
        return pending
    return pending[:max_tasks]
