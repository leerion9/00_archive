"""
Step G g4 — delisted validation panel + status report.

  python -m scripts.archive_g4_delisted
  python -m scripts.archive_g4_delisted --symbols 036490 002300
  python -m scripts.archive_g4_delisted --status-only
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from config.settings import settings
from core.enrich_validate import validate_derived_samples
from core.listing_events import delisted_master_path, load_delisted_master
from core.merge_validate import validate_sample_symbols
from core.post_delist_verify import pick_spot_sample, run_post_delist_spot_check
from core.step_g_status import analyze_step_g, load_delisted_symbols
from scripts.archive_g3_delisted import G3_YEARS


def _load_panel_symbols(base, explicit: list[str] | None, sample_size: int) -> list[str]:
    if explicit:
        return [str(s).strip().zfill(6) for s in explicit]
    all_syms = load_delisted_symbols(base)
    return pick_spot_sample(all_syms, sample_size)


def _names_for_symbols(base) -> dict[str, str]:
    records = load_delisted_master(delisted_master_path(base))
    return {str(r["symbol"]).strip().zfill(6): str(r.get("name") or "") for r in records}


def main() -> None:
    parser = argparse.ArgumentParser(description="Step G g4 — delisted validation + status")
    parser.add_argument("--symbols", nargs="+", help="Validation panel symbols")
    parser.add_argument("--sample-size", type=int, default=10, help="Panel size (default 10)")
    parser.add_argument("--status-only", action="store_true", help="Skip merge/derived validation")
    parser.add_argument(
        "--skip-post-delist",
        action="store_true",
        help="Skip post-delist spot (status embeds full check by default)",
    )
    args = parser.parse_args()

    base = settings.base_dir
    all_syms = load_delisted_symbols(base)
    if not all_syms:
        raise SystemExit(f"no delisted master at {delisted_master_path(base)}")

    panel = _load_panel_symbols(base, args.symbols, int(args.sample_size))
    names = _names_for_symbols(base)
    years = G3_YEARS

    merge_results: list = []
    enrich_results: list = []
    if not args.status_only:
        merge_results = validate_sample_symbols(
            base,
            panel,
            years_planned=years,
        )
        for sym, result in zip(panel, merge_results):
            if not result.name:
                result.name = names.get(sym, "")

        enrich_results = validate_derived_samples(base, panel, years=years)

    status = analyze_step_g(base)
    post_delist = None
    if not args.skip_post_delist:
        post_delist = run_post_delist_spot_check(base, all_syms).to_dict()

    merge_pass = sum(1 for r in merge_results if r.ok)
    enrich_pass = sum(1 for r in enrich_results if r.ok)

    payload = {
        "schema_version": 1,
        "at_iso": datetime.now().astimezone().isoformat(timespec="seconds"),
        "phase": "g4",
        "validation_panel": panel,
        "merge_validation": {
            "passed": merge_pass,
            "total": len(merge_results),
            "results": [
                {
                    "symbol": r.symbol,
                    "name": r.name,
                    "ok": r.ok,
                    "bar_count": r.bar_count,
                    "failures": [{"name": c.name, "detail": c.detail} for c in r.failures()],
                }
                for r in merge_results
            ],
        },
        "enrich_validation": {
            "passed": enrich_pass,
            "total": len(enrich_results),
            "results": [
                {
                    "symbol": r.symbol,
                    "ok": r.ok,
                    "row_count": r.row_count,
                    "failures": [{"name": c.name, "detail": c.detail} for c in r.failures()],
                }
                for r in enrich_results
            ],
        },
        "post_delist_spot": post_delist or status.get("post_delist_spot"),
        "status": status,
    }

    date_tag = datetime.now().strftime("%Y%m%d")
    report_path = base / "reports" / f"g4_delisted_{date_tag}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n=== Step G g4 ===")
    print(f"panel ({len(panel)}): {', '.join(panel)}")
    if merge_results:
        print(f"merge validation: {merge_pass}/{len(merge_results)} passed")
        for r in merge_results:
            if not r.ok:
                print(f"  [FAIL] {r.symbol} {r.name}")
                for c in r.failures()[:5]:
                    print(f"         x {c.name}: {c.detail}")
    if enrich_results:
        print(f"enrich derived validation: {enrich_pass}/{len(enrich_results)} passed")
        for r in enrich_results:
            if not r.ok:
                print(f"  [FAIL] {r.symbol}")
                for c in r.failures()[:5]:
                    print(f"         x {c.name}: {c.detail}")

    pd = payload.get("post_delist_spot") or {}
    print(f"post-delist: ok={pd.get('ok')} anomaly={pd.get('anomaly')}")

    mcap = status.get("mcap_taxonomy") or {}
    tc = mcap.get("task_counts") or {}
    print(
        f"mcap taxonomy: done={tc.get('done', 0)} skipped_expected={tc.get('skipped_expected', 0)} "
        f"failed={tc.get('failed', 0)} pending={tc.get('pending', 0)} "
        f"(legacy reclassified={mcap.get('legacy_failed_reclassified_to_skipped_expected', 0)})"
    )
    print(f"report: {report_path}")

    failed = (merge_pass < len(merge_results)) or (enrich_pass < len(enrich_results))
    if pd.get("anomaly"):
        failed = True
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
