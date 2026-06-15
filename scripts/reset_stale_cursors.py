"""Reset cursors stuck beyond Naver page limit (e.g. after bad 789-page run)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from config.settings import settings
from scripts.repair_overfetched import _reset_cursor_from_2026

_log = logging.getLogger("archive")


def reset_stale_cursors(base: Path, worker_id: str, *, min_next_page: int = 800) -> int:
    cur_dir = base / "manifest" / "cursors"
    if not cur_dir.exists():
        return 0
    count = 0
    for path in cur_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if int(data.get("next_page", 1)) >= min_next_page:
                _reset_cursor_from_2026(base, worker_id, path.stem)
                count += 1
        except Exception:
            continue
    return count


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    n = reset_stale_cursors(settings.base_dir, settings.worker_id)
    print(f"reset stale cursors: {n}")


if __name__ == "__main__":
    main()
