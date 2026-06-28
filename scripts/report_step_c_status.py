"""Step C chunk별 manifest 실측 → stdout + snapshot JSON (legacy + relabeled)."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from core.mcap_taxonomy import PHASE1_YEARS, analyze_mcap_taxonomy, summarize_relabel_delta

GOOD_METHODS = frozenset({"pykrx_mcap", "etf_aum"})
YEARS = list(PHASE1_YEARS)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_latest_mcap_tasks(base_dir: Path) -> dict[str, dict]:
    path = base_dir / "manifest" / "enrich_tasks.jsonl"
    latest: dict[str, dict] = {}
    if not path.exists():
        return latest
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        t = json.loads(line)
        if t.get("step") != "market_cap":
            continue
        latest[t["task_id"]] = t
    return latest


def _sym_status(symbol: str, latest: dict[str, dict]) -> tuple[int, list[tuple[int, str, str | None]]]:
    good = 0
    details: list[tuple[int, str, str | None]] = []
    for year in YEARS:
        tid = f"{symbol}:{year}"
        t = latest.get(tid)
        if t and t.get("status") == "done" and t.get("method") in GOOD_METHODS:
            good += 1
        elif t:
            details.append((year, str(t.get("status", "")), t.get("method")))
        else:
            details.append((year, "none", None))
    return good, details


def _chunk_symbols(base_dir: Path, from_symbol: str, to_symbol: str) -> list[str]:
    merged = base_dir / "merged"
    return sorted(
        p.stem for p in merged.glob("*.json") if from_symbol <= p.stem <= to_symbol
    )


def _load_reports(base_dir: Path) -> dict[int, list[tuple[str, dict]]]:
    out: dict[int, list[tuple[str, dict]]] = defaultdict(list)
    reports_dir = base_dir / "reports"
    if not reports_dir.exists():
        return out
    for path in sorted(reports_dir.glob("enrich_market_cap_c*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cid = int(data["chunk_id"])
        out[cid].append((path.name, data))
    return out


def _load_failures_by_chunk(base_dir: Path, cfg: dict) -> dict[int, list[dict]]:
    path = base_dir / "manifest" / "enrich_mcap_failures.jsonl"
    by_chunk: dict[int, list[dict]] = defaultdict(list)
    if not path.exists():
        return by_chunk
    seen: set[str] = set()
    chunks = cfg["chunks"]
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        f = json.loads(line)
        tid = str(f.get("task_id", ""))
        if tid in seen:
            continue
        seen.add(tid)
        sym = str(f.get("symbol", ""))
        for ch in chunks:
            if ch["from_symbol"] <= sym <= ch["to_symbol"]:
                by_chunk[int(ch["chunk_id"])].append(f)
                break
    return by_chunk


def analyze(base_dir: Path) -> dict:
    cfg = json.loads((base_dir / "config" / "chunks_enrich.json").read_text(encoding="utf-8"))
    latest = _load_latest_mcap_tasks(base_dir)
    reports = _load_reports(base_dir)
    failures = _load_failures_by_chunk(base_dir, cfg)

    result: dict[int, dict] = {}
    relabel_totals = Counter()

    for ch in cfg["chunks"]:
        cid = int(ch["chunk_id"])
        fs, ts = ch["from_symbol"], ch["to_symbol"]
        syms = _chunk_symbols(base_dir, fs, ts)
        ok_n = partial_n = none_n = 0
        partial_list: list[tuple[str, int, list]] = []
        none_list: list[str] = []
        old_method_tasks: Counter[str] = Counter()

        for sym in syms:
            good, details = _sym_status(sym, latest)
            if good == 7:
                ok_n += 1
            elif good == 0:
                none_n += 1
                none_list.append(sym)
            else:
                partial_n += 1
                partial_list.append((sym, good, details))
            for year, status, method in details:
                if status == "done" and method and method not in GOOD_METHODS:
                    old_method_tasks[method] += 1

        relabeled = analyze_mcap_taxonomy(
            base_dir,
            syms,
            years=YEARS,
            open_task_limit=10,
            partial_limit=10,
            none_limit=10,
        )
        delta = summarize_relabel_delta(
            {"complete_7yr": ok_n, "partial": partial_n, "none": none_n},
            relabeled,
        )
        for key, val in delta.items():
            if key.startswith("relabeled_") or key.startswith("task_"):
                relabel_totals[key] += int(val)
        relabel_totals["legacy_complete_7yr"] += ok_n
        relabel_totals["legacy_partial"] += partial_n
        relabel_totals["legacy_none"] += none_n
        relabel_totals["legacy_failed_reclassified"] += relabeled.get(
            "legacy_failed_reclassified_to_skipped_expected", 0
        )

        result[cid] = {
            "chunk_id": cid,
            "role": ch.get("role", ""),
            "from_symbol": fs,
            "to_symbol": ts,
            "symbol_count": len(syms),
            "complete_7yr": ok_n,
            "partial": partial_n,
            "none": none_n,
            "partial_symbols": [
                {
                    "symbol": sym,
                    "done_years": good,
                    "missing": [
                        {"year": y, "status": st, "method": m}
                        for y, st, m in details
                        if not (st == "done" and m in GOOD_METHODS)
                    ],
                }
                for sym, good, details in partial_list
            ],
            "none_symbols": none_list,
            "legacy_method_tasks_remaining": dict(old_method_tasks),
            "failure_log_unique_tasks": len(failures.get(cid, [])),
            "relabeled": {
                "task_counts": relabeled.get("task_counts"),
                "delta": delta,
                "open_tasks": relabeled.get("open_tasks"),
                "partial_symbols": relabeled.get("partial_symbols"),
                "none_symbols": relabeled.get("none_symbols"),
            },
            "reports": [
                {
                    "file": name,
                    "at_iso": r.get("at_iso"),
                    "done": r.get("done"),
                    "failed": r.get("failed"),
                    "methods": r.get("methods"),
                }
                for name, r in reports.get(cid, [])
            ],
        }

    all_merged = sorted(p.stem for p in (base_dir / "merged").glob("*.json"))
    universe_relabel = analyze_mcap_taxonomy(
        base_dir,
        all_merged,
        years=YEARS,
        open_task_limit=50,
        partial_limit=30,
        none_limit=30,
    )

    return {
        "at_iso": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": 2,
        "chunks": {str(k): v for k, v in result.items()},
        "relabel_totals_by_chunk": dict(relabel_totals),
        "universe_relabel": universe_relabel,
    }


def main() -> None:
    base = _root() / "data" / "naver_daily_archive"
    payload = analyze(base)
    chunks = payload["chunks"]
    snapshot = base / "reports" / "step_c_status_snapshot.json"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    total_ok = total_partial = total_none = 0
    for cid in sorted(chunks, key=int):
        s = chunks[str(cid)]
        total_ok += s["complete_7yr"]
        total_partial += s["partial"]
        total_none += s["none"]
        rel = s.get("relabeled") or {}
        delta = rel.get("delta") or {}
        print(
            f"chunk {int(cid):1d} | {s['from_symbol']}~{s['to_symbol']} | "
            f"syms={s['symbol_count']} | legacy 7yr_ok={s['complete_7yr']} "
            f"partial={s['partial']} none={s['none']} | "
            f"relabeled complete={delta.get('relabeled_tradable_complete')} "
            f"partial={delta.get('relabeled_tradable_partial')} "
            f"none={delta.get('relabeled_tradable_none')} | "
            f"fail_log={s['failure_log_unique_tasks']}"
        )
        tc = rel.get("task_counts") or {}
        if tc.get("skipped_expected"):
            print(f"  relabel tasks: skipped_expected={tc.get('skipped_expected')} failed={tc.get('failed', 0)}")
        for rep in s["reports"]:
            print(
                f"  report {rep['file']}: done={rep['done']} failed={rep['failed']} at={rep['at_iso']}"
            )
        print()

    rt = payload.get("relabel_totals_by_chunk") or {}
    uni = payload.get("universe_relabel") or {}
    utc = uni.get("task_counts") or {}
    print(
        f"TOTAL legacy: 7yr_ok={total_ok} partial={total_partial} none={total_none}"
    )
    print(
        f"TOTAL relabeled: tradable_complete={rt.get('relabeled_tradable_complete')} "
        f"partial={rt.get('relabeled_tradable_partial')} none={rt.get('relabeled_tradable_none')} | "
        f"tasks skipped_expected={rt.get('task_skipped_expected')} failed={rt.get('task_failed_tradable')} "
        f"legacy_failed_reclassified={rt.get('legacy_failed_reclassified')}"
    )
    print(f"universe ({len(uni.get('years', []))}yr tasks={uni.get('tasks_total')}): {utc}")
    print(f"snapshot: {snapshot}")


if __name__ == "__main__":
    main()
