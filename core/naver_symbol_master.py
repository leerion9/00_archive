"""
Naver sise_market_sum: KOSPI/KOSDAQ symbol code -> name (from moa core/naver_symbol_master.py).
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

_log = logging.getLogger("archive")

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}
_MARKET_SUM_URL = "https://finance.naver.com/sise/sise_market_sum.naver"
_MAX_PAGES_PER_MARKET = 120


def _parse_market_sum_codes_names(html: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.type_2")
    if not table:
        return []
    out: List[Tuple[str, str]] = []
    for tr in table.select("tbody tr"):
        tds = tr.find_all("td")
        if len(tds) < 10:
            continue
        a = tr.select_one("a[href*='main.naver?code=']")
        if not a:
            continue
        m = re.search(r"code=(\d{6})", a.get("href", ""))
        if not m:
            continue
        name = a.get_text(strip=True)
        if not name:
            continue
        out.append((m.group(1), name))
    return out


def fetch_kr_symbol_master(delay_sec: float = 0.05) -> Dict[str, str]:
    session = requests.Session()
    session.headers.update(_UA)
    merged: Dict[str, str] = {}
    for sosok in (0, 1):
        for page in range(1, _MAX_PAGES_PER_MARKET + 1):
            resp = session.get(
                _MARKET_SUM_URL,
                params={"sosok": sosok, "page": page},
                timeout=20,
            )
            resp.encoding = "euc-kr"
            resp.raise_for_status()
            rows = _parse_market_sum_codes_names(resp.text)
            if not rows:
                break
            for code, name in rows:
                merged[code] = name
            time.sleep(delay_sec)
    _log.info("Naver symbol master: %s codes", len(merged))
    return merged


def save_symbol_master(path: Path, symbols: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "naver_sise_market_sum",
        "count": len(symbols),
        "symbols": dict(sorted(symbols.items(), key=lambda x: x[0])),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_symbol_master(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        syms = raw.get("symbols")
        if isinstance(syms, dict):
            return {str(k).strip(): str(v).strip() for k, v in syms.items() if str(k).strip()}
    except Exception:
        return {}
    return {}
