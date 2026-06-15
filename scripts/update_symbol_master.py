"""
Fetch KOSPI/KOSDAQ symbol master from Naver and save JSON.

  python -m scripts.update_symbol_master
"""

from __future__ import annotations

from config.settings import settings
from core.naver_symbol_master import fetch_kr_symbol_master, save_symbol_master


def main() -> None:
    symbols = fetch_kr_symbol_master(delay_sec=settings.delay_sec)
    save_symbol_master(settings.symbol_master_path, symbols)
    print(f"saved {len(symbols)} symbols -> {settings.symbol_master_path}")


if __name__ == "__main__":
    main()
