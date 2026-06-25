"""Tests for market_cap_fetch (no pykrx network)."""

from __future__ import annotations

import pandas as pd

from core.market_cap_fetch import (
    build_etf_aum_frame,
    is_etf_or_etn,
    load_etf_etn_symbol_set,
)


def test_is_etf_or_etn_by_name_and_set():
    known = {"069500", "500023"}
    assert is_etf_or_etn("069500", "", known=known)
    assert is_etf_or_etn("005930", "KODEX 200", known=set())
    assert is_etf_or_etn("069660", "KIWOOM 200", known=set())
    assert not is_etf_or_etn("301410", "PLUS 코스닥150", known=set())
    assert is_etf_or_etn("500023", "신한 레버리지 ETN(H)", known=set())


def test_build_etf_aum_frame():
    nav = pd.DataFrame({"date": ["20240102", "20240103"], "nav": [100.0, 101.0]})
    shares = pd.DataFrame({"date": ["20240102", "20240103"], "shares_outstanding": [1000, 1000]})
    out = build_etf_aum_frame(nav, shares)
    assert len(out) == 2
    assert out.loc[out["date"] == "20240102", "market_cap"].iloc[0] == 100_000
    assert out.loc[out["date"] == "20240103", "market_cap"].iloc[0] == 101_000


def test_build_etf_aum_frame_inner_join():
    nav = pd.DataFrame({"date": ["20240102"], "nav": [100.0]})
    shares = pd.DataFrame({"date": ["20240103"], "shares_outstanding": [1000]})
    assert build_etf_aum_frame(nav, shares).empty


def test_parse_krx_number():
    from core.market_cap_fetch import _parse_krx_number

    assert _parse_krx_number("1,234,567") == 1234567
    import math
    assert math.isnan(_parse_krx_number("-"))


def test_load_etf_etn_symbol_set_no_crash():
    # Without KRX credentials this may return empty; must not raise.
    result = load_etf_etn_symbol_set("20260201")
    assert isinstance(result, set)
