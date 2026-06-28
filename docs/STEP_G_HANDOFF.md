# Step G — 상장/폐지 메타 + 상폐 주권 보강 handoff

> **AI/개발자**: Step G **실행 전 이 파일 전체** + [NEXT_STEPS.md](./NEXT_STEPS.md) 를 읽을 것.  
> **실제 수집·적재는 새 채팅에서** 사용자 지정 chunk/단계만 터미널 실행 (일괄 for-loop 금지).

**마지막 갱신**: 2026-06-28 (g0~g4 ✅ · Phase 1 ✅ · mcap 4종 무시)

**선행 완료**: Step A~D ✅ · Step F ✅ · Step E ⏸️ · **Phase 1** → [PHASE1_HANDOFF.md](./PHASE1_HANDOFF.md)

**mcap retry 이어하기**: [STEP_C_MCAP_RETRY_HANDOFF.md](./STEP_C_MCAP_RETRY_HANDOFF.md)

---

## Step G phase (g0~g4 · 5단계)

| Phase | 내용 | 상태 |
|-------|------|------|
| **g0** | 190종 마스터 + 연도별 상폐 리포트 JSON | ✅ 2026-06-28 |
| **g1** | `listing_events.json` (4,137종) | ✅ 2026-06-28 |
| **g2** | 190종 OHLCV (2020~2026) | ✅ 2026-06-28 |
| **g3** | 190종 merge·B·C·F | ✅ 2026-06-28 |
| **g4** | 검증 | ✅ 2026-06-28 |

> **넘버링**: 이번 Step G는 **g0~g4 고정**. 앞으로 **새** phase·프로젝트는 1-base(g1, g2 …).

---

## 사용자 결정사항 (2026-06-28)

| # | 결정 |
|---|------|
| 1 | FDR `KRX-DELISTING` · 2020~2026 · `SecuGroup=주권` · SPAC 제외 · **KONEX 64종 제외** → **190종** |
| 2 | 190종도 기존 3,945종과 **동일 sidecar**: OHLCV → merge → derived → 시총 → market |
| 3 | **순서**: g1 `listing_events` → g2 OHLCV → g3 enrich → g4 검증 |
| 4 | Step E 스킵 · known failure(381+980) 별도 — [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) |
| 5 | SPAC·채권·워런트·수익증권 수집 제외 |

---

## 유니버스 규모 (2026-06-28 실측)

### 상폐 추가 대상 (KONEX 제외)

| 구분 | 건수 |
|------|------|
| FDR 주권 2020~2026 − SPAC | 254 |
| **KONEX 제외** | **−64** |
| **Step G 추가 대상** | **190** |
| 기존 `merged/` 겹침 | 0 |

**190종 시장**: KOSDAQ 132 · KOSPI 58

**연도별 상폐 (190종, DelistingDate 기준)**

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|------|------|------|------|------|------|------|
| 25 | 28 | 31 | 21 | 29 | 34 | 22 |

### 통합 유니버스

| 레이어 | 종목 수 |
|--------|---------|
| Phase 1 (현재 상장) | 3,947 (`symbols_active`) / 3,945 (`merged`) |
| Step G 추가 (상폐 주권) | 190 |
| **g1 listing_events 합계** | **4,137** |

---

## g0 산출물 ✅

```
data/naver_daily_archive/
├── master/symbols_delisted_joo_2020_2026.json   # 190종
└── reports/delisting_joo_ex_spac_2020_2026_by_year.json
```

```powershell
python -m scripts.archive_listing_events --g0
```

---

## g1 산출물 ✅

```
data/naver_daily_archive/master/listing_events.json   # 4,137종
```

| 검증 | 결과 |
|------|------|
| symbol count | 4,137 (listed=3,947, delisted=190) |
| listing_date 보유 | 4,132 / 4,137 |
| delisted status | 190/190 |

```powershell
python -m scripts.archive_listing_events --g1
```

---

## g2 OHLCV ✅ (2026-06-28)

| 항목 | 값 |
|------|-----|
| tasks total | 1,330 |
| **done** | **749** |
| prune skipped | 574 (상장/폐지 연도) |
| **Naver 0건 skipped (final)** | **7** |
| pending / failed / running | 0 |

**Naver 0건 (pykrx/FDR fallback 후보)**

`036260:2021` · `050320:2022` · `053660:2022` · `054340:2020` · `065620:2021` · `065940:2020` · `141020:2024`

| chunk | done | prune skipped | naver 0건 |
|-------|------|---------------|-----------|
| 0 | 198 | 138 | 0 |
| 1 | 173 | 157 | 5 |
| 2 | 174 | 154 | 1 |
| 3 | 204 | 125 | 1 |

```
manifest/tasks_delisted.jsonl
config/chunks_delisted.json
```

```powershell
python -m scripts.archive_plan_delisted --years 2020 2021 2022 2023 2024 2025 2026

python -m scripts.archive_collect --worker pc --max-tasks 0 --chunk 1 ^
  --tasks-file manifest/tasks_delisted.jsonl --chunk-config config/chunks_delisted.json
```

---

## g3 sidecar enrich ✅ (2026-06-28)

```powershell
python -m scripts.archive_g3_delisted
```

| Step | 결과 |
|------|------|
| merge (A) | **190/190** merged |
| derived (B) | **190/190** enriched |
| market_cap (C) | task **755 done** / 1,330 (575 failed — 상장 전·폐지 후 연도 등) · method `pykrx_mcap` |
| market (F) | **190/190** enriched · unknown_rows **0** |

**리포트**: `reports/merge_report_g3_20260628.json` · `enrich_derived_g3_*` · `enrich_market_cap_g3_c0~c3_*` · `enrich_market_g3_*`

**g2 Naver 0건 7종** (`036260` 등): merged/features row 있으나 bars 적음 — 시총·OHLCV sparse 예상.

---

## g4 — 검증 ✅ (2026-06-28)

```powershell
python -m scripts.archive_g4_delisted
python -m scripts.report_step_g_status
python -m scripts.verify_post_delist_spot --all-delisted
```

| 항목 | 결과 |
|------|------|
| merge/derived panel (10종) | **10/10 PASS** |
| post-delist spot (190종) | **ok=190, anomaly=0** |
| sidecar merged/features | **190/190** |
| mcap taxonomy (reclassified) | done **755** · skipped_expected **574** · expected_blank **1** |
| legacy g3 failed→skipped_expected | **574** |
| symbol tradable mcap | complete **190** · partial **0** |

**`141020:2024`**: 재시도 → **`expected_blank`** (`no_ohlcv_for_year` — 2024 OHLCV 0건, 폐지 2024-01-03)

**리포트**: `reports/g4_delisted_20260628.json` · `step_g_status_snapshot.json` · `post_delist_spot_20260628.json`

---

## ⚠️ blank / fail 분류 ✅ (2026-06-28 완료)

### 문제 (해결됨)

g3 시총 **575 failed** 중 **574**는 상장 전·폐지 후 연도 → **`skipped_expected`** 재분류.  
**1**건만 tradable 구간 실패 (`141020:2024`).

### 구현 완료

| # | 작업 | 상태 |
|---|------|------|
| 1 | `core/listing_window.py` | ✅ |
| 2 | `build_mcap_tasks` + enrich | ✅ |
| 3 | `scripts/verify_post_delist_spot.py` | ✅ |
| 4 | g4 / `report_step_g_status` | ✅ |
| 5 | (선택) Phase 1 partial 980·none 381 | ✅ **relabel 집계** · retry S1·2 — [STEP_C_MCAP_RETRY_HANDOFF.md](./STEP_C_MCAP_RETRY_HANDOFF.md) |

### task status taxonomy (목표)

| status | 의미 |
|--------|------|
| `done` | 거래 가능 구간 · enrich 성공 |
| `skipped_expected` | 상장 전·폐지 후 연도 (조회 생략) |
| `partial` | 구간 내 일부만 blank |
| `failed` | 거래 가능 구간 · API/수집 실패 |
| `anomaly_post_delist` | 폐지 후 bars/mcap 잔존 |

### 작업량 추정

| 규모 | 내용 |
|------|------|
| **중** (~1세션) | 1~3 + g3 mcap 재분류·handoff |
| **중~대** (+1세션) | 4 g4 검증 + Phase 1 Step C taxonomy 연동(5) |

→ **새 채팅 1~2세션** 권장.

---

## 이번 세션 구현 요약 (2026-06-28)

### Step G + mcap taxonomy (git)

| 파일 | 역할 |
|------|------|
| `core/listing_window.py` | tradable window · skip reason |
| `core/mcap_taxonomy.py` | mcap relabel · Phase 1 + G 공통 |
| `core/post_delist_verify.py` | post-delist spot |
| `core/step_g_status.py` | Step G status |
| `core/enrich_market_cap.py` | prune · expected_blank · no_ohlcv_for_year |
| `scripts/report_step_c_status.py` | v2 legacy + relabeled |
| `scripts/report_step_g_status.py` | Step G snapshot |
| `scripts/verify_post_delist_spot.py` | post-delist CLI |
| `scripts/archive_g4_delisted.py` | g4 validation |
| `tests/test_listing_window.py` · `test_mcap_taxonomy.py` · `test_post_delist_verify.py` · `test_step_g_status.py` · `test_enrich_market_cap.py` | |

### Step G g0~g2 초기 (git)

| 파일 | 역할 |
|------|------|
| `core/delisted_universe.py` | FDR KRX-DELISTING 필터 |
| `core/listing_events.py` | pykrx + FDR → listing_events |
| `scripts/archive_listing_events.py` | g0/g1 CLI |
| `scripts/archive_plan_delisted.py` | g2 OHLCV plan (listing_window prune) |
| `scripts/archive_g3_delisted.py` | g3 merge·enrich |

### 변경 코드

| 파일 | 변경 |
|------|------|
| `core/archive_merge.py` | delisted master 이름 fallback |
| `core/manifest.py` | `merge_tasks()` 공통화 |
| `scripts/archive_collect.py` | `--tasks-file`, `--chunk-config` |
| `scripts/archive_plan.py` | `merge_tasks` import |
| `.cursorrules` | Step G g0~g4 · KONEX 제외 190종 |

### 로컬 데이터 (git **제외** · PC만)

```
data/naver_daily_archive/
├── master/listing_events.json
├── manifest/mcap_retry_8a_symbols.json          # Session 2 · 95종
├── reports/step_c_status_snapshot.json          # v2 relabel
├── reports/step_g_status_snapshot.json
├── reports/g4_delisted_20260628.json
├── reports/enrich_market_cap_c8_retry_8a_20260628.json
└── (Step G merged/features 190종)
```

---

## 새 채팅 시작 문장

**mcap retry 이어하기** (다음 작업):

```
docs/STEP_C_MCAP_RETRY_HANDOFF.md · docs/NEXT_STEPS.md · .cursorrules 읽고 이어하기.

【먼저】Session 3 전 필수 설명 — Session 1·2 failed 원인(etf외→pykrx_mcap)과 3-pre(etf_aum 분기) 설명해줘.
【완료】Step G g0~g4 ✅ · listing_window/mcap taxonomy ✅ · mcap retry Session 1·2 (복구 0)
【대기】Session 3-pre etf외→etf_aum 코드 수정 → 8-A 재실행
【로컬】manifest/mcap_retry_8a_symbols.json · failed 1449 (chunk8 1433)
```
