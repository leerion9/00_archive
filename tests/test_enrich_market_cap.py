"""Tests for market cap enrich task prune and empty classification."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from core.enrich_market_cap import build_mcap_tasks, run_mcap_enrich
from core.listing_events import listing_events_path


def _write_listing_events(base: Path, symbols: dict) -> None:
    path = listing_events_path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "symbols": symbols}, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_merged(base: Path, symbol: str, bars: list[dict]) -> None:
    path = base / "merged" / f"{symbol}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"bars": bars}, ensure_ascii=False), encoding="utf-8")


def test_build_mcap_tasks_prunes_outside_tradable_window(tmp_path: Path):
    base = tmp_path / "data"
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text(
        json.dumps({"036490": "상폐", "005930": "삼성"}, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_listing_events(
        base,
        {
            "036490": {
                "listing_date": "20100101",
                "delisting_date": "20211227",
                "status": "delisted",
            },
            "005930": {
                "listing_date": "19750611",
                "delisting_date": None,
                "status": "listed",
            },
        },
    )
    _write_merged(base, "036490", [{"date": "20210104", "close": 1}])
    _write_merged(base, "005930", [{"date": "20260102", "close": 1}])

    tasks = build_mcap_tasks(base, years=[2020, 2021, 2022])
    by_id = {t["task_id"]: t for t in tasks}

    assert by_id["036490:2020"]["status"] == "pending"
    assert by_id["036490:2021"]["status"] == "pending"
    assert by_id["036490:2022"]["status"] == "skipped_expected"
    assert by_id["036490:2022"]["skip_reason"] == "already_delisted"
    assert by_id["005930:2022"]["status"] == "pending"


def test_run_mcap_enrich_passes_listing_market_etf외(tmp_path: Path):
    base = tmp_path / "data"
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text(
        json.dumps({"500020": "ETN"}, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_listing_events(
        base,
        {
            "500020": {
                "listing_date": "20200101",
                "delisting_date": None,
                "status": "listed",
                "market": "etf외",
            },
        },
    )
    _write_merged(base, "500020", [{"date": "20260102", "close": 100, "volume": 1}])

    tasks = [
        {
            "task_id": "500020:2026",
            "symbol": "500020",
            "name": "ETN",
            "year": 2026,
            "step": "market_cap",
            "status": "pending",
        },
    ]

    with patch("core.enrich_market_cap.fetch_market_cap_for_year") as fetch:
        fetch.return_value = (
            pd.DataFrame({"date": ["20260102"], "market_cap": [1.0], "shares_outstanding": [1]}),
            "etf_aum",
        )
        report = run_mcap_enrich(base, tasks, use_listing_window=True)

    assert report.done == 1
    _, kwargs = fetch.call_args
    assert kwargs["listing_market"] == "etf외"


def test_run_mcap_enrich_skips_expected_and_classifies_empty(tmp_path: Path):
    base = tmp_path / "data"
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text("{}", encoding="utf-8")
    _write_listing_events(
        base,
        {
            "036490": {
                "listing_date": "20100101",
                "delisting_date": "20211227",
                "status": "delisted",
            },
        },
    )
    _write_merged(base, "036490", [{"date": "20210104", "close": 100, "volume": 1}])

    tasks = [
        {
            "task_id": "036490:2022",
            "symbol": "036490",
            "name": "상폐",
            "year": 2022,
            "step": "market_cap",
            "status": "skipped_expected",
            "skip_reason": "already_delisted",
        },
        {
            "task_id": "036490:2021",
            "symbol": "036490",
            "name": "상폐",
            "year": 2021,
            "step": "market_cap",
            "status": "pending",
        },
    ]

    with patch("core.enrich_market_cap.fetch_market_cap_for_year") as fetch:
        fetch.return_value = (
            pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]),
            "failed",
        )
        report = run_mcap_enrich(base, tasks, use_listing_window=True)

    assert report.skipped_expected == 1
    assert report.failed == 1
    assert report.expected_blank == 0
    fetch.assert_called_once()


def test_run_mcap_enrich_empty_outside_window_is_expected_blank(tmp_path: Path):
    base = tmp_path / "data"
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text("{}", encoding="utf-8")
    _write_listing_events(
        base,
        {
            "036490": {
                "listing_date": "20100101",
                "delisting_date": "20211227",
                "status": "delisted",
            },
        },
    )
    _write_merged(base, "036490", [{"date": "20220104", "close": 100, "volume": 1}])

    tasks = [
        {
            "task_id": "036490:2022",
            "symbol": "036490",
            "name": "상폐",
            "year": 2022,
            "step": "market_cap",
            "status": "pending",
        },
    ]

    with patch("core.enrich_market_cap.fetch_market_cap_for_year") as fetch:
        fetch.return_value = (
            pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]),
            "empty",
        )
        report = run_mcap_enrich(base, tasks, use_listing_window=True)

    assert report.expected_blank == 1
    assert report.failed == 0
    assert report.results[0].status == "expected_blank"


def test_run_mcap_enrich_empty_no_ohlcv_is_expected_blank(tmp_path: Path):
    base = tmp_path / "data"
    (base / "master").mkdir(parents=True)
    (base / "master" / "symbols_active.json").write_text("{}", encoding="utf-8")
    path = base / "master" / "listing_events.json"
    path.write_text(
        json.dumps(
            {
                "symbols": {
                    "141020": {
                        "listing_date": "20130129",
                        "delisting_date": "20240103",
                        "status": "delisted",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    merged = base / "merged" / "141020.json"
    merged.parent.mkdir(parents=True, exist_ok=True)
    merged.write_text(
        json.dumps({"bars": [{"date": "20231228", "close": 1, "volume": 1}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    tasks = [
        {
            "task_id": "141020:2024",
            "symbol": "141020",
            "name": "테스트",
            "year": 2024,
            "step": "market_cap",
            "status": "pending",
        },
    ]

    with patch("core.enrich_market_cap.fetch_market_cap_for_year") as fetch:
        fetch.return_value = (
            pd.DataFrame(columns=["date", "market_cap", "shares_outstanding"]),
            "empty",
        )
        report = run_mcap_enrich(base, tasks, use_listing_window=True)

    assert report.expected_blank == 1
    assert report.failed == 0
    assert report.results[0].skip_reason == "no_ohlcv_for_year"


def test_merge_mcap_accumulates_years():
    from core.enrich_market_cap import _merge_mcap_into_features

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
