# 수집·보강 계획 (2026-06-23 확정)

> **원칙**: Phase 1 OHLCV와 동일하게 **한꺼번에 하지 않고 단계별** 진행.  
> 각 Step 완료 후 manifest/status 확인 → 다음 Step.

---

## 의사결정 (확정)

| # | 항목 | 방침 |
|---|------|------|
| 1 | **거래대금** | `종가 × 거래량` 계산 (근사치로 충분) |
| 2 | **시가총액** | **일별** pykrx 수집 후 저장 |
| 3 | **저장 구조** | OHLCV `bars`는 유지, 보강·파생 필드는 **sidecar** |
| 4 | **상장폐지** | 2차 필드·merge 완료 **후** Phase 2 (⏰ 리마인드) |
| 5 | **ETF·ETN 규모** | **AUM = NAV × 일별 상장좌수** → `market_cap` (`etf_aum`); Naver 근사 fallback 없음 |
| 6 | **파생 저장** | **거래대금 5일 평균**(`value_ma5`), **종가 5일선**(`close_ma5`) 계산 후 sidecar 저장 |

---

## Phase 1 OHLCV — 완료 (2020~2026)

| 연도 | done | skipped | failed | pending | 상태 |
|------|------|---------|--------|---------|------|
| 2026 | 3,945 | 2 | 0 | 0 | ✅ |
| 2025 | 3,898 | 49 | 0 | 0 | ✅ |
| 2024 | 3,726 | 221 | 0 | 0 | ✅ |
| 2023 | 3,371 | 576 | 0 | 0 | ✅ |
| 2022 | 3,084 | 863 | 0 | 0 | ✅ |
| 2021 | 2,849 | 1,098 | 0 | 0 | ✅ |
| 2020 | 2,619 | 1,328 | 0 | 0 | ✅ |

- 종목 수: **3,947** / 연도, 합계 **27,629** task
- skip: ETF·신규상장·네이버 데이터 없음 등 (~15%, 연도·chunk마다 상이)
- raw: `data/naver_daily_archive/raw/pc/{symbol}/{year}.json`

---

## Sidecar 스키마 (목표)

```
merged/{symbol}.json                 # Phase 1 bars (OHLCV, 변경 없음)
features/{symbol}.parquet            # date index sidecar (신규)
```

| 컬럼 | 출처 | 비고 |
|------|------|------|
| `trading_value` | close × volume | Step B |
| `value_ma5` | trading_value 5일 rolling | Step B |
| `close_ma5` | close 5일 rolling | Step B |
| `market_cap` | pykrx 일별 시총 / ETF·ETN AUM(NAV×상장좌수) | Step C |
| `market_cap_method` | `pykrx_mcap` \| `etf_aum` | Step C |
| `shares_outstanding` | pykrx 일별 | ETF AUM·검증용 |

---

## 단계별 실행 순서

### Step A — `archive_merge` (Phase 1b) ✅

**목적**: raw 연도 chunk → 종목별 통합 bars

- [x] `merged/{symbol}.json` 생성 (2020~2026, 3,945종)
- [x] merge 리포트 (`reports/merge_report_20260624.json`)

```powershell
cd c:\cursor\00_archive
# python -m scripts.archive_merge   # 구현 후
```

**선행**: Phase 1 OHLCV ✅  
**다음**: Step B

---

### Step B — `archive_enrich_derived` (API 없음) ✅

**목적**: bars만으로 계산 가능한 sidecar 필드

- [x] `trading_value` = close × volume
- [x] `value_ma5`, `close_ma5`
- [x] manifest: `manifest/enrich_tasks.jsonl` (derived 3,945종)

```powershell
# python -m scripts.archive_enrich_derived --years 2020 2021 2022 2023 2024 2025 2026
```

**선행**: Step A  
**다음**: Step C

---

### Step C — `archive_enrich_market_cap` (pykrx) 🔄

**목적**: 일별 규모(`market_cap`) sidecar 보강

| 종류 | API | method |
|------|-----|--------|
| 주식 | `get_market_cap_by_date` | `pykrx_mcap` |
| ETF·ETN | KRX `개별종목시세_ETF`: **NAV × LIST_SHRS** | `etf_aum` |

- **Naver 현재주식수×종가 fallback 없음** — 실패 시 `manifest/enrich_mcap_failures.jsonl`
- [x] 구현·chunk enrich 0~5 1차 실행 (2026-06-24, 구 `etf_nav` 방식)
- [x] **2026-06-25** 정책 반영 코드 (`etf_aum`, fallback 제거)
- [ ] **chunk 1~8 재적재** (chunk 0 test 재완료, chunk 1~5·6~8 남음) → [NEXT_STEPS.md](./NEXT_STEPS.md)

```powershell
python -m scripts.archive_enrich_market_cap --chunk N
# enrich chunk 0=test, 1~8=prod (chunks_enrich.json)
```

**선행**: Step B (bars·date join 검증)  
**다음**: Step D

---

### Step D — 검증·리포트

- [ ] 샘플 종목: merged bars ↔ features sidecar date join
- [ ] null·method 분포 (stock vs etf)
- [ ] repair_v13 필터 재현 가능 여부 (point-in-time 시총 percentile)

```powershell
# python -m scripts.archive_status --fields
```

**선행**: Step C  
**다음**: Step E (병렬 가능) 또는 백테스트 연동

---

### Step E — OHLCV 역순 계속 (2019 → 2000)

**Phase 1 패턴 반복** (chunk 0→3, retry, 연도별):

1. `archive_plan --years YYYY --append`
2. `archive_collect --chunk N` × 4
3. `--retry-failed` (chunk별 + 연도 마무리 시 전체)
4. **해당 연도 merge → Step B → Step C** (또는 연도 묶음 batch)

- [ ] 2019 OHLCV
- [ ] 2018 …
- [ ] 2000

> Step A~D를 2020~26 전체에 먼저 끝낸 뒤, 2019 OHLCV와 **병렬**로 진행해도 됨.

---

### Step F — Phase 2 상장폐지 ⏰ (보류 · 리마인드)

**2차 필드·2019~ merge/enrich 완료 후** 착수. 순서 엄수:

1. FDR `StockListing('KRX-DELISTING')` → 연도별 폐지 종목·건수 **보고**
2. 사용자 확인
3. `listing_events.json` (상장일·폐지일)
   - v1: FDR `StockListing('KRX')` (현재 상장)
   - v2: FDR `StockListing('KRX-DELISTING')`
4. 폐지 종목 OHLCV (FDR / pykrx / 네이버 fallback)

→ [NEXT_STEPS.md](./NEXT_STEPS.md) ⏰ 항목 참고

---

## chunk 분할 (OHLCV·enrich 공통)

| chunk | 코드 범위 | 종목 수 |
|-------|-----------|---------|
| 0 | 000020 ~ 051500 | 1,000 |
| 1 | 051600 ~ 214330 | 1,000 |
| 2 | 214370 ~ 433500 | 1,000 |
| 3 | 433880 ~ 950250 | 947 |

설정: `data/naver_daily_archive/config/chunks.json`

---

## 백테스트 연동 (repair_v13 개선)

| repair_v13 | 아카이브 |
|------------|----------|
| 시총 상위 10% (스냅샷 ❌) | **일별** `market_cap` + 날짜별 cross-section percentile |
| 거래대금 폭발 | `trading_value`, `value_ma5` |
| 5일선 필터 | `close_ma5` |
| K=0.7 돌파 | bars OHLC (백테스트 시 계산) |

---

## Git·데이터 경로

- 수집 데이터(`raw/`, `merged/`, `features/`, `manifest/`) — **git 제외**, PC 로컬
- 원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`

```
data/naver_daily_archive/
├── raw/pc/{symbol}/{year}.json
├── merged/{symbol}.json
├── features/{symbol}.parquet          # Step B·C
├── manifest/tasks.jsonl
├── manifest/enrich_tasks.jsonl        # Step B·C (예정)
└── master/listing_events.json         # Step F (예정)
```

---

## 다음 작업 (즉시)

1. **Step A** — `archive_merge` 구현·실행 (2020~2026)
2. **Step B** — `archive_enrich_derived` 구현
3. **Step C** — `archive_enrich_market_cap` 구현

(스크립트 미구현 — Step A부터 순차 개발)
