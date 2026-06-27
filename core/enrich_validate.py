"use Validate Step B derived features against merged bars (10-symbol panel)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

import pandas as pd

from core.enrich_derived import (
    FEATURE_COLUMNS,
    compute_derived_frame,
    features_path,
    filter_frame_by_years,
    read_features_parquet,
)
from core.merge_validate import DEFAULT_SAMPLE_SYMBOLS
from core.archive_merge import load_collection_plan_years, merged_path


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class DerivedValidation:
    symbol: str
    ok: bool
    checks: List[CheckResult] = field(default_factory=list)
    row_count: int = 0

    def failures(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.ok]


def validate_derived_symbol(
    base_dir: Path,
    symbol: str,
    *,
    years: Optional[Sequence[int]] = None,
) -> DerivedValidation:
    sym = str(symbol).strip()
    years_list = sorted({int(y) for y in years}, reverse=True) if years else load_collection_plan_years(base_dir)
    checks: List[CheckResult] = []

    merged_file = merged_path(base_dir, sym)
    feat_file = features_path(base_dir, sym)

    if not merged_file.exists():
        checks.append(CheckResult("merged_exists", False, str(merged_file)))
        return DerivedValidation(symbol=sym, ok=False, checks=checks)

    if not feat_file.exists():
        checks.append(CheckResult("features_exists", False, str(feat_file)))
        return DerivedValidation(symbol=sym, ok=False, checks=checks)

    checks.append(CheckResult("features_exists", True, str(feat_file)))

    merged = json.loads(merged_file.read_text(encoding="utf-8"))
    bars = list(merged.get("bars") or [])
    expected_full = compute_derived_frame(bars)
    expected = filter_frame_by_years(expected_full, years_list) if years_list else expected_full
    actual = read_features_parquet(feat_file)

    required_cols = {"date", *FEATURE_COLUMNS}
    actual_cols = set(actual.columns)
    missing = sorted(required_cols - actual_cols)
    checks.append(
        CheckResult(
            "columns",
            not missing,
            f"columns={list(actual.columns)} missing={missing}",
        )
    )
    checks.append(
        CheckResult(
            "row_count",
            len(actual) == len(expected),
            f"actual={len(actual)} expected={len(expected)}",
        )
    )

    if not expected.empty:
        exp = expected.copy()
        act = actual.copy()
        for col in FEATURE_COLUMNS:
            exp[col] = pd.to_numeric(exp[col], errors="coerce")
            act[col] = pd.to_numeric(act[col], errors="coerce")
        merged_cmp = exp.merge(act, on="date", suffixes=("_exp", "_act"))
        checks.append(
            CheckResult(
                "dates_join",
                len(merged_cmp) == len(exp),
                f"joined={len(merged_cmp)} expected={len(exp)}",
            )
        )
        for col in FEATURE_COLUMNS:
            exp_col = merged_cmp[f"{col}_exp"]
            act_col = merged_cmp[f"{col}_act"]
            both_nan = exp_col.isna() & act_col.isna()
            numeric_match = (exp_col.fillna(0) - act_col.fillna(0)).abs().max() < 0.01
            checks.append(
                CheckResult(
                    f"{col}_match",
                    bool(both_nan.all() or numeric_match),
                    f"max_diff={(exp_col - act_col).abs().max()}",
                )
            )

        if len(exp) >= 5:
            date_key = str(exp.iloc[4]["date"])
            bar = next((b for b in bars if str(b.get("date")) == date_key), None)
            if bar:
                expected_tv = int(bar.get("close", 0) or 0) * int(bar.get("volume", 0) or 0)
                actual_tv = int(actual.loc[actual["date"] == date_key, "trading_value"].iloc[0])
                checks.append(
                    CheckResult(
                        "trading_value_formula",
                        expected_tv == actual_tv,
                        f"date={date_key} expected={expected_tv} actual={actual_tv}",
                    )
                )

    ok = all(c.ok for c in checks)
    return DerivedValidation(symbol=sym, ok=ok, checks=checks, row_count=len(actual))


def validate_derived_samples(
    base_dir: Path,
    symbols: Sequence[str],
    *,
    years: Optional[Sequence[int]] = None,
) -> List[DerivedValidation]:
    return [validate_derived_symbol(base_dir, sym, years=years) for sym in symbols]
