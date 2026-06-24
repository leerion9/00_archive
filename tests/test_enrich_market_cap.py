"""Tests for market cap enrich merge."""

from __future__ import annotations

import pandas as pd

from core.enrich_market_cap import _merge_mcap_into_features


def test_merge_mcap_accumulates_years():
    base = pd.DataFrame(
        {
            "date": ["20200102", "20210104"],
            "trading_value": [1, 2],
        }
    )
    y2020 = pd.DataFrame({"date": ["20200102"], "market_cap": [100], "shares_outstanding": [10]})
    merged = _merge_mcap_into_features(base, y2020, "pykrx_mcap")
    y2021 = pd.DataFrame({"date": ["20210104"], "market_cap": [200], "shares_outstanding": [10]})
    merged = _merge_mcap_into_features(merged, y2021, "pykrx_mcap")
    assert merged.loc[merged["date"] == "20200102", "market_cap"].iloc[0] == 100
    assert merged.loc[merged["date"] == "20210104", "market_cap"].iloc[0] == 200
