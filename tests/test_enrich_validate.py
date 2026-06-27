"""Tests for core/enrich_validate.py."""

from __future__ import annotations

import json

import pandas as pd

from core.enrich_derived import write_features_parquet
from core.enrich_validate import validate_derived_symbol


def test_validate_derived_allows_step_c_columns(tmp_path):
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

    derived = pd.DataFrame(
        {
            "date": [f"2026010{d}" for d in range(1, 7)],
            "trading_value": [d * 10 for d in range(1, 7)],
            "value_ma5": [None] * 4 + [30.0, 40.0],
            "close_ma5": [None] * 4 + [3.0, 4.0],
            "market_cap": [1000] * 6,
            "market_cap_method": ["pykrx_mcap"] * 6,
            "market": ["KOSPI"] * 6,
        }
    )
    write_features_parquet(base / "features" / "005930.parquet", derived)

    result = validate_derived_symbol(base, "005930", years=[2026])
    assert result.ok
    assert all(c.ok for c in result.checks if c.name == "columns")


def test_validate_derived_allows_market_column_only(tmp_path):
    base = tmp_path
    (base / "config").mkdir(parents=True)
    (base / "config" / "collection_plan.json").write_text(
        json.dumps({"years": [2026]}),
        encoding="utf-8",
    )
    (base / "merged").mkdir(parents=True)
    bars = [{"date": "20260102", "open": 1, "high": 1, "low": 1, "close": 2, "volume": 10}]
    (base / "merged" / "005930.json").write_text(
        json.dumps({"schema_version": 1, "symbol": "005930", "bars": bars}),
        encoding="utf-8",
    )
    derived = pd.DataFrame(
        {
            "date": ["20260102"],
            "trading_value": [20],
            "value_ma5": [None],
            "close_ma5": [None],
            "market": ["KOSPI"],
        }
    )
    write_features_parquet(base / "features" / "005930.parquet", derived)
    result = validate_derived_symbol(base, "005930", years=[2026])
    assert result.ok
