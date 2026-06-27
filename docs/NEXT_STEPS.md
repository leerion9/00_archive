# 향후 작업 · 리마인더

> **AI/개발자**: ⏰ **Step G(상장폐지)** 시작 시 **반드시 먼저 리마인드**할 것.  
> **Step C handoff**: **[STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md)** 를 **chunk 번호별로** 읽을 것. chunk 1~5를 「재적재 잔여」로 **묶어 요약하지 말 것**. **사용자가 지정한 chunk만** 실행.

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-27 (chunk 0~6 완료·문서 저장 — **다음: chunk 7~8 최초 적재**)

**필독 문서**: [STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md) (chunk별) · [STEP_C_RUN_LOG.md](./STEP_C_RUN_LOG.md) (실행·누락 사유)

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
| **C** | `archive_enrich_market_cap` | 🔄 **[STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md) chunk별 — 미완** |
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

### partial retry vs chunk 전체 (6/27 확정)

| 구분 | 명령 | 용도 |
|------|------|------|
| **partial만** | `--chunk N --symbols A B C ...` | chunk 1~5 잔여 종목 retry (몇 분) |
| **chunk 전체** | `--chunk N` | chunk 6~8 **최초 적재** (~50~90분, skip 없음) |

- chunk 1~5 **partial retry는 6/27 완료** — 잔여는 known failure (봉 없음 / KRX no-data).
- **301410** (chunk 5 none): ETF AUM API 실패 — Step D 조사 대상.

### 스크립트 동작 (handoff 시 오해 금지)

- `archive_enrich_market_cap --chunk N` 은 **해당 chunk 전 종목 × 7연도를 전부 API 호출** (완료분 skip 없음).
- 따라서 **「재적재 이어서」= 사용자가 말한 chunk 번호만** 실행. 다른 chunk는 **최초 적재이거나 아직 손대지 않음**.
- KRX 세션 **~1시간** — chunk 소요 >1h 이면 후반 실패 가능. chunk당 1프로세스·중간 재로그인 이슈 주의.

---

## Step C — chunk별 상세 handoff

**→ [STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md)** (chunk 0~8 **개별 섹션**: 실행 이력, partial 종목 목록, 다음 액션)

**실측 갱신** (세션 종료·chunk 실행 후):

```powershell
cd c:\cursor\00_archive
python -m scripts.report_step_c_status
python -m scripts.update_step_c_handoff
```

**요약 (2026-06-27 manifest 실측)** — 상세·partial 목록: handoff · run log

| chunk | 성격 | 7yr 완료 | partial | none | 상태 |
|-------|------|----------|---------|------|------|
| **0** | 재적재 test | 50/50 | 0 | 0 | ✅ 완료 |
| **1** | 재적재 | 486/488 | 2 | 0 | ✅ partial retry 완료 — known failure 2종 |
| **2** | 재적재 | 484/487 | 3 | 0 | ✅ partial retry 완료 — known failure 3종 |
| **3** | 재적재 | 471/487 | 16 | 0 | ✅ partial retry 완료 — known failure 16종 |
| **4** | 재적재 | 443/487 | 44 | 0 | ✅ partial retry 완료 — **117690** ETF 개선, 잔여 44 known |
| **5** | 재적재 | 443/487 | 43 | 1 | ✅ partial retry 완료 — **301410** ETF 조사, 잔여 43 known |
| **6** | 최초 적재 | 189/487 | 297 | 1 | ✅ **1회 전체 실행 완료(6/27)** |
| **7** | 최초 적재 | 0/487 | 486 | 1 | ❌ **다음 작업** — 1회 전체 실행 |
| **8** | 최초 적재 | 18/485 | 89 | 378 | ❌ chunk 7 후 — 1회 전체 실행 (6/26 중단분) |

**합계**: 2,584 / 3,945 · partial 980 · none 381

**AI는 사용자 확인 없이 chunk 실행하지 말 것.** 금지: chunk 1~8 for-loop 일괄 실행.

```powershell
cd c:\cursor\00_archive
# 다음 세션 (chunk 7만 — 사용자 지정 시)
python -m scripts.archive_enrich_market_cap --chunk 7
```

---

## Step F — 시장구분 (상장폐지 **직전**)

- pykrx `get_market_ticker_list(date, market=KOSPI/KOSDAQ)` → sidecar `market`
- **선행**: Step C 완료 + Step D 검증 (2020~26)
- 구현: `scripts/archive_enrich_market` (예정)

---

## enrich chunk 분할

→ [STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md) chunk 요약표 · `data/naver_daily_archive/config/chunks_enrich.json`

---

## Git

**2026-06-27 커밋·푸시됨** (`9939071`): chunk 0~6 handoff·STEP_C_RUN_LOG  
**2026-06-26** (`b294c52`): STEP_C_HANDOFF·실측 스크립트  
원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`  
`data/` — git 제외 (로컬)

---

## 새 채팅 시작 문장 (chunk 7~8)

> `docs/NEXT_STEPS.md` · `docs/STEP_C_RUN_LOG.md` 읽고, Step C **chunk 7 최초 적재만** 터미널 실행해줘. (chunk 8·1~8 일괄 금지)

> chunk 7 완료 후 **chunk 8** 최초 적재 1회만. 완료 시 `report_step_c_status` → `update_step_c_handoff` → RUN_LOG 갱신.
