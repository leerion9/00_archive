"""Tests for delisted_universe filters (no network)."""

from __future__ import annotations

import pandas as pd

from core.delisted_universe import (
    build_yearly_report,
    filter_delisted_universe,
    is_spac_name,
    records_from_dataframe,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Symbol": "111111",
                "Name": "정상주권",
                "Market": "KOSDAQ",
                "SecuGroup": "주권",
                "ListingDate": "20180101",
                "DelistingDate": "20210315",
                "Reason": "자진상장폐지",
            },
            {
                "Symbol": "222222",
                "Name": "테스트 SPAC",
                "Market": "KOSPI",
                "SecuGroup": "주권",
                "ListingDate": "20200101",
                "DelistingDate": "20210601",
                "Reason": "SPAC",
            },
            {
                "Symbol": "333333",
                "Name": "코넥스주",
                "Market": "KONEX",
                "SecuGroup": "주권",
                "ListingDate": "20190101",
                "DelistingDate": "20220101",
                "Reason": "상장폐지",
            },
            {
                "Symbol": "44444",
                "Name": "짧은코드",
                "Market": "KOSPI",
                "SecuGroup": "주권",
                "ListingDate": "20190101",
                "DelistingDate": "20220101",
                "Reason": "상장폐지",
            },
            {
                "Symbol": "555555",
                "Name": "채권",
                "Market": "KOSPI",
                "SecuGroup": "채권",
                "ListingDate": "20190101",
                "DelistingDate": "20220101",
                "Reason": "상장폐지",
            },
        ]
    )


def test_is_spac_name():
    assert is_spac_name("ABC SPAC")
    assert is_spac_name("한국스팩1호")
    assert not is_spac_name("삼성전자")


def test_filter_delisted_universe_excludes_spac_konex_short_code():
    filtered = filter_delisted_universe(_sample_df(), year_from=2020, year_to=2026, exclude_konex=True)
    symbols = set(filtered["Symbol"].astype(str))
    assert symbols == {"111111"}


def test_records_and_yearly_report():
    filtered = filter_delisted_universe(_sample_df(), year_from=2020, year_to=2026)
    records = records_from_dataframe(filtered)
    assert records[0]["symbol"] == "111111"
    assert records[0]["delisting_date"] == "20210315"
    report = build_yearly_report(records, year_from=2020, year_to=2026)
    assert report["counts_by_year"]["2021"] == 1
