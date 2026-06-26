# 향후 작업 · 리마인더

> **AI/개발자**: 이 파일의 ⏰ 항목은 **Step G(상장폐지)** 시작 시 **반드시 먼저 리마인드**할 것.  
> **Step C handoff**: 아래 **「Step C 작업 이력·chunk 상태표」** 를 **새 채팅에서 가장 먼저** 읽고, **사용자가 지정한 chunk만** 실행할 것.

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-26 (세션 종료 — Step C 추가 실행 없음, 문서·코드만 커밋)

---

## ⏰ 상장폐지 종목 (Phase 2 / Step G) — 순서 엄수

**Step F(시장구분)·2차 필드 enrich·merge 완료 후** 착수. OHLCV 수집 전에:

1. **연도별 상장폐지 종목 리스트** — FDR `StockListing('KRX-DELISTING')` + 폐지일 기준 연도별 집계
2. **연도별 몇 종목인지** 규모 파악 → 사용자에게 보고
3. 사용자 확인 후 폐지 종목 **가격·메타** 수집 (FDR / pykrx / 네이버 fallback)

→ `master/listing_events.json` (`archive_listing_events`, 구현 예정)

---

## Phase 1 OHLCV — **2020~2026 완료** ✅

| 연도 | done | skipped |
|------|------|---------|
| 2026~2020 | (각 3,947 task) | 연도별 skip ~2~1,328 |

---

## Step A~G 진행

| Step | 내용 | 상태 |
|------|------|------|
| **A** | `archive_merge` (3,945종) | ✅ |
| **B** | `archive_enrich_derived` (3,945종) | ✅ |
| **C** | `archive_enrich_market_cap` | 🔄 **아래 chunk표 기준 — 미완** |
| **D** | 검증·status | ❌ (Step C 완료 후) |
| **E** | 2019→2000 OHLCV | ❌ |
| **F** | 일별 시장구분 KOSPI/KOSDAQ | ❌ — Step G 직전 |
| **G** | 상장폐지 ⏰ | 보류 |

---

## Step C — 용어·범위 (반드시 구분)

| 용어 | 의미 | 해당 chunk |
|------|------|------------|
| **재적재** | 6/24 구코드(`etf_nav` 등)로 **잘못 넣은 sidecar**를 `etf_aum`/`pykrx_mcap` 정책으로 **덮어쓰기** | **chunk 0~5** (6/24에 구방식 실행됨) |
| **최초 적재** | 수정 코드(`etf_aum`) 기준으로 **한 번도 끝까지 돌린 적 없음** | **chunk 6~8** |
| **OHLCV 수집** | ❌ Step C 아님 — `archive_collect` / 네이버 `sise_day` | Step E |

- 대상: 기존 `merged/{symbol}.json` (3,945종) + 연도 **2020~2026** 만.
- 출력: `features/{symbol}.parquet` 의 `market_cap`, `market_cap_method` 등 sidecar.
- **9 chunk 분할 이유**: chunk당 ~30~90분 → **한 세션에 1~3 chunk만**. 사용자 지정 없이 **1~8 일괄 실행 금지**.

### 정책 (코드 반영됨, commit `bfc0eab`)

| 종류 | `market_cap` | method |
|------|--------------|--------|
| 일반주 | pykrx 일별 시가총액 | `pykrx_mcap` |
| ETF·ETN | NAV × 일별 상장좌수 (AUM) | `etf_aum` |
| fallback | ❌ Naver 주식수×종가 없음 | |
| 단위 | **원(₩)** | |
| 실패 | `manifest/enrich_mcap_failures.jsonl` | |

`.env`: `KRX_ID`, `KRX_PW`  
설정: `data/naver_daily_archive/config/chunks_enrich.json`

### 스크립트 동작 (handoff 시 오해 금지)

- `archive_enrich_market_cap --chunk N` 은 **해당 chunk 전 종목 × 7연도를 전부 API 호출** (완료분 skip 없음).
- 따라서 **「재적재 이어서」= 사용자가 말한 chunk 번호만** 실행. 다른 chunk는 **최초 적재이거나 아직 손대지 않음**.
- KRX 세션 **~1시간** — chunk 소요 >1h 이면 후반 실패 가능. chunk당 1프로세스·중간 재로그인 이슈 주의.

---

## Step C 작업 이력 (타임라인)

| 일자 | 내용 |
|------|------|
| **6/24** | Step C **chunk 0~5** 1차 실행 — 구방식 **`etf_nav`** 혼재 → **재적재 대상** |
| **6/25** | ETF AUM 버그 수정 (`etf_aum`), fallback 제거 (`bfc0eab`) |
| **6/25 23:41** | **chunk 0** (test 50종) 수정 코드로 **재적재 완료** ✅ |
| **6/25 23:44~** | **chunk 1** 재적재 시작 → ~1050/3416 **중단** |
| **6/26 11:28~18:47** | ⚠️ AI가 **chunk 1~8 전부** 일괄 실행 (사용자 의도: **chunk 1 재적재 이어서**만) |
| **6/26 18:49~22:45** | ⚠️ AI가 **chunk 4~8** 추가 일괄 재실행 → chunk 8 **사용자 중단** |

**6/26 세션 교훈**: handoff에 「chunk 1~8 재적재」라고만 적혀 있어 AI가 **최초 적재 chunk(6~8)까지 포함 일괄 실행**. chunk **역할(재적재 vs 최초)** 과 **다음 chunk 번호**를 표로 명시해야 함.

---

## Step C chunk 상태표 (2026-06-26 23:00 KST 기준)

**완료 기준**: 종목당 2020~2026 **7연도** 모두 `pykrx_mcap` 또는 `etf_aum` done.  
**manifest**: `enrich_tasks.jsonl` — 동일 `task_id`는 **마지막 줄이 최신**.

| chunk | 코드 범위 | 작업 성격 | 6/26 이전 | **현재 (6/26 후)** | 다음 액션 |
|-------|-----------|-----------|-----------|-------------------|-----------|
| **0** | 000020~000815 | 재적재 (test) | ✅ 6/25 완료 | **50/50 완료** | **스킵** |
| **1** | 000850~014950 | **재적재** | ~1050/3416 중단 | **486/488** 완료, 2 partial | partial·실패만 점검 후 **스킵 가능** (사용자 확인) |
| **2** | 014970~053050 | **재적재** | 미완 | **484/487** 완료, 3 partial | 위와 동일 |
| **3** | 053060~101670 | **재적재** | 구 `etf_nav` | **471/487** 완료, 16 partial | partial 잔여·실패 retry |
| **4** | 101680~214320 | **재적재** | 구 `etf_nav` | **442/487** 완료, 45 partial | partial 잔여·실패 retry |
| **5** | 214330~305720 | **재적재** | 구 `etf_nav` | **443/487** 완료, 43 partial | partial 잔여·실패 retry |
| **6** | 306040~425040 | **최초 적재** | **미착수** | **189/487** 완료, 297 partial | **최초 적재 이어서** (1 chunk씩) |
| **7** | 425420~488720 | **최초 적재** | **미착수** | **0/487** 7연도완료, 486 partial | **최초 적재** (세션·시간 주의) |
| **8** | 488770~950250 | **최초 적재** | **미착수** | **18/485** 완료, 378 none | **최초 적재** (6/26 chunk8 **중단**) |

**합계**: **2,583 / 3,945** 종목 7연도 완료 · partial 981 · none 381  
**실패 log**: `manifest/enrich_mcap_failures.jsonl` (~5,500 task, 연도·종목별 KRX no-data 포함)

### 6/26 일괄 실행 run 요약 (로그·reports)

| chunk | run | done | failed | 비고 |
|-------|-----|------|--------|------|
| 1 | 6/26 11:28 | 3408 | 8 | 재적재 — 대체로 OK |
| 2 | 6/26 11:59 | 3397 | 12 | 재적재 — 대체로 OK |
| 3 | 6/26 12:28 | 3357 | 52 | 재적재 |
| 4 | 6/26 13:05 | 3279 | 130 | 재적재, ~94분 (세션 경계) |
| 5 | 6/26 14:39 | 3289 | 120 | 재적재, ~107분 |
| 6 | 6/26 16:26 | 2810 | 599 | **최초**인데 재실행됨, 후반 실패多 |
| 7 | 6/26 17:32 | 1775 | 1634 | **최초**, 대량 partial |
| 8 | 6/26 18:25 | 384 | 3011 | **최초**, 6/26 retry **중단** |

리포트: `data/naver_daily_archive/reports/enrich_market_cap_c{N}_20260626.json`

---

## Step C — **다음에 할 일** (사용자 지정 후)

**AI는 아래를 사용자 확인 없이 실행하지 말 것.**

1. **재적재 잔여 (chunk 1~5)** — 이미 대부분 덮어씀. 필요 시 **partial 종목만** `--symbols` 로 (스크립트·목록 정리는 미구현 → chunk 단위 재실행 시 **중복 API** 발생).
2. **최초 적재 (chunk 6 → 7 → 8 순)** — **한 번에 1 chunk** 권장.

```powershell
cd c:\cursor\00_archive
# 예: 최초 적재 chunk 6만 (사용자가 「chunk 6만」이라고 할 때)
python -m scripts.archive_enrich_market_cap --chunk 6
```

**금지 예**: `chunk 1`부터 `8`까지 for-loop 일괄 실행.

### 코드 변경 (6/26, 미커밋)

- `core/market_cap_fetch.py`: `refresh_krx_session()` — KRX 세션 갱신
- `core/enrich_market_cap.py`: 500 task마다 세션 갱신  
→ 효과 검증 전. 커밋·추가 chunk 실행은 **사용자 확인 후**.

---

## Step F — 시장구분 (상장폐지 **직전**)

- pykrx `get_market_ticker_list(date, market=KOSPI/KOSDAQ)` → sidecar `market`
- **선행**: Step C 완료 + Step D 검증 (2020~26)
- 구현: `scripts/archive_enrich_market` (예정)

---

## enrich chunk 분할 (Step C, 9분할)

| chunk | 범위 | 종목 수 | 성격 |
|-------|------|---------|------|
| 0 | 000020~000815 | 50 | test · 재적재 ✅ |
| 1 | 000850~014950 | 488 | prod · **재적재** |
| 2 | 014970~053050 | 487 | prod · **재적재** |
| 3 | 053060~101670 | 487 | prod · **재적재** |
| 4 | 101680~214320 | 487 | prod · **재적재** |
| 5 | 214330~305720 | 487 | prod · **재적재** |
| 6 | 306040~425040 | 487 | prod · **최초 적재** |
| 7 | 425420~488720 | 487 | prod · **최초 적재** |
| 8 | 488770~950250 | 485 | prod · **최초 적재** |

---

## Git (미커밋 로컬 변경)

- `.cursorrules` (신규)
- `docs/NEXT_STEPS.md`, `docs/COLLECTION_PLAN.md`
- `core/market_cap_fetch.py`, `core/enrich_market_cap.py` (KRX 세션, 6/26)

원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`  
`data/` — git 제외

---

## 새 채팅 시작 문장 (예시)

> `docs/NEXT_STEPS.md` handoff(2026-06-26) **chunk 상태표** 읽고, Step C **chunk 6 최초 적재만** 터미널 실행해줘. (1~8 일괄 실행 금지)

> 재적재: chunk 3 partial 잔여만 점검해줘.
