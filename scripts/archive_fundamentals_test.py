# -*- coding: utf-8 -*-
"""
Test-only DART fundamentals collect + daily as-of expand.

Does NOT write into production features/ for all symbols.
Writes:
  fundamentals_events/{symbol}.parquet
  fundamentals_daily_test/{symbol}.parquet
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from config.settings import settings
from core.dart_client import REPRT_CODES, DartApiError, DartQuotaExceeded, DartClient
from core.fundamentals_build import accounts_to_event, events_to_frame, expand_daily_asof

_log = logging.getLogger("archive")


def _load_daily(symbol: str, base: Path) -> pd.DataFrame:
    feat_path = base / "features" / f"{symbol}.parquet"
    merged_path = base / "merged" / f"{symbol}.json"
    if not feat_path.exists():
        raise FileNotFoundError(f"features missing: {feat_path}")
    feat = pd.read_parquet(feat_path)
    if "date" not in feat.columns:
        feat = feat.reset_index()
    feat["date"] = feat["date"].astype(str).str.replace(r"\D", "", regex=True).str[:8]

    closes = {}
    if merged_path.exists():
        payload = json.loads(merged_path.read_text(encoding="utf-8"))
        for bar in payload.get("bars") or []:
            d = str(bar.get("date", "")).replace(".", "").replace("-", "")[:8]
            if d:
                closes[d] = int(bar.get("close") or 0)

    feat["close"] = feat["date"].map(closes)
    return feat[["date", "close", "shares_outstanding", "market_cap"]].copy()


def run_test(symbol: str, years: list[int]) -> dict:
    base = Path(settings.base_dir)
    if not base.is_absolute():
        base = Path(__file__).resolve().parents[1] / base

    client = DartClient(
        settings.dart_api_key,
        delay_sec=max(0.1, float(settings.dart_delay_sec)),
        quota_path=base / "master" / "dart_quota.json",
        soft_limit=int(settings.dart_daily_soft_limit),
        hard_limit=int(settings.dart_daily_hard_limit),
    )
    q0 = client.quota.state()
    _log.info(
        "DART quota before: %s/%s (hard=%s, ymd=%s)",
        q0.count,
        q0.soft_limit,
        q0.hard_limit,
        q0.ymd,
    )
    corp_cache = base / "master" / "dart_corp_codes.zip"
    corp_code = client.corp_code_for(symbol, corp_cache)
    _log.info("symbol=%s corp_code=%s", symbol, corp_code)

    events = []
    for year in years:
        for code in REPRT_CODES:
            rows = client.fetch_major_accounts(
                corp_code=corp_code, bsns_year=year, reprt_code=code
            )
            ev = accounts_to_event(
                symbol=symbol,
                corp_code=corp_code,
                bsns_year=year,
                reprt_code=code,
                rows=rows,
            )
            if ev is None:
                _log.info("no data %s %s %s", symbol, year, code)
                continue
            events.append(ev)
            _log.info(
                "ok %s %s %s rcept=%s rev=%s ni=%s equity=%s",
                symbol,
                year,
                code,
                ev["rcept_dt"],
                ev["revenue"],
                ev["net_income"],
                ev["equity"],
            )

    ev_df = events_to_frame(events)
    ev_dir = base / "fundamentals_events"
    daily_dir = base / "fundamentals_daily_test"
    ev_dir.mkdir(parents=True, exist_ok=True)
    daily_dir.mkdir(parents=True, exist_ok=True)

    ev_path = ev_dir / f"{symbol}.parquet"
    daily_path = daily_dir / f"{symbol}.parquet"

    if ev_df.empty:
        raise SystemExit("수집된 이벤트가 0건입니다.")

    ev_df.to_parquet(ev_path, index=False)

    daily = _load_daily(symbol, base)
    asof = expand_daily_asof(ev_df, daily=daily)
    asof.to_parquet(daily_path, index=False)

    q1 = client.quota.state()
    covered = int(asof["fund_asof_date"].notna().sum())
    sample = asof.dropna(subset=["per"]).tail(3)[
        ["date", "fund_asof_date", "per", "pbr", "eps_method"]
    ]

    summary = {
        "symbol": symbol,
        "corp_code": corp_code,
        "events": int(len(ev_df)),
        "events_path": str(ev_path),
        "daily_rows": int(len(asof)),
        "daily_with_fund": covered,
        "daily_path": str(daily_path),
        "dart_quota": {
            "ymd": q1.ymd,
            "count": q1.count,
            "soft_limit": q1.soft_limit,
            "hard_limit": q1.hard_limit,
            "remaining_soft": q1.remaining_soft,
        },
        "sample_tail": sample.to_dict(orient="records"),
    }
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="DART fundamentals test collect")
    parser.add_argument("--symbol", default="005930")
    parser.add_argument("--years", nargs="+", type=int, default=[2023, 2024])
    args = parser.parse_args()
    try:
        summary = run_test(str(args.symbol).zfill(6), list(args.years))
    except (DartApiError, DartQuotaExceeded) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
