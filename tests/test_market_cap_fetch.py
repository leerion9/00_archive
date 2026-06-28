"""Tests for market_cap_fetch (no pykrx network)."""

from __future__ import annotations

import pandas as pd

from core.market_cap_fetch import (
    MARKET_ETF_ETN,
    build_etf_aum_frame,
    is_etf_or_etn,
    load_etf_etn_symbol_set,
    should_use_etf_aum,
)


def test_is_etf_or_etn_by_name_and_set():
    known = {"069500", "500023"}
    assert is_etf_or_etn("069500", "", known=known)
    assert is_etf_or_etn("005930", "KODEX 200", known=set())
    assert is_etf_or_etn("069660", "KIWOOM 200", known=set())
    assert not is_etf_or_etn("301410", "PLUS 코스닥150", known=set())
    assert is_etf_or_etn("500023", "신한 레버리지 ETN(H)", known=set())


def test_should_use_etf_aum_listing_market_overrides_name():
    assert should_use_etf_aum("301410", "PLUS 코스닥150", listing_market=MARKET_ETF_ETN)
    assert not should_use_etf_aum("005930", "삼성전자", listing_market="KOSPI")
    assert should_use_etf_aum("500023", "신한 레버리지 ETN(H)", listing_market=MARKET_ETF_ETN)


def test_fetch_pykrx_etx_aum_routes_etn(monkeypatch):
    from core.market_cap_fetch import fetch_pykrx_etx_aum_krx

    calls: list[str] = []

    def fake_etf(sym, f, t):
        calls.append("etf")
        return pd.DataFrame()

    def fake_etn(sym, f, t):
        calls.append("etn")
        return pd.DataFrame({"date": ["20260102"], "market_cap": [1.0], "shares_outstanding": [1]})

    monkeypatch.setattr("core.market_cap_fetch.get_etx_kind", lambda s: "ETN")
    monkeypatch.setattr("core.market_cap_fetch.fetch_pykrx_etf_aum_krx", fake_etf)
    monkeypatch.setattr("core.market_cap_fetch.fetch_pykrx_etn_aum_krx", fake_etn)

    df = fetch_pykrx_etx_aum_krx("500020", "20260101", "20260131")
    assert len(df) == 1
    assert calls == ["etn"]


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
