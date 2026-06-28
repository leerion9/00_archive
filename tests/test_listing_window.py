"""Tests for listing_window tradable range (no network)."""

from __future__ import annotations

import pytest

from core.listing_window import (
    ListingWindowIndex,
    SkipReason,
    date_skip_reason,
    is_tradable_date,
    is_tradable_year,
    legacy_skip_tag,
    year_skip_reason,
)


LISTING = "20100101"
DELISTING = "20211227"


def test_year_skip_before_listing_and_after_delisting():
    assert year_skip_reason(LISTING, DELISTING, 2009) == SkipReason.NOT_LISTED_YET
    assert year_skip_reason(LISTING, DELISTING, 2022) == SkipReason.ALREADY_DELISTED


def test_year_tradable_when_partial_overlap():
    assert year_skip_reason(LISTING, DELISTING, 2010) is None
    assert year_skip_reason(LISTING, DELISTING, 2021) is None
    assert is_tradable_year(LISTING, DELISTING, 2021) is True


def test_year_tradable_when_dates_missing():
    assert year_skip_reason(None, DELISTING, 2020) is None
    assert year_skip_reason(LISTING, None, 2030) is None
    assert year_skip_reason(None, None, 2020) is None


def test_date_skip_inclusive_bounds():
    assert date_skip_reason(LISTING, DELISTING, "20091231") == SkipReason.NOT_LISTED_YET
    assert date_skip_reason(LISTING, DELISTING, "20100101") is None
    assert date_skip_reason(LISTING, DELISTING, "20211227") is None
    assert date_skip_reason(LISTING, DELISTING, "20211228") == SkipReason.ALREADY_DELISTED
    assert is_tradable_date(LISTING, DELISTING, "20211227") is True


def test_legacy_skip_tag_matches_plan_delisted():
    assert legacy_skip_tag(SkipReason.NOT_LISTED_YET, 2020) == "listing_after_2020"
    assert legacy_skip_tag(SkipReason.ALREADY_DELISTED, 2022) == "delisted_before_2022"
    assert legacy_skip_tag(None, 2021) == ""


def test_listing_window_index_year_and_date():
    index = ListingWindowIndex(
        {
            "036490": {
                "listing_date": LISTING,
                "delisting_date": DELISTING,
                "status": "delisted",
            },
            "005930": {
                "listing_date": "19750611",
                "delisting_date": None,
                "status": "listed",
            },
        }
    )
    assert index.skip_reason("036490", 2009) == SkipReason.NOT_LISTED_YET
    assert index.skip_reason("036490", 2021) is None
    assert index.is_tradable("036490", 2021) is True
    assert index.is_tradable("036490", "20211227") is True
    assert index.is_tradable("036490", "20211228") is False
    assert index.is_tradable("005930", 2026) is True
    assert index.skip_reason("999999", 2020) == SkipReason.UNKNOWN_SYMBOL


def test_norm_ymd_invalid():
    with pytest.raises(ValueError):
        date_skip_reason(LISTING, DELISTING, "2021")
