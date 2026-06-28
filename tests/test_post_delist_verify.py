"""Tests for post-delisting spot verification."""

from __future__ import annotations

import json
from pathlib import Path

from core.post_delist_verify import (
    check_post_delist_symbol,
    pick_spot_sample,
    run_post_delist_spot_check,
)


def _write_merged(base: Path, symbol: str, bars: list[dict]) -> None:
    path = base / "merged" / f"{symbol}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"bars": bars}, ensure_ascii=False), encoding="utf-8")


def _write_features(base: Path, symbol: str, rows: list[dict]) -> None:
    import pandas as pd

    path = base / "features" / f"{symbol}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_check_post_delist_ok_when_empty_after_delist(tmp_path: Path):
    base = tmp_path / "data"
    sym = "036490"
    delist = "20211227"
    _write_merged(
        base,
        sym,
        [
            {"date": "20211227", "close": 100},
            {"date": "20211224", "close": 99},
        ],
    )
    _write_features(
        base,
        sym,
        [
            {"date": "20211227", "market_cap": 1000},
            {"date": "20211224", "market_cap": 900},
        ],
    )

    check = check_post_delist_symbol(base, sym, delisting_date=delist, name="상폐")
    assert check.ok
    assert check.status == "ok"
    assert check.post_delist_bars == 0
    assert check.post_delist_mcap_rows == 0


def test_check_post_delist_anomaly_on_bars_and_mcap(tmp_path: Path):
    base = tmp_path / "data"
    sym = "036490"
    delist = "20211227"
    _write_merged(
        base,
        sym,
        [
            {"date": "20211227", "close": 100},
            {"date": "20220104", "close": 50},
        ],
    )
    _write_features(
        base,
        sym,
        [
            {"date": "20211227", "market_cap": 1000},
            {"date": "20220201", "market_cap": 500},
        ],
    )

    check = check_post_delist_symbol(base, sym, delisting_date=delist)
    assert not check.ok
    assert check.status == "anomaly_post_delist"
    assert check.post_delist_bars == 1
    assert check.post_delist_mcap_rows == 1
    assert check.post_delist_bar_dates == ["20220104"]
    assert check.post_delist_mcap_dates == ["20220201"]


def test_pick_spot_sample_evenly_spreads():
    symbols = [f"{i:06d}" for i in range(100)]
    sample = pick_spot_sample(symbols, 10)
    assert len(sample) == 10
    assert sample[0] == "000000"
    assert sample[-1] == "000090"


def test_run_post_delist_spot_check_counts(tmp_path: Path):
    base = tmp_path / "data"
    sym_ok = "111111"
    sym_bad = "222222"
    delist = "20200315"
    _write_merged(base, sym_ok, [{"date": "20200313", "close": 1}])
    _write_merged(base, sym_bad, [{"date": "20200401", "close": 1}])

    report = run_post_delist_spot_check(
        base,
        [sym_ok, sym_bad],
        delisting_dates={sym_ok: delist, sym_bad: delist},
    )
    assert report.ok == 1
    assert report.anomaly == 1
    assert report.sample_size == 2
