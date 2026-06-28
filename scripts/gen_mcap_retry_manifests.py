"""Generate mcap retry batch manifests (8-B/C/D) from step_c_status snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from config.settings import settings


def main() -> None:
    base = settings.base_dir
    snap_path = base / "reports" / "step_c_status_snapshot.json"
    if not snap_path.exists():
        raise SystemExit(f"missing snapshot: {snap_path}")

    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    none_syms = sorted(snap["chunks"]["8"].get("none_symbols") or [])

    a_path = base / "manifest" / "mcap_retry_8a_symbols.json"
    a_syms = set(json.loads(a_path.read_text(encoding="utf-8"))["symbols"]) if a_path.exists() else set()
    remaining = [s for s in none_syms if s not in a_syms]

    batch_size = 95
    manifest_dir = base / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    for i, label in enumerate(["8-B", "8-C", "8-D"], start=1):
        batch = remaining[(i - 1) * batch_size : i * batch_size]
        out = manifest_dir / f"mcap_retry_{label.lower().replace('-', '')}_symbols.json"
        payload = {"chunk": 8, "batch": label, "symbols": batch}
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{label}: {len(batch)} symbols -> {out.name}")


if __name__ == "__main__":
    main()
