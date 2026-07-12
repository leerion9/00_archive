# -*- coding: utf-8 -*-
"""
DART fundamentals bulk collect (events parquet) with daily soft-quota resume.

Writes: data/naver_daily_archive/fundamentals_events/{symbol}.parquet
Progress: data/naver_daily_archive/master/fundamentals_collect_progress.json

Year range default matches OHLCV archive: ARCHIVE_YEAR_FROM .. ARCHIVE_YEAR_TO
(2020~2026). Daily as-of expand is a later step (see FUNDAMENTALS_SCHEMA.md).

Examples:
  # D1 smoke (50 symbols)
  python -m scripts.archive_fundamentals_collect --limit 50

  # Full resume (stops at soft 35k)
  python -m scripts.archive_fundamentals_collect
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from config.settings import settings
from core.dart_client import (
    REPRT_CODES,
    DartApiError,
    DartClient,
    DartQuotaExceeded,
)
from core.fundamentals_build import accounts_to_event, events_to_frame

_log = logging.getLogger("archive")
_KST = ZoneInfo("Asia/Seoul")


def _base_dir() -> Path:
    base = Path(settings.base_dir)
    if not base.is_absolute():
        base = Path(__file__).resolve().parents[1] / base
    return base


def _list_symbols(base: Path) -> List[str]:
    merged = base / "merged"
    feats = base / "features"
    syms: set[str] = set()
    if merged.exists():
        for p in merged.glob("*.json"):
            if p.stem.isdigit() and len(p.stem) == 6:
                syms.add(p.stem)
    if feats.exists():
        for p in feats.glob("*.parquet"):
            if p.stem.isdigit() and len(p.stem) == 6:
                syms.add(p.stem)
    return sorted(syms)


def _progress_path(base: Path) -> Path:
    return base / "master" / "fundamentals_collect_progress.json"


def _load_progress(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "years": [],
            "completed": {},
            "failed": {},
            "no_corp": [],
            "updated_at_iso": "",
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "years": [],
            "completed": {},
            "failed": {},
            "no_corp": [],
            "updated_at_iso": "",
        }


def _save_progress(path: Path, progress: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    progress["updated_at_iso"] = datetime.now(_KST).isoformat(timespec="seconds")
    path.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def collect_symbol(
    client: DartClient,
    *,
    symbol: str,
    years: List[int],
    corp_cache: Path,
    events_dir: Path,
) -> Dict[str, Any]:
    corp_code = client.corp_code_for(symbol, corp_cache)
    events = []
    empty = 0
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
                empty += 1
                continue
            events.append(ev)

    ev_df = events_to_frame(events)
    events_dir.mkdir(parents=True, exist_ok=True)
    out_path = events_dir / f"{symbol}.parquet"
    ev_df.to_parquet(out_path, index=False)

    return {
        "symbol": symbol,
        "corp_code": corp_code,
        "events": int(len(ev_df)),
        "empty_calls": empty,
        "path": str(out_path),
    }


def run(
    *,
    years: List[int],
    limit: Optional[int],
    force: bool,
    offset: int,
) -> Dict[str, Any]:
    base = _base_dir()
    symbols = _list_symbols(base)
    if offset:
        symbols = symbols[offset:]
    if limit is not None:
        symbols = symbols[: max(0, int(limit))]

    progress_path = _progress_path(base)
    progress = _load_progress(progress_path)
    progress["years"] = list(years)

    client = DartClient(
        settings.dart_api_key,
        delay_sec=max(0.1, float(settings.dart_delay_sec)),
        quota_path=base / "master" / "dart_quota.json",
        soft_limit=int(settings.dart_daily_soft_limit),
        hard_limit=int(settings.dart_daily_hard_limit),
    )
    q0 = client.quota.state()
    _log.info(
        "DART quota before: %s/%s (hard=%s, ymd=%s) symbols_target=%s years=%s",
        q0.count,
        q0.soft_limit,
        q0.hard_limit,
        q0.ymd,
        len(symbols),
        years,
    )

    corp_cache = base / "master" / "dart_corp_codes.zip"
    events_dir = base / "fundamentals_events"
    # Warm corp map once (counts as 1 request if zip missing).
    client.download_corp_codes(corp_cache)

    done = 0
    skipped = 0
    failed = 0
    no_corp = 0
    stopped_quota = False
    last_symbol = ""

    for i, symbol in enumerate(symbols):
        if (not force) and symbol in progress.get("completed", {}):
            skipped += 1
            continue
        last_symbol = symbol
        try:
            result = collect_symbol(
                client,
                symbol=symbol,
                years=years,
                corp_cache=corp_cache,
                events_dir=events_dir,
            )
            progress.setdefault("completed", {})[symbol] = {
                "events": result["events"],
                "corp_code": result["corp_code"],
                "empty_calls": result["empty_calls"],
                "updated_at_iso": datetime.now(_KST).isoformat(timespec="seconds"),
            }
            progress.get("failed", {}).pop(symbol, None)
            done += 1
            if done % 5 == 0 or done == 1:
                q = client.quota.state()
                _log.info(
                    "progress done=%s skipped=%s fail=%s last=%s events=%s quota=%s/%s",
                    done,
                    skipped,
                    failed,
                    symbol,
                    result["events"],
                    q.count,
                    q.soft_limit,
                )
                _save_progress(progress_path, progress)
        except DartQuotaExceeded as exc:
            stopped_quota = True
            _log.warning("quota stop at %s: %s", symbol, exc)
            _save_progress(progress_path, progress)
            break
        except DartApiError as exc:
            failed += 1
            msg = str(exc)
            if "corp_code 없음" in msg:
                no_corp += 1
                progress.setdefault("no_corp", [])
                if symbol not in progress["no_corp"]:
                    progress["no_corp"].append(symbol)
            progress.setdefault("failed", {})[symbol] = msg
            _log.error("fail %s: %s", symbol, exc)
            _save_progress(progress_path, progress)
            continue

    _save_progress(progress_path, progress)
    q1 = client.quota.state()
    return {
        "years": years,
        "symbols_targeted": len(symbols),
        "done_this_run": done,
        "skipped_already_done": skipped,
        "failed_this_run": failed,
        "no_corp_this_run": no_corp,
        "stopped_quota": stopped_quota,
        "last_symbol": last_symbol,
        "completed_total": len(progress.get("completed", {})),
        "failed_total": len(progress.get("failed", {})),
        "no_corp_total": len(progress.get("no_corp", [])),
        "progress_path": str(progress_path),
        "events_dir": str(events_dir),
        "dart_quota": {
            "ymd": q1.ymd,
            "count": q1.count,
            "soft_limit": q1.soft_limit,
            "hard_limit": q1.hard_limit,
            "remaining_soft": q1.remaining_soft,
        },
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="DART fundamentals bulk collect")
    parser.add_argument(
        "--year-from",
        type=int,
        default=2020,
        help="first business year (OHLCV archive start)",
    )
    parser.add_argument(
        "--year-to",
        type=int,
        default=int(settings.year_to),
        help="last business year (default: ARCHIVE_YEAR_TO)",
    )
    parser.add_argument("--limit", type=int, default=None, help="max symbols this run")
    parser.add_argument("--offset", type=int, default=0, help="skip first N symbols")
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-fetch even if symbol is in progress completed",
    )
    args = parser.parse_args()

    # Align with OHLCV archive window: 2020 .. 2026 (May end_date is trading data;
    # fiscal years still requested through year_to).
    year_from = max(2020, int(args.year_from))
    year_to = int(args.year_to)
    if year_to < year_from:
        raise SystemExit("year-to must be >= year-from")
    years = list(range(year_from, year_to + 1))

    try:
        summary = run(
            years=years,
            limit=args.limit,
            force=bool(args.force),
            offset=int(args.offset),
        )
    except DartApiError as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
