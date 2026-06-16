"""
Collect Naver daily OHLCV archive chunks for assigned worker tasks.

  python -m scripts.archive_collect --chunk 0 --max-tasks 0
  python -m scripts.archive_collect --retry-failed --max-tasks 50
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime

from config.settings import settings
from core.archive_schema import build_chunk_payload, raw_chunk_path, utc_now_iso, write_chunk
from core.manifest import append_progress, load_tasks_jsonl, pick_pending_tasks, save_tasks_jsonl, update_task_status
from core.naver_daily import fetch_pages_for_year
from core.page_cursor import start_page_for_fetch, update_cursor_after_fetch
from core.shard import chunk_config_path
from core.throttle import RequestThrottler

_log = logging.getLogger("archive")


def _configure_logging(worker_id: str, chunk_id: int | None) -> None:
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    chunk_tag = f"_c{chunk_id}" if chunk_id is not None else ""
    log_file = log_dir / f"archive_{worker_id}{chunk_tag}_{date_tag}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )


def _print_run_summary(tasks: list[dict], stats: dict) -> None:
    failed = [t for t in tasks if t.get("status") == "failed" and t.get("_run_failed")]
    skipped = [t for t in tasks if t.get("status") == "skipped" and t.get("_run_skipped")]
    print("\n=== run summary ===")
    print(
        f"picked={stats['picked']} done={stats['done']} failed={stats.get('failed', 0)} "
        f"skipped={stats.get('skipped', 0)} "
        f"requests={stats.get('requests', 0)} elapsed={stats.get('elapsed_sec', 0)}s "
        f"cursor_skip_pages={stats.get('skipped_pages', 0)}"
    )
    if stats.get("aborted_ok"):
        print(f"aborted_with_data={stats['aborted_ok']} (stale/page-budget, saved partial)")
    if failed:
        print(f"failed this run ({len(failed)}):")
        for t in failed[:20]:
            print(f"  {t['task_id']}: {t.get('error', '')}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")
        print("retry later: python -m scripts.archive_collect --retry-failed")
    if skipped:
        print(f"skipped this run ({len(skipped)}) - final after retry:")
        for t in skipped[:20]:
            print(f"  {t['task_id']}: {t.get('error', '')}")
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more")


def run_collect(
    worker_id: str,
    max_tasks: int,
    *,
    chunk_id: int | None = None,
    retry_failed: bool = False,
    symbols_only: set[str] | None = None,
) -> dict:
    base = settings.base_dir
    tasks_path = base / "manifest" / "tasks.jsonl"
    progress_path = base / "manifest" / "progress.jsonl"
    bounds_path = chunk_config_path(base)

    tasks = load_tasks_jsonl(tasks_path)
    if not tasks:
        raise SystemExit(f"no tasks at {tasks_path}; run archive_plan first")

    batch = pick_pending_tasks(
        tasks,
        worker_id,
        max_tasks=max_tasks,
        pc_year_min=settings.pc_year_min,
        chunk_id=chunk_id,
        chunk_bounds_path=bounds_path if chunk_id is not None else None,
        symbols_only=symbols_only,
        retry_failed=retry_failed,
    )
    if not batch:
        _log.info("no tasks to collect worker=%s chunk=%s retry_failed=%s", worker_id, chunk_id, retry_failed)
        return {"picked": 0, "done": 0, "failed": 0}

    throttler = RequestThrottler(
        delay_sec=settings.delay_sec,
        jitter_sec=settings.jitter_sec,
        batch_size=settings.batch_size,
        batch_pause_sec=settings.batch_pause_sec,
    )

    stats = {"picked": len(batch), "done": 0, "failed": 0, "skipped": 0, "skipped_pages": 0, "aborted_ok": 0}
    t0 = time.monotonic()

    for task in batch:
        tid = str(task["task_id"])
        symbol = str(task["symbol"])
        year = int(task["year"])
        update_task_status(tasks, tid, "running")
        save_tasks_jsonl(tasks_path, tasks)
        append_progress(
            progress_path,
            {"at_iso": utc_now_iso(), "worker_id": worker_id, "task_id": tid, "status": "running"},
        )

        start_page = start_page_for_fetch(base, symbol)
        if start_page > 1:
            stats["skipped_pages"] = stats.get("skipped_pages", 0) + start_page - 1
        _log.info("collect start %s start_page=%s", tid, start_page)
        try:
            result = fetch_pages_for_year(
                symbol,
                year,
                start_page=start_page,
                max_pages_per_task=settings.max_pages_per_year_task,
                end_date=settings.end_date,
                on_page=lambda _page: throttler.after_request(),
            )
            if result is None or not result.bars:
                raise RuntimeError("no bars fetched")

            if result.aborted:
                stats["aborted_ok"] += 1
                _log.warning(
                    "collect aborted %s reason=%s bars=%s pages=%s",
                    tid,
                    result.abort_reason,
                    len(result.bars),
                    len(result.pages_fetched),
                )

            out_path = raw_chunk_path(base, worker_id, symbol, year)
            payload = build_chunk_payload(
                symbol=symbol,
                year=year,
                worker_id=worker_id,
                bars=result.bars,
                pages_fetched=result.pages_fetched,
                end_date=settings.end_date,
            )
            write_chunk(out_path, payload)
            update_cursor_after_fetch(base, symbol, year, result.pages_fetched, result.bars)
            update_task_status(tasks, tid, "done")
            stats["done"] += 1
            append_progress(
                progress_path,
                {
                    "at_iso": utc_now_iso(),
                    "worker_id": worker_id,
                    "task_id": tid,
                    "status": "done",
                    "bar_count": payload["bar_count"],
                    "pages": len(result.pages_fetched),
                    "start_page": start_page,
                    "aborted": result.aborted,
                    "abort_reason": result.abort_reason,
                    "path": str(out_path),
                },
            )
            _log.info(
                "collect done %s bars=%s pages=%s start_page=%s",
                tid,
                payload["bar_count"],
                len(result.pages_fetched),
                start_page,
            )
        except Exception as exc:
            err = str(exc)
            if retry_failed:
                stats["skipped"] += 1
                update_task_status(tasks, tid, "skipped", error=err)
                for t in tasks:
                    if str(t.get("task_id")) == tid:
                        t["_run_skipped"] = True
                append_progress(
                    progress_path,
                    {
                        "at_iso": utc_now_iso(),
                        "worker_id": worker_id,
                        "task_id": tid,
                        "status": "skipped",
                        "error": err,
                        "final_after_retry": True,
                    },
                )
                _log.warning("collect skipped %s (retry failed): %s", tid, exc)
            else:
                stats["failed"] += 1
                update_task_status(tasks, tid, "failed", error=err)
                for t in tasks:
                    if str(t.get("task_id")) == tid:
                        t["_run_failed"] = True
                append_progress(
                    progress_path,
                    {
                        "at_iso": utc_now_iso(),
                        "worker_id": worker_id,
                        "task_id": tid,
                        "status": "failed",
                        "error": err,
                    },
                )
                _log.error("collect failed %s: %s", tid, exc)

        save_tasks_jsonl(tasks_path, tasks)

    stats["elapsed_sec"] = round(time.monotonic() - t0, 1)
    stats["requests"] = throttler.request_count
    _print_run_summary(tasks, stats)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Naver daily archive chunks")
    parser.add_argument("--worker", default=settings.worker_id)
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=settings.max_tasks_per_run,
        help="Max tasks this run (0=unlimited)",
    )
    parser.add_argument("--chunk", type=int, default=settings.chunk_id)
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry failed tasks with same fetch logic; still failing → skipped (final)",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        help="Only collect these symbol codes (optional)",
    )
    args = parser.parse_args()

    worker_id = str(args.worker).strip().lower()
    chunk_id = args.chunk
    _configure_logging(worker_id, chunk_id)
    _log.info(
        "archive_collect worker=%s chunk=%s max_tasks=%s retry_failed=%s",
        worker_id,
        chunk_id,
        args.max_tasks,
        args.retry_failed,
    )

    sym_set = frozenset(str(s).strip() for s in args.symbols) if args.symbols else None

    run_collect(
        worker_id,
        int(args.max_tasks),
        chunk_id=chunk_id if sym_set is None else None,
        retry_failed=args.retry_failed,
        symbols_only=set(sym_set) if sym_set else None,
    )


if __name__ == "__main__":
    main()
