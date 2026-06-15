"""Archive JSON schema helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.shard import task_id

SCHEMA_VERSION = 1
SOURCE = "naver_sise_day"
PRICE_BASIS = "adjusted"
VOLUME_BASIS = "raw"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def raw_chunk_path(base_dir: Path, worker_id: str, symbol: str, year: int) -> Path:
    return base_dir / "raw" / worker_id / str(symbol).strip() / f"{int(year)}.json"


def build_chunk_payload(
    *,
    symbol: str,
    year: int,
    worker_id: str,
    bars: List[Dict],
    pages_fetched: List[int],
    end_date: str = "",
) -> Dict[str, Any]:
    dates = [str(b.get("date", "")) for b in bars if b.get("date")]
    date_range: Dict[str, Optional[str]] = {"from": None, "to": None}
    if dates:
        date_range = {"from": min(dates), "to": max(dates)}

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id(symbol, year),
        "symbol": str(symbol).strip(),
        "year": int(year),
        "source": SOURCE,
        "price_basis": PRICE_BASIS,
        "volume_basis": VOLUME_BASIS,
        "worker_id": str(worker_id).strip().lower(),
        "fetched_at_iso": utc_now_iso(),
        "pages_fetched": pages_fetched,
        "bar_count": len(bars),
        "date_range": date_range,
        "end_date_cap": str(end_date or "").strip() or None,
        "bars": bars,
    }


def write_chunk(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_chunk(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
