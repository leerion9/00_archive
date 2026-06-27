# Step D — 검증 handoff (2026-06-27)

> **AI/개발자**: Step F(시장구분) 착수 전 이 파일 + [NEXT_STEPS.md](./NEXT_STEPS.md) 를 읽을 것.  
> **known failure(381+980)** 와 **상장폐지(Step G)** 는 **Step F 완료 후 함께** 검토·의사결정 (2026-06-27 사용자 합의).

**마지막 실측**: 2026-06-27 (Step D 옵션 B + C 완료)

---

## Step 구분 (혼동 금지)

| Step | 내용 |
|------|------|
| **F** | 일별 **시장구분** KOSPI/KOSDAQ (`market` sidecar) — **다음 작업** |
| **G** | **상장폐지** 종목 OHLCV·메타 ⏰ — F 완료 **후**, 사용자 확인 **후** |
| **E** | 2019→2000 OHLCV — ⏸️ **스킵** (2026-06-27) |

known failure·partial·none 처리 정책은 **Step G 착수 시 Step F 결과와 함께** 재논의.

---

## Step D 수행 내역 (2026-06-27)

### 옵션 B — 샘플 + 전체 집계 (~30초)

| 검증 | 결과 |
|------|------|
| `archive_merge_validate_samples` (10종) | **10/10 PASS** |
| `archive_enrich_validate_samples` (10종, validator 수정 후) | **10/10 PASS** |
| `report_step_c_status` | 7yr 2,584 / partial 980 / none 381 |
| 전 종목 parquet 집계 (3,945 files, 4,895,211 rows) | 아래 표 |

**Step B null (row-level)**

| 필드 | null | 비율 |
|------|------|------|
| `trading_value` | 0 | 0.00% |
| `value_ma5` | 15,778 | 0.32% (시작 4일 × 종목, 정상) |
| `close_ma5` | 15,778 | 0.32% |

**Step C (row-level, market_cap 컬럼 있는 종목만)**

| 항목 | 값 |
|------|-----|
| `market_cap` 컬럼 **있음** | 3,564 / 3,945 |
| `market_cap` 컬럼 **없음** | **381** (= manifest none) |
| market_cap null (컬럼 있는 row) | 0% |
| `pykrx_mcap` / `etf_aum` | 79.6% / 20.4% (row) |

### 옵션 C — 전 종목 QA (~6.5분)

```powershell
python -m scripts.archive_merge_validate_samples --all   # 3945/3945 PASS (~5분)
python -m scripts.archive_enrich_validate_samples --all  # 3945/3945 PASS (~1.5분)
```

- raw ↔ merged bars **전 종목 일치**
- `trading_value`, `value_ma5`, `close_ma5` **재계산값 전 종목 일치**

### 코드 변경 (validator)

- `core/enrich_validate.py`: Step C sidecar 컬럼(`market_cap` 등) **추가 허용**, Step B 3컬럼 **필수 포함**만 검사
- `scripts/archive_*_validate_samples.py`: **`--all`** 플래그 (전 종목 QA)
- `tests/test_enrich_validate.py`: Step C 컬럼 coexist 테스트

---

## known failure — partial 980 + none 381

Step C manifest 기준 **3,945종** 분류 (상호 배타):

| 구분 | 종목 수 | 의미 |
|------|---------|------|
| **7yr 완료** | 2,584 | 2020~2026 7연도 모두 `pykrx_mcap` 또는 `etf_aum` |
| **partial** | **980** | 일부 연도만 성공 (예: 5/7, 3/7) |
| **none** | **381** | 7연도 전부 실패 — parquet에 **`market_cap` 컬럼 없음** (Step B만) |

**381 + 980 = 1,361종** — 완벽 7년 시총 아님. Step D QA(merge·derived)와 **별개** (시총 커버리지).

### 실패 사유 (누락 코드)

| code | 의미 | retry |
|------|------|-------|
| `empty` | 해당 연도 **merged OHLCV bars 없음** | ❌ (신규상장·OHLCV skip) |
| `failed` | bars 있으나 pykrx / ETF AUM API 실패 | ⚠️ 소수만 조사 가치 |
| (none) | merged 없거나 enrich 전혀 안 됨 | chunk 8 **378** 등 |

### 조사 후보 (Step G 전까지 보류)

| 종목 | 비고 |
|------|------|
| **301410** | chunk 5 none — bars 있으나 `etf_aum`·`pykrx_mcap` 전 연도 failed (ETF API) |

### 백테스트 시 정책 (미확정 → Step G와 함께)

- partial: bars 있는 연도만 `market_cap` 사용, 없는 연도 null
- none 381: `market_cap` sidecar 없음 → 필터 제외 또는 null 처리
- **Step G(상장폐지)** 착수 시 위 1,361종 + 폐지 종목 유니버스를 **함께** 정책 확정

---

## Step C 세션 요약 (chunk 7~8, 동일 일자)

| chunk | 소요 | done/failed | 7yr / partial / none |
|-------|------|-------------|----------------------|
| **7** | ~42분 | 1776 / 1633 | 0 / 486 / 1 |
| **8** | ~19분 | 384 / 3011 | 18 / 89 / 378 |

리포트: `data/naver_daily_archive/reports/enrich_market_cap_c7_20260627.json`, `..._c8_20260627.json`

---

## Step D 판정 (2026-06-27)

| 영역 | 판정 |
|------|------|
| merge (3,945) | ✅ |
| derived (3,945) | ✅ |
| Step B sidecar | ✅ |
| Step C 7yr 완료율 | ⚠️ 2,584/3,945 (known failure 1,361) |
| Step C row 품질 (컬럼 있는 종목) | ✅ null 0% |

**Step D (2020~2026) 검증 완료.** 다음: **Step F**.

---

## 다음 세션 (Step F)

```powershell
cd c:\cursor\00_archive
# 구현 예정: scripts/archive_enrich_market
# pykrx get_market_ticker_list(date, market=KOSPI|KOSDAQ) → features.market
```

**새 채팅 시작 문장**:

> `docs/NEXT_STEPS.md` · `docs/STEP_D_HANDOFF.md` 읽고 Step **F**(일별 KOSPI/KOSDAQ 시장구분 enrich) 착수해줘. Step E 스킵·known failure 381+980은 Step G와 함께 나중에.
