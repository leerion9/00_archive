"""Tests for listing_events payload builder (no network)."""

from __future__ import annotations

from core.listing_events import build_listing_events_payload, validate_listing_events


def test_build_listing_events_payload_merges_active_and_delisted():
    active = {"005930": "삼성전자", "069500": "KODEX 200"}
    delisted = [
        {
            "symbol": "036490",
            "name": "상폐종목",
            "market": "KOSDAQ",
            "listing_date": "20100101",
            "delisting_date": "20211227",
            "reason": "자진상장폐지",
        }
    ]
    stock = {
        "005930": {"name": "삼성전자", "market": "KOSPI", "listing_date": "19750611", "source": "pykrx_stock"},
    }
    etf = {
        "069500": {"name": "KODEX 200", "market": "etf외", "listing_date": "20021014", "source": "pykrx_etf"},
    }
    payload = build_listing_events_payload(
        active_symbols=active,
        delisted_records=delisted,
        stock_listings=stock,
        etf_listings=etf,
    )
    symbols = payload["symbols"]
    assert len(symbols) == 3
    assert symbols["005930"]["status"] == "listed"
    assert symbols["036490"]["status"] == "delisted"
    assert symbols["036490"]["delisting_date"] == "20211227"
    errors = validate_listing_events(payload, expected_delisted=1, expected_total=3, delisted_symbols={"036490"})
    assert errors == []
