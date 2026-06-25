# 향후 작업 · 리마인더

> **AI/개발자**: 이 파일의 ⏰ 항목은 Phase 2(상장폐지) 시작 시 **반드시 먼저 리마인드**할 것.

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-25

---

## ⏰ 상장폐지 종목 (Phase 2 / Step F) — 순서 엄수

**2차 필드 enrich·merge 완료 후** 착수. OHLCV 수집 전에:

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

## Step A~F 진행 (2026-06-25)

| Step | 내용 | 상태 |
|------|------|------|
| **A** | `archive_merge` (3,945종) | ✅ |
| **B** | `archive_enrich_derived` (3,945종) | ✅ |
| **C** | `archive_enrich_market_cap` | 🔄 **재적재 필요** (아래) |
| **D** | 검증·status | ❌ |
| **E** | 2019→2000 OHLCV | ❌ |
| **F** | 상장폐지 ⏰ | 보류 |

---

## Step C — 시총 enrich (즉시 다음)

### 정책 (2026-06-25 확정 · 코드 반영됨)

| 종류 | `market_cap` | method |
|------|--------------|--------|
| **일반주** | pykrx 일별 시가총액 | `pykrx_mcap` |
| **ETF·ETN** | **NAV × 일별 상장좌수 (AUM)** | `etf_aum` |
| **fallback** | ❌ Naver 현재주식수×종가 **사용 안 함** |
| **실패** | `manifest/enrich_mcap_failures.jsonl` 기록 → 나중에 검토 |

- ETF AUM: KRX `개별종목시세_ETF` API (`LST_NAV` × `LIST_SHRS`)
- `.env`에 `KRX_ID`, `KRX_PW` 필요 (pykrx KRX 로그인)
- enrich chunk: `data/naver_daily_archive/config/chunks_enrich.json` (9분할, chunk 0=test 50종)

### 로컬 데이터 상태 (주의)

1. **구 Step C** (2026-06-24): chunk enrich **0~5** 1회차 완료 (`etf_nav` / `shares_x_close` / `pykrx_mcap` 혼재)
2. **버그 재적재** (2026-06-25 저녁): ETF AUM 로직 오류로 **ETF 다수 failed**, sidecar mcap 공백·오류 가능
3. **수정 코드 재적재** (2026-06-25 23:41~): **chunk 0만 완료** (350/350) 후 **중단** — chunk 1~5 **미완**

### 다음 실행 (새 채팅에서)

```powershell
cd c:\cursor\00_archive
# chunk 1~5 순차 (chunk 0 test는 23:41 run 완료 — 스킵 가능)
python -m scripts.archive_enrich_market_cap --chunk 1
python -m scripts.archive_enrich_market_cap --chunk 2
# … chunk 5까지
# 완료 후 chunk 6~8 (미착수)
```

실패 목록: `data/naver_daily_archive/manifest/enrich_mcap_failures.jsonl`

---

## enrich chunk 분할 (Step C, 9분할)

| chunk | 범위 | 역할 |
|-------|------|------|
| 0 | 000020~000815 | test (50) |
| 1~8 | prod ~487종/chunk | 시총 enrich |

---

## OHLCV chunk (4등분, collect용)

| chunk | 코드 범위 |
|-------|-----------|
| 0 | 000020 ~ 051500 |
| 1 | 051600 ~ 214330 |
| 2 | 214370 ~ 433500 |
| 3 | 433880 ~ 950250 |

---

## Git

- 원격: [leerion9/00_archive](https://github.com/leerion9/00_archive)
- 브랜치: `master`
- `raw/`, `merged/`, `features/`, `manifest/` — **git 제외**, PC 로컬

---

## 새 채팅 시작 문장 (예시)

> `docs/NEXT_STEPS.md` handoff(2026-06-25) 기준 Step C 시총 enrich **chunk 1부터** 재적재 이어서 해줘.
