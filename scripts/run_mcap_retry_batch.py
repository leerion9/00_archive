"""Run mcap retry batch from manifest JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from config.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run archive_enrich_market_cap for a manifest batch")
    parser.add_argument("manifest", help="e.g. mcap_retry_8a_symbols.json or 8-B")
    args = parser.parse_args()

    base = settings.base_dir
    name = args.manifest
    if not name.endswith(".json"):
        name = f"mcap_retry_{name.lower().replace('-', '')}_symbols.json"
    path = base / "manifest" / Path(name).name
    if not path.exists():
        path = Path(name)
    if not path.exists():
        raise SystemExit(f"manifest not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    chunk = int(payload["chunk"])
    symbols = payload["symbols"]
    batch = payload.get("batch", path.stem)
    if not symbols:
        print(f"{batch}: empty symbol list — skip")
        return

    cmd = [
        sys.executable,
        "-m",
        "scripts.archive_enrich_market_cap",
        "--chunk",
        str(chunk),
        "--symbols",
        *symbols,
    ]
    print(f"=== {batch} chunk={chunk} symbols={len(symbols)} ===")
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
