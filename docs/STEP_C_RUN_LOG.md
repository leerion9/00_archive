# Step C — 실행·partial retry 로그

> **목적**: chunk별 재적재/partial retry **언제·무엇을·결과·누락 사유**를 남겨, 나중에 빠진 데이터 원인 점검용.  
> manifest 실측 갱신: `python -m scripts.report_step_c_status` → `python -m scripts.update_step_c_handoff`

**누락 사유 코드**

| method / error | 의미 |
|----------------|------|
| `empty` | 해당 연도 **merged OHLCV bars 없음** → enrich 조회 전 종료 (Phase 1 `skipped`/`no bars fetched` 와 대응) |
| `failed` | bars는 있으나 pykrx 시총 또는 ETF AUM 조회 실패 |
| `pykrx_mcap` | 일반주 시총 적재 성공 |
| `etf_aum` | ETF·ETN AUM 적재 성공 |

---

## 2026-06-27 — chunk 1 partial retry

- **명령**: `python -m scripts.archive_enrich_market_cap --chunk 1 --symbols 012210 014950`
- **task**: 14 (2종 × 7연도) · **done** 6 · **failed** 8 · 소요 ~10초
- **리포트**: `data/naver_daily_archive/reports/enrich_market_cap_c1_20260627.json`
- **chunk 1 결과**: 486/488 완료, partial **2** (변화 없음)

| 종목 | 이름 | 유형 | 실패 연도 | 사유 |
|------|------|------|-----------|------|
| 012210 | 삼미금속 | 일반주 | 2020~2022 | `empty` — OHLCV skip (`no bars fetched`) |
| 014950 | 삼익제약 | 일반주 | 2020~2024 | `empty` — OHLCV skip |

→ ETF/ETN 아님. **known failure** (봉 없는 연도).

---

## 2026-06-27 — chunk 2 partial retry

- **명령**: `python -m scripts.archive_enrich_market_cap --chunk 2 --symbols 017860 031210 036220`
- **task**: 21 (3종 × 7연도) · **done** 9 · **failed** 12 · 소요 ~12초
- **리포트**: `data/naver_daily_archive/reports/enrich_market_cap_c2_20260627.json`
- **chunk 2 결과**: 484/487 완료, partial **3** (변화 없음)

| 종목 | 이름 | 유형 | 실패 연도 | 사유 |
|------|------|------|-----------|------|
| 017860 | DS단석 | 일반주 | 2020~2022 | `empty` — OHLCV skip |
| 031210 | 서울보증보험 | 일반주 | 2020~2024 | `empty` — OHLCV skip |
| 036220 | 오상헬스케어 | 일반주 | 2022~2023 | `empty` — OHLCV skip |

→ **known failure**.

---

## 2026-06-27 — chunk 3 partial retry

- **명령**: `python -m scripts.archive_enrich_market_cap --chunk 3 --symbols 059270 061090 062040 064400 068100 079900 081180 086710 088280 088340 089860 092790 096250 098070 099390 099430`
- **task**: 112 (16종 × 7연도) · **done** 60 · **failed** 52 · 소요 ~47초
- **리포트**: `data/naver_daily_archive/reports/enrich_market_cap_c3_20260627.json`
- **chunk 3 결과**: **471/487** 완료, partial **16** (변화 없음)

| 종목 | 7yr | 실패 연도 | 비고 |
|------|-----|-----------|------|
| 059270 | 6/7 | 2020 | `empty` |
| 061090 | 2/7 | 2020~2024 | `empty` — 5연도 OHLCV skip |
| 062040 | 3/7 | 2020~2023 | `empty` |
| 064400 | 2/7 | 2020~2024 | `empty` |
| 068100 | 3/7 | 2020~2023 | `empty` |
| 079900 | 3/7 | 2020~2023 | `empty` |
| 081180 | 2/7 | 2020~2024 | `empty` |
| 086710 | 6/7 | 2020 | `empty` |
| 088280 | 4/7 | 2020~2022 | `empty` |
| 088340 | 3/7 | 2020~2023 | `empty` |
| 089860 | 6/7 | 2020 | `empty` |
| 092790 | 4/7 | 2020~2022 | `empty` |
| 096250 | 2/7 | 2020~2024 | `empty` |
| 098070 | 2/7 | 2020~2024 | `empty` |
| 099390 | 6/7 | 2020 | `empty` |
| 099430 | 6/7 | 2020 | `empty` |

- 성공 task method: 전부 **`pykrx_mcap`** (ETF `etf_aum` 해당 없음)
- 실패 52 task: 전부 **`no market cap (empty)`** — 해당 연도 merged bars 없음
- **chunk 3 재적재 잔여**: partial 16종은 retry 완료, **추가 API 불필요** (known failure로 Step D에 넘김)

---

## 2026-06-27 — chunk 4 partial retry

- **명령**: `python -m scripts.archive_enrich_market_cap --chunk 4 --symbols` (partial 45종, 아래 목록)
- **task**: 315 (45종 × 7연도) · **done** 186 · **failed** 129 · 소요 ~2분
- **methods**: `pykrx_mcap` 179 · **`etf_aum` 7**
- **리포트**: `data/naver_daily_archive/reports/enrich_market_cap_c4_20260627.json`
- **chunk 4 결과**: **443/487** 완료 (+1), partial **44** (−1)

### 개선 (재적재 효과)

| 종목 | 이름 | 변경 |
|------|------|------|
| **117690** | TIGER 차이나항셍30 | **ETF** — 7연도 전부 `etf_aum` 성공 → **partial → 7yr 완료** |

→ 재적재 목적(ETF AUM 대체)이 **이 종목에서 실제 반영**됨.

### 잔여 partial 44종

- 실패 129 task: 전부 **`no market cap (empty)`** — 해당 연도 OHLCV bars 없음 (known failure)
- **chunk 4 재적재 잔여**: partial 44종 retry 완료, **추가 API 불필요** (117690 제외 완료)

**partial 45종 목록** (retry 대상):  
101970, 102370, 105760, 107600, 109670, 111380, 112290, 114840, 117690, 125020, 125490, 126720, 126730, 127980, 129920, 136150, 136410, 137080, 137310, 139990, 140430, 145170, 146060, 146320, 148930, 159010, 160190, 162300, 163280, 163730, 168360, 172670, 177900, 187660, 188040, 188260, 195940, 198940, 199430, 199480, 199550, 199730, 204610, 209640, 212710

---

## 2026-06-27 — chunk 5 partial + none retry

- **명령**: `python -m scripts.archive_enrich_market_cap --chunk 5 --symbols` (partial 43 + none 1 = **44종**)
- **task**: 308 (44종 × 7연도) · **done** 188 · **failed** 120 · 소요 ~2분
- **methods**: `pykrx_mcap` 188 only
- **리포트**: `data/naver_daily_archive/reports/enrich_market_cap_c5_20260627.json`
- **chunk 5 결과**: **443/487** 완료, partial **43**, none **1** (변화 없음)

### none 1종 — ETF AUM 실패 (별도 추적)

| 종목 | 이름 | 유형 | 사유 |
|------|------|------|------|
| **301410** | PLUS 코스닥150선물인버스 | **ETF** | 7연도 전부 `failed` — OHLCV는 있으나 **`etf_aum`·`pykrx_mcap` 모두 실패** (pykrx KRX ETF 시세 API 컬럼 오류 로그). Step D에서 **원인 조사 대상**. |

### 잔여 partial 43종

- 실패 120 task (301410 7 + partial 43종): 대부분 **`empty`** (OHLCV bars 없는 연도)
- **chunk 5 재적재 partial retry**: 43종 **완료**, known failure → Step D

**retry 44종**: 301410, 217590, 226590, 234030, 236810, 240550, 240600, 247660, 248070, 251120, 252990, 254490, 257720, 259960, 261520, 261780, 262840, 271830, 271940, 273640, 274400, 276040, 276730, 277810, 278470, 279570, 282720, 285800, 287840, 288180, 288980, 289220, 289930, 290090, 290560, 291810, 294570, 295310, 296640, 298830, 302440, 303530, 303810, 304360

---

## 2026-06-27 — chunk 6 **최초 적재** (전체)

- **명령**: `python -m scripts.archive_enrich_market_cap --chunk 6`
- **성격**: 최초 적재 (487종 × 7연도 = 3409 task, skip 없음)
- **소요**: ~50분 (10:08~10:58 KST)
- **task**: 3409 · **done** 2810 · **failed** 599
- **methods**: `pykrx_mcap` 1661 · **`etf_aum` 1149**
- **리포트**: `data/naver_daily_archive/reports/enrich_market_cap_c6_20260627.json`
- **7yr 완료**: **189/487** · partial **297** · none **1** (6/26 run과 동일 — failed 다수 `empty`/KRX no-data)

→ chunk 6 **1회 전체 실행 완료**. 7yr 완료율은 failed가 영구적(no bars)인 종목·연도가 많아 **189에서 증가하지 않음**. partial 297·none 1은 Step D known failure.

---

## 다음 세션 (chunk 7 → 8)

| chunk | 명령 | 예상 |
|-------|------|------|
| **7** | `python -m scripts.archive_enrich_market_cap --chunk 7` | ~90분+, KRX 세션 주의 |
| **8** | `python -m scripts.archive_enrich_market_cap --chunk 8` | ~90분+ (6/26 중단분 이어서 **전체 1회**) |

완료 후: `python -m scripts.report_step_c_status` → `python -m scripts.update_step_c_handoff` → 본 RUN_LOG에 섹션 추가.

---
