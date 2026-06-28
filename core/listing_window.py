"""Tradable window helpers using listing_events ([listing_date, delisting_date])."""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

from core.listing_events import listing_events_path

YMD_RE = re.compile(r"^\d{8}$")


class SkipReason(str, Enum):
    """Why a symbol is outside the tradable window for a year or date."""

    NOT_LISTED_YET = "not_listed_yet"
    ALREADY_DELISTED = "already_delisted"
    UNKNOWN_SYMBOL = "unknown_symbol"


def _norm_symbol(symbol: str) -> str:
    return str(symbol).strip().zfill(6)


def _norm_ymd(value: Union[str, int]) -> str:
    text = str(value).strip()
    if YMD_RE.match(text):
        return text
    raise ValueError(f"expected YYYYMMDD, got {value!r}")


def _year_bounds(year: int) -> tuple[str, str]:
    y = int(year)
    return f"{y}0101", f"{y}1231"


def _is_year(when: Union[str, int]) -> bool:
    if isinstance(when, int):
        return True
    text = str(when).strip()
    return len(text) == 4 and text.isdigit()


def year_skip_reason(
    listing_date: Optional[str],
    delisting_date: Optional[str],
    year: int,
) -> Optional[SkipReason]:
    """Return skip reason when the entire calendar year is outside the tradable window."""
    y_start, y_end = _year_bounds(year)
    if listing_date and listing_date > y_end:
        return SkipReason.NOT_LISTED_YET
    if delisting_date and delisting_date < y_start:
        return SkipReason.ALREADY_DELISTED
    return None


def is_tradable_year(
    listing_date: Optional[str],
    delisting_date: Optional[str],
    year: int,
) -> bool:
    return year_skip_reason(listing_date, delisting_date, year) is None


def date_skip_reason(
    listing_date: Optional[str],
    delisting_date: Optional[str],
    date: str,
) -> Optional[SkipReason]:
    ymd = _norm_ymd(date)
    if listing_date and ymd < listing_date:
        return SkipReason.NOT_LISTED_YET
    if delisting_date and ymd > delisting_date:
        return SkipReason.ALREADY_DELISTED
    return None


def is_tradable_date(
    listing_date: Optional[str],
    delisting_date: Optional[str],
    date: str,
) -> bool:
    return date_skip_reason(listing_date, delisting_date, date) is None


def legacy_skip_tag(reason: Optional[SkipReason], year: int) -> str:
    """Error tag used by archive_plan_delisted (e.g. listing_after_2020)."""
    if reason is None:
        return ""
    if reason == SkipReason.NOT_LISTED_YET:
        return f"listing_after_{year}"
    if reason == SkipReason.ALREADY_DELISTED:
        return f"delisted_before_{year}"
    return reason.value


class ListingWindowIndex:
    """In-memory index over listing_events.json symbols."""

    def __init__(self, symbols: Mapping[str, Dict[str, Any]]):
        self._symbols = {_norm_symbol(k): v for k, v in symbols.items()}

    @classmethod
    def load(cls, base_dir: Path) -> ListingWindowIndex:
        path = listing_events_path(base_dir)
        if not path.exists():
            return cls({})
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(payload.get("symbols") or {})

    def record(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._symbols.get(_norm_symbol(symbol))

    def listing_delisting(self, symbol: str) -> tuple[Optional[str], Optional[str]]:
        rec = self.record(symbol)
        if rec is None:
            return None, None
        return rec.get("listing_date"), rec.get("delisting_date")

    def listing_market(self, symbol: str) -> str:
        rec = self.record(symbol)
        if rec is None:
            return ""
        return str(rec.get("market") or "").strip()

    def skip_reason(self, symbol: str, when: Union[str, int]) -> Optional[SkipReason]:
        rec = self.record(symbol)
        if rec is None:
            return SkipReason.UNKNOWN_SYMBOL
        listing = rec.get("listing_date")
        delisting = rec.get("delisting_date")
        if _is_year(when):
            return year_skip_reason(listing, delisting, int(when))
        return date_skip_reason(listing, delisting, str(when))

    def is_tradable(self, symbol: str, when: Union[str, int]) -> bool:
        """True when *when* (YYYYMMDD or calendar year) overlaps the tradable window."""
        return self.skip_reason(symbol, when) is None


def is_tradable(
    symbol: str,
    when: Union[str, int],
    *,
    index: ListingWindowIndex,
) -> bool:
    return index.is_tradable(symbol, when)


def skip_reason_for(
    symbol: str,
    when: Union[str, int],
    *,
    index: ListingWindowIndex,
) -> Optional[SkipReason]:
    return index.skip_reason(symbol, when)
