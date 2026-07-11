# -*- coding: utf-8 -*-
from core.fundamentals_build import accounts_to_event, events_to_frame, expand_daily_asof
import pandas as pd


def test_accounts_to_event_prefers_cfs():
    rows = [
        {
            "rcept_no": "20240515000123",
            "fs_div": "OFS",
            "account_nm": "매출액",
            "thstrm_amount": "100",
            "thstrm_dt": "2024.03.31",
        },
        {
            "rcept_no": "20240515000123",
            "fs_div": "CFS",
            "account_nm": "매출액",
            "thstrm_amount": "200",
            "thstrm_add_amount": "200",
            "thstrm_dt": "2024.03.31",
        },
        {
            "rcept_no": "20240515000123",
            "fs_div": "CFS",
            "account_nm": "영업이익",
            "thstrm_amount": "50",
        },
        {
            "rcept_no": "20240515000123",
            "fs_div": "CFS",
            "account_nm": "당기순이익",
            "thstrm_amount": "40",
        },
        {
            "rcept_no": "20240515000123",
            "fs_div": "CFS",
            "account_nm": "자본총계",
            "thstrm_amount": "1000",
        },
    ]
    ev = accounts_to_event(
        symbol="005930",
        corp_code="00126380",
        bsns_year=2024,
        reprt_code="11013",
        rows=rows,
    )
    assert ev is not None
    assert ev["rcept_dt"] == "20240515"
    assert ev["fs_div"] == "CFS"
    assert ev["revenue"] == 200.0
    assert ev["operating_income"] == 50.0
    assert ev["net_income"] == 40.0
    assert ev["equity"] == 1000.0


def test_expand_daily_asof_no_lookahead():
    events = events_to_frame(
        [
            {
                "symbol": "005930",
                "corp_code": "00126380",
                "bsns_year": 2024,
                "reprt_code": "11013",
                "reprt_name": "1Q",
                "rcept_no": "20240515000123",
                "rcept_dt": "20240515",
                "fiscal_end": "20240331",
                "fs_div": "CFS",
                "revenue": 200.0,
                "operating_income": 50.0,
                "net_income": 40.0,
                "equity": 1000.0,
                "assets": None,
                "liabilities": None,
                "eps": None,
                "source": "test",
                "fetched_at_iso": "2026-07-12T00:00:00+00:00",
            }
        ]
    )
    daily = pd.DataFrame(
        {
            "date": ["20240514", "20240515", "20240516"],
            "close": [70000, 71000, 72000],
            "shares_outstanding": [100.0, 100.0, 100.0],
        }
    )
    out = expand_daily_asof(events, daily=daily)
    # day before receipt: no fund
    assert pd.isna(out.loc[0, "fund_asof_date"])
    assert pd.isna(out.loc[0, "per"])
    # receipt day onward
    assert out.loc[1, "fund_asof_date"] == "20240515"
    assert out.loc[1, "bps_asof"] == 10.0  # 1000/100
    assert abs(out.loc[1, "pbr"] - 7100.0) < 1e-6  # 71000/10
    assert out.loc[1, "eps_method"] == "ni_over_shares"
