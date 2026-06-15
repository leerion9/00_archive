"""Task assignment: worker split (optional) and chunk bounds path helper."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

WORKER_IDS = frozenset({"pc", "laptop"})


def chunk_config_path(base_dir: Path) -> Path:
    return base_dir / "config" / "chunks.json"


def assign_worker(
    symbol: str,
    year: int,
    worker_id: str,
    *,
    pc_year_min: Optional[int] = None,
) -> bool:
    _ = symbol
    wid = str(worker_id or "").strip().lower()
    if wid not in WORKER_IDS:
        raise ValueError(f"worker_id must be one of {sorted(WORKER_IDS)}")

    y = int(year)
    if pc_year_min is None:
        return wid == "pc"

    cutoff = int(pc_year_min)
    if wid == "pc":
        return y >= cutoff
    return y < cutoff


def task_id(symbol: str, year: int) -> str:
    return f"{str(symbol).strip()}:{int(year)}"


def parse_task_id(task: str) -> tuple[str, int]:
    sym, year_text = str(task).split(":", maxsplit=1)
    return sym.strip(), int(year_text)
