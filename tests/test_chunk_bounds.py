"""Tests for core/chunk_bounds.py."""

from __future__ import annotations

from core.chunk_bounds import assign_chunk, split_symbols


def test_split_symbols_four_chunks():
    syms = [f"{i:06d}" for i in range(3947)]
    chunks = split_symbols(syms, 4)
    assert len(chunks) == 4
    assert chunks[0]["count"] == 1000
    assert chunks[1]["count"] == 1000
    assert chunks[2]["count"] == 1000
    assert chunks[3]["count"] == 947


def test_assign_chunk_by_range(tmp_path):
    cfg = tmp_path / "chunks.json"
    cfg.write_text(
        """
{
  "chunks": [
    {"chunk_id": 0, "from_symbol": "000010", "to_symbol": "000020", "count": 2},
    {"chunk_id": 1, "from_symbol": "000030", "to_symbol": "000040", "count": 2}
  ]
}
""".strip(),
        encoding="utf-8",
    )
    assert assign_chunk("000015", 0, cfg) is True
    assert assign_chunk("000025", 0, cfg) is False
    assert assign_chunk("000035", 1, cfg) is True
