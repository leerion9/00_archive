"""Step G manifest 실측 → stdout + snapshot JSON (g4 status)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from config.settings import settings
from core.step_g_status import analyze_step_g


def _print_status(payload: dict) -> None:
    print("\n=== Step G status (g4) ===")
    print(f"delisted symbols: {payload['delisted_symbols']}")
    print(f"listing_events delisted: {payload['listing_events_delisted']}")

    sidecar = payload["sidecar"]
    print(f"sidecar merged/features: {sidecar['merged']}/{sidecar['symbols']} · {sidecar['features']}/{sidecar['symbols']}")

    g2 = payload["g2_tasks"]
    if g2.get("exists"):
        print(f"g2 OHLCV tasks: {g2['tasks_total']} {g2['status_counts']}")
    else:
        print("g2 OHLCV tasks: (missing tasks_delisted.jsonl)")

    mcap = payload["mcap_taxonomy"]
    tc = mcap["task_counts"]
    print("\n--- mcap task taxonomy (listing_window reclassified) ---")
    print(f"tasks total: {mcap['tasks_total']}")
    for key in (
        "done",
        "skipped_expected",
        "expected_blank",
        "partial",
        "failed",
        "pending",
    ):
        if key in tc:
            print(f"  {key}: {tc[key]}")
    print(
        f"legacy failed→skipped_expected: {mcap['legacy_failed_reclassified_to_skipped_expected']}"
    )
    print(
        "symbol tradable mcap: "
        f"complete={mcap['symbol_tradable_complete']} "
        f"partial={mcap['symbol_tradable_partial']} "
        f"none={mcap['symbol_tradable_none']} "
        f"skipped_only={mcap['symbol_skipped_only']}"
    )

    legacy = payload.get("g3_mcap_reports_legacy") or []
    if legacy:
        print("\n--- g3 run reports (legacy counters) ---")
        for rep in legacy:
            print(
                f"  c{rep.get('chunk_id')} {rep.get('file')}: "
                f"done={rep.get('done')} failed={rep.get('failed')}"
            )

    pd = payload["post_delist_spot"]
    print(
        f"\npost-delist spot: ok={pd['ok']} anomaly={pd['anomaly']} skipped={pd['skipped']}"
    )

    open_tasks = mcap.get("open_tasks_sample") or []
    if open_tasks:
        print(f"\nopen tasks sample ({len(open_tasks)}):")
        for row in open_tasks[:10]:
            print(
                f"  {row['task_id']}: {row['classified']} "
                f"(logged={row.get('logged_status')}) {row.get('error') or ''}"
            )


def main() -> None:
    base = settings.base_dir
    payload = analyze_step_g(base)
    payload["at_iso"] = datetime.now().astimezone().isoformat(timespec="seconds")

    snapshot = base / "reports" / "step_g_status_snapshot.json"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    _print_status(payload)
    print(f"\nsnapshot: {snapshot}")


if __name__ == "__main__":
    main()
