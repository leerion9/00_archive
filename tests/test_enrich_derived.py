"use Tests for core/enrich_derived.py."""

from __future__ import annotations

import json

import pandas as pd

from core.enrich_derived import (
    compute_derived_frame,
    enrich_symbol_derived,
    read_features_parquet,
)


def test_compute_derived_frame_ma5():
    bars = []
    for i, day in enumerate(["20260105", "20260106", "20260107", "20260108", "20260109"], start=1):
        bars.append(
            {
                "date": day,
                "open": 100 * i,
                "high": 100 * i,
                "low": 100 * i,
                "close": 100 * i,
                "volume": 10 * i,
            }
        )
    df = compute_derived_frame(bars)
    assert len(df) == 5
    assert pd.isna(df.loc[df["date"] == "20260105", "close_ma5"].iloc[0])
    assert df.loc[df["date"] == "20260109", "close_ma5"].iloc[0] == 300.0
    assert df.loc[df["date"] == "20260109", "trading_value"].iloc[0] == 500 * 50


def test_enrich_symbol_derived_writes_parquet(tmp_path):
    base = tmp_path
    (base / "config").mkdir(parents=True)
    (base / "config" / "collection_plan.json").write_text(
        json.dumps({"years": [2026]}),
        encoding="utf-8",
    )
    (base / "merged").mkdir(parents=True)
    bars = [
        {"date": f"2026010{d}", "open": 1, "high": 1, "low": 1, "close": d, "volume": 10}
        for d in range(1, 7)
    ]
    (base / "merged" / "005930.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "symbol": "005930",
                "bars": bars,
                "updated_at_iso": "2026-06-24T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    result = enrich_symbol_derived(base, "005930", years=[2026])
    assert result.ok
    assert result.features_path.exists()
    df = read_features_parquet(result.features_path)
    assert len(df) == 6
    assert "trading_value" in df.columns
