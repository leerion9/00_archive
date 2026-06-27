# 향후 작업 · 리마인더

> **AI/개발자**: ⏰ **Step G(상장폐지)** 시작 시 **반드시 먼저 리마인드**할 것.  
> **Step C handoff**: **[STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md)** 를 **chunk 번호별로** 읽을 것. chunk 1~5를 「재적재 잔여」로 **묶어 요약하지 말 것**. **사용자가 지정한 chunk만** 실행.

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-27 (Step C chunk별 상세 handoff 문서·실측 스크립트 추가)

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

**요약 (2026-06-27 manifest 실측)** — 상세·partial 목록은 handoff 문서 참조:

| chunk | 성격 | 7yr 완료 | partial | none | 다음 액션 (요약) |
|-------|------|----------|---------|------|------------------|
| **0** | 재적재 test | 50/50 | 0 | 0 | 스킵 |
| **1** | 재적재 | 486/488 | 2 | 0 | partial 2종 점검 (012210, 014950) |
| **2** | 재적재 | 484/487 | 3 | 0 | partial 3종 점검 |
| **3** | 재적재 | 471/487 | 16 | 0 | partial 16종 — chunk 3 재실행 또는 retry |
| **4** | 재적재 | 442/487 | 45 | 0 | partial 45종 — chunk 4 재실행 또는 retry |
| **5** | 재적재 | 443/487 | 43 | 1 | partial 43 + none 1 — chunk 5 재실행 또는 retry |
| **6** | 최초 적재 | 189/487 | 297 | 1 | **최초 적재 이어서** (1 chunk) |
| **7** | 최초 적재 | 0/487 | 486 | 1 | **최초 적재** (1 chunk) |
| **8** | 최초 적재 | 18/485 | 89 | 378 | **최초 적재** (6/26 중단, 1 chunk) |

**합계**: 2,583 / 3,945 · partial 981 · none 381

**AI는 사용자 확인 없이 chunk 실행하지 말 것.** 금지: chunk 1~8 for-loop 일괄 실행.

```powershell
cd c:\cursor\00_archive
python -m scripts.archive_enrich_market_cap --chunk 6   # 예: 사용자가 chunk 6 지정 시만
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

**2026-06-26 커밋·푸시됨** (`e95f8ba`): `.cursorrules`, Step C handoff, KRX 세션 갱신  
원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`  
`data/` — git 제외 (로컬)

---

## 새 채팅 시작 문장 (예시)

> `docs/STEP_C_HANDOFF.md` **chunk 6** 섹션 읽고, Step C **chunk 6 최초 적재만** 터미널 실행해줘. (1~8 일괄 실행 금지)

> `docs/STEP_C_HANDOFF.md` **chunk 1** partial 2종(012210, 014950)만 점검해줘.
