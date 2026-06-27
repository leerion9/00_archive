"""Tests for core/enrich_market.py."""

from __future__ import annotations

import json

import pandas as pd

from core.enrich_derived import write_features_parquet
from core.enrich_market import MARKET_ETF_ETN, _merge_market_into_features, enrich_symbol_market


def test_merge_market_into_features():
    base = pd.DataFrame({"date": ["20260102", "20260103"], "trading_value": [1, 2]})
    membership = {
        "20260102": {"005930": "KOSPI"},
        "20260103": {"005930": "KOSPI"},
    }
    merged, unknown = _merge_market_into_features(base, "005930", membership)
    assert unknown == 0
    assert merged.loc[merged["date"] == "20260102", "market"].iloc[0] == "KOSPI"


def test_merge_market_etf_etn_label():
    base = pd.DataFrame({"date": ["20260102", "20260103"], "trading_value": [1, 2]})
    merged, unknown = _merge_market_into_features(base, "069500", {}, etf_etn=True)
    assert unknown == 0
    assert (merged["market"] == "etf외").all()


def test_merge_market_unknown_symbol():
    base = pd.DataFrame({"date": ["20260102"], "trading_value": [1]})
    membership = {"20260102": {"005930": "KOSPI"}}
    merged, unknown = _merge_market_into_features(base, "999999", membership)
    assert unknown == 1
    assert pd.isna(merged.loc[0, "market"])


def test_enrich_symbol_market_writes_market(tmp_path):
    base = tmp_path
    (base / "merged").mkdir(parents=True)
    (base / "merged" / "005930.json").write_text(
        json.dumps({"symbol": "005930", "bars": [{"date": "20260102", "close": 1, "volume": 1}]}),
        encoding="utf-8",
    )
    write_features_parquet(
        base / "features" / "005930.parquet",
        pd.DataFrame({"date": ["20260102"], "trading_value": [1], "value_ma5": [None], "close_ma5": [None]}),
    )
    membership = {"20260102": {"005930": "KOSPI"}}
    result = enrich_symbol_market(base, "005930", years=[2026], membership_by_date=membership)
    assert result.ok
    assert result.market_rows == 1
