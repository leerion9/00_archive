"""Symbol chunk bounds: sorted codes split into N contiguous blocks (~1000 each)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def split_symbols(sorted_symbols: List[str], num_chunks: int = 4) -> List[Dict[str, Any]]:
    """Split sorted symbol list into contiguous chunks (~1000 for first blocks when num_chunks=4)."""
    syms = [str(s).strip() for s in sorted_symbols if str(s).strip()]
    n = len(syms)
    nc = max(1, int(num_chunks))
    chunks: List[Dict[str, Any]] = []

    if nc == 4 and n > 3000:
        cuts = [0, 1000, 2000, 3000, n]
    else:
        q, r = divmod(n, nc)
        cuts = [0]
        for i in range(nc):
            cuts.append(cuts[-1] + q + (1 if i < r else 0))

    for cid in range(nc):
        start, end = cuts[cid], cuts[cid + 1]
        block = syms[start:end]
        if not block:
            continue
        chunks.append(
            {
                "chunk_id": cid,
                "from_symbol": block[0],
                "to_symbol": block[-1],
                "count": len(block),
            }
        )
    return chunks


def write_chunk_config(path: Path, sorted_symbols: List[str], num_chunks: int = 4) -> List[Dict[str, Any]]:
    chunks = split_symbols(sorted_symbols, num_chunks)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "num_chunks": num_chunks,
        "total_symbols": len(sorted_symbols),
        "chunks": chunks,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return chunks


def load_chunk_config(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def assign_chunk(symbol: str, chunk_id: int, bounds_path: Path) -> bool:
    """True if symbol falls in chunk_id range (inclusive, sorted 6-digit codes)."""
    sym = str(symbol).strip()
    cfg = load_chunk_config(bounds_path)
    if not cfg:
        return False
    cid = int(chunk_id)
    for row in cfg.get("chunks", []):
        if int(row.get("chunk_id", -1)) != cid:
            continue
        return str(row["from_symbol"]) <= sym <= str(row["to_symbol"])
    return False
