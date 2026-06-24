"""Load archive settings from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    worker_id: str
    delay_sec: float
    jitter_sec: float
    batch_size: int
    batch_pause_sec: float
    max_tasks_per_run: int
    year_from: int
    year_to: int
    end_date: str
    symbol_master_path: Path
    pc_year_min: int | None
    num_chunks: int
    chunk_id: int | None
    max_pages_per_year_task: int
    krx_id: str
    krx_pw: str


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    return float(raw)


def _env_optional_int(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    return int(raw)


def load_settings() -> Settings:
    base = Path(os.getenv("ARCHIVE_BASE_DIR", "data/naver_daily_archive"))
    return Settings(
        base_dir=base,
        worker_id=os.getenv("ARCHIVE_WORKER_ID", "pc").strip().lower(),
        delay_sec=_env_float("ARCHIVE_DELAY_SEC", 0.08),
        jitter_sec=_env_float("ARCHIVE_JITTER_SEC", 0.03),
        batch_size=_env_int("ARCHIVE_BATCH_SIZE", 50),
        batch_pause_sec=_env_float("ARCHIVE_BATCH_PAUSE_SEC", 3.0),
        max_tasks_per_run=_env_int("ARCHIVE_MAX_TASKS_PER_RUN", 150),
        year_from=_env_int("ARCHIVE_YEAR_FROM", 2000),
        year_to=_env_int("ARCHIVE_YEAR_TO", 2026),
        end_date=os.getenv("ARCHIVE_END_DATE", "20260531").strip(),
        symbol_master_path=Path(os.getenv("SYMBOL_MASTER_PATH", "data/kr_symbol_master.json")),
        pc_year_min=_env_optional_int("ARCHIVE_PC_YEAR_MIN"),
        num_chunks=_env_int("ARCHIVE_NUM_CHUNKS", 4),
        chunk_id=_env_optional_int("ARCHIVE_CHUNK_ID"),
        max_pages_per_year_task=_env_int("ARCHIVE_MAX_PAGES_PER_YEAR_TASK", 30),
        krx_id=os.getenv("KRX_ID", "").strip(),
        krx_pw=os.getenv("KRX_PW", "").strip(),
    )


settings = load_settings()
