# -*- coding: utf-8 -*-
"""OpenDART API client (crtfc_key) with daily quota guard."""

from __future__ import annotations

import io
import json
import logging
import time
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

BASE = "https://opendart.fss.or.kr/api"
_KST = ZoneInfo("Asia/Seoul")
_log = logging.getLogger("archive")

# OpenDART published daily allowance (user-confirmed): 40,000
DART_DAILY_HARD_LIMIT = 40_000
# Stop before the hard ceiling to avoid status=020 lockouts.
DART_DAILY_SOFT_LIMIT = 35_000

REPRT_CODES = {
    "11013": "1Q",
    "11012": "half",
    "11014": "3Q",
    "11011": "annual",
}


class DartApiError(RuntimeError):
    pass


class DartQuotaExceeded(DartApiError):
    pass


@dataclass
class DartQuotaState:
    ymd: str
    count: int
    soft_limit: int
    hard_limit: int

    @property
    def remaining_soft(self) -> int:
        return max(0, self.soft_limit - self.count)


class DartQuotaLedger:
    """Persist per-KST-day request counts so multi-run scrapes stay under quota."""

    def __init__(
        self,
        path: Path,
        *,
        soft_limit: int = DART_DAILY_SOFT_LIMIT,
        hard_limit: int = DART_DAILY_HARD_LIMIT,
    ) -> None:
        self.path = path
        self.soft_limit = int(soft_limit)
        self.hard_limit = int(hard_limit)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def today_ymd() -> str:
        return datetime.now(_KST).strftime("%Y%m%d")

    def _read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"ymd": self.today_ymd(), "count": 0}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"ymd": self.today_ymd(), "count": 0}
        ymd = str(data.get("ymd", ""))
        if ymd != self.today_ymd():
            return {"ymd": self.today_ymd(), "count": 0}
        return {"ymd": ymd, "count": int(data.get("count", 0) or 0)}

    def _write(self, ymd: str, count: int) -> None:
        payload = {
            "ymd": ymd,
            "count": int(count),
            "soft_limit": self.soft_limit,
            "hard_limit": self.hard_limit,
            "updated_at_iso": datetime.now(_KST).isoformat(timespec="seconds"),
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def state(self) -> DartQuotaState:
        raw = self._read()
        return DartQuotaState(
            ymd=str(raw["ymd"]),
            count=int(raw["count"]),
            soft_limit=self.soft_limit,
            hard_limit=self.hard_limit,
        )

    def reserve(self, n: int = 1) -> DartQuotaState:
        """Atomically check+increment. Raises if soft limit would be exceeded."""
        raw = self._read()
        ymd = str(raw["ymd"])
        count = int(raw["count"])
        n = max(1, int(n))
        if count + n > self.soft_limit:
            self._write(ymd, count)
            raise DartQuotaExceeded(
                f"DART 일일 soft limit 도달: {count}/{self.soft_limit} "
                f"(hard={self.hard_limit}, ymd={ymd}). 내일 이어서 수집하세요."
            )
        count += n
        self._write(ymd, count)
        if count >= int(self.soft_limit * 0.9):
            _log.warning(
                "DART quota high: %s/%s (hard=%s)",
                count,
                self.soft_limit,
                self.hard_limit,
            )
        return DartQuotaState(
            ymd=ymd,
            count=count,
            soft_limit=self.soft_limit,
            hard_limit=self.hard_limit,
        )


class DartClient:
    def __init__(
        self,
        api_key: str,
        *,
        delay_sec: float = 0.15,
        quota_path: Optional[Path] = None,
        soft_limit: int = DART_DAILY_SOFT_LIMIT,
        hard_limit: int = DART_DAILY_HARD_LIMIT,
    ) -> None:
        key = (api_key or "").strip()
        if not key:
            raise DartApiError(
                "DART_API_KEY(crtfc_key)가 없습니다. "
                "opendart.fss.or.kr 에서 인증키를 발급해 .env 에 넣으세요. "
                "(KRX_ID/KRX_PW 는 DART 키가 아닙니다.)"
            )
        self.api_key = key
        self.delay_sec = float(delay_sec)
        self.session = requests.Session()
        self._corp_map: Optional[Dict[str, str]] = None  # stock_code -> corp_code
        qpath = quota_path or Path("data/naver_daily_archive/master/dart_quota.json")
        self.quota = DartQuotaLedger(
            qpath, soft_limit=soft_limit, hard_limit=hard_limit
        )

    def _before_request(self) -> None:
        self.quota.reserve(1)
        time.sleep(self.delay_sec)

    def _get_json(self, path: str, params: Dict[str, Any]) -> dict:
        self._before_request()
        q = dict(params)
        q["crtfc_key"] = self.api_key
        resp = self.session.get(f"{BASE}/{path}", params=q, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        status = str(data.get("status", ""))
        if status != "000":
            msg = data.get("message", "")
            if status == "013":
                return data
            if status == "020":
                raise DartQuotaExceeded(
                    f"DART 요청 제한 초과(status=020): {msg}. 오늘 수집 중단."
                )
            raise DartApiError(f"DART {path} status={status} message={msg}")
        return data

    def download_corp_codes(self, cache_path: Path) -> Dict[str, str]:
        """Return mapping stock_code(6) -> corp_code(8). Cache zip/xml locally."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        xml_path = cache_path.with_suffix(".xml")
        if not xml_path.exists():
            self._before_request()
            resp = self.session.get(
                f"{BASE}/corpCode.xml",
                params={"crtfc_key": self.api_key},
                timeout=120,
            )
            resp.raise_for_status()
            try:
                zf = zipfile.ZipFile(io.BytesIO(resp.content))
            except zipfile.BadZipFile as exc:
                # Error payload may be JSON with status
                try:
                    err = resp.json()
                    if str(err.get("status")) == "020":
                        raise DartQuotaExceeded(
                            f"DART corpCode 제한 초과: {err.get('message')}"
                        ) from exc
                except DartQuotaExceeded:
                    raise
                except Exception:
                    pass
                raise DartApiError(
                    f"corpCode.xml zip 실패 (키가 잘못됐거나 차단). detail={resp.text[:200]}"
                ) from exc
            name = zf.namelist()[0]
            xml_bytes = zf.read(name)
            xml_path.write_bytes(xml_bytes)
            cache_path.write_bytes(resp.content)

        root = ET.parse(xml_path).getroot()
        out: Dict[str, str] = {}
        for el in root.iter("list"):
            stock = (el.findtext("stock_code") or "").strip()
            corp = (el.findtext("corp_code") or "").strip()
            if len(stock) == 6 and stock.isdigit() and len(corp) == 8:
                out[stock] = corp
        self._corp_map = out
        return out

    def corp_code_for(self, symbol: str, cache_path: Path) -> str:
        sym = str(symbol).zfill(6)
        if self._corp_map is None:
            self.download_corp_codes(cache_path)
        assert self._corp_map is not None
        code = self._corp_map.get(sym)
        if not code:
            raise DartApiError(f"DART corp_code 없음: symbol={sym}")
        return code

    def fetch_major_accounts(
        self, *, corp_code: str, bsns_year: int, reprt_code: str
    ) -> List[dict]:
        data = self._get_json(
            "fnlttSinglAcnt.json",
            {
                "corp_code": corp_code,
                "bsns_year": str(bsns_year),
                "reprt_code": str(reprt_code),
            },
        )
        if str(data.get("status")) == "013":
            return []
        rows = data.get("list") or []
        return list(rows) if isinstance(rows, list) else []
