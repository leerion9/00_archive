# Step F — 시장구분 enrich handoff (2026-06-27)

> **AI/개발자**: Step F 구현·스모크 완료. 전체 3,945종 적재는 chunk별 터미널 실행 권장.  
> **Step G(상장폐지)** · **known failure(381+980)** 는 F **완료 후** [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) 와 함께 논의.

**마지막 실측**: 2026-06-27 (chunk **0~3** 전량 적재 **완료**)

---

## 구현 요약

| 항목 | 내용 |
|------|------|
| CLI | `scripts/archive_enrich_market` |
| core | `core/market_fetch.py`, `core/enrich_market.py` |
| 출처 | pykrx `get_market_ticker_list(date, market=KOSPI\|KOSDAQ)` |
| 거래일 | pykrx KOSPI 지수(`1001`) OHLCV 일정 |
| 캐시 | `master/market_daily/{YYYYMMDD}.json` |
| sidecar | `features/{symbol}.parquet` 컬럼 `market` (`KOSPI` \| `KOSDAQ` \| `etf외`) |
| 실패 로그 | `manifest/enrich_market_failures.jsonl` |

### 동작

1. `--years` 구간의 **전체 거래일**에 대해 KOSPI·KOSDAQ 목록 조회 (캐시 재사용)
2. 종목별 features parquet에 **point-in-time** `market` 매핑
3. pykrx 목록에 없는 (날짜, 종목) → `market` null + failures 로그

### chunk 0~3 적재 (2026-06-27)

| chunk | enriched | failed | market null | cache | 소요 |
|-------|----------|--------|-------------|-------|------|
| 0 | 1,000 | 0 | 0.18% | fetch 1,472 + cache 118, **fail 1** | ~22분 |
| 1 | 1,000 | 0 | 13.0% | cache hit | ~32초 |
| 2 | 1,000 | 0 | 42.5% | cache hit | ~29초 |
| 3 | 945 | 0 | 81.3% | cache hit | ~22초 |

**합계 3,945종** · failed 0 · row-level market null **0.48%** (etf외 패치 후, 2026-06-27)

### ETF/ETN → `etf외` (2026-06-27)

- **1,247종** × 전 거래일 `market=etf외` (`--etf-patch`, ~19초)
- `market` 값: `KOSPI` / `KOSDAQ` / `etf외` (ETN 포함)
- null **24.76% → 0.48%** (잔여: 비ETF 상장 전·캐시 1일 등)

- **chunk 4 없음**: `chunks.json` 분할은 **0~3** (4 block)뿐
- chunk 3·tail: ETF·ETN·채권형 비중 → null ↑
- **Step F 완료** → Step G · known failure 논의

---

## 전체 적재 (2020~2026, 3,945종)

**캐시**: 7년 ~1,750 거래일 × 2 API ≈ **첫 실행 30~40분** (이후 chunk는 캐시 hit).

```powershell
cd c:\cursor\00_archive

# chunk 0~3 (chunks.json, ~1000종/block) — 한 세션 1~2 chunk 권장
python -m scripts.archive_enrich_market --chunk 0 --years 2020 2021 2022 2023 2024 2025 2026
python -m scripts.archive_enrich_market --chunk 1 --years 2020 2021 2022 2023 2024 2025 2026
python -m scripts.archive_enrich_market --chunk 2 --years 2020 2021 2022 2023 2024 2025 2026
python -m scripts.archive_enrich_market --chunk 3 --years 2020 2021 2022 2023 2024 2025 2026
```

옵션:

- `--refresh-cache` — `master/market_daily` 재조회
- `--clear-failures` — failures manifest 초기화
- `.env` — `KRX_ID`, `KRX_PW` 필수

---

## 검증 (적재 후)

```powershell
python -m pytest tests/test_enrich_market.py tests/test_market_fetch.py -q
# parquet spot-check (market null 비율, KOSPI/KOSDAQ 분포)
python -c "import pandas as pd; from pathlib import Path; p=Path('data/naver_daily_archive/features'); ..."
```

Step D validator는 Step B 3컬럼 필수 + Step C·F sidecar **추가 허용** (`market` 포함).

---

## Step G / known failure (보류)

- partial **980** + none **381** 시총 미완 → F와 **별개** (merge·derived QA는 PASS)
- 상장폐지 OHLCV·유니버스 정책 → **Step F 전 종목 `market` 적재 완료 후** 사용자 확인

→ [NEXT_STEPS.md](./NEXT_STEPS.md) · [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md)

---

## 새 채팅 시작 문장 (Step G)

> `docs/NEXT_STEPS.md` · `docs/STEP_D_HANDOFF.md` 읽고 Step **G**(상장폐지) + known failure(381+980) 정책 확정·착수해줘.
