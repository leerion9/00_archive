# Step G — 상장/폐지 메타 + 상폐 주권 보강 handoff

> **AI/개발자**: Step G **실행 전 이 파일 전체** + [NEXT_STEPS.md](./NEXT_STEPS.md) 를 읽을 것.  
> **실제 수집·적재는 새 채팅에서** 사용자 지정 chunk/단계만 터미널 실행 (일괄 for-loop 금지).

**마지막 갱신**: 2026-06-28 (g0~g3 ✅ · g4 검증 대기)

**선행 완료**: Step A~D ✅ · Step F ✅ · Step E ⏸️ 스킵

---

## Step G phase (g0~g4 · 5단계)

| Phase | 내용 | 상태 |
|-------|------|------|
| **g0** | 190종 마스터 + 연도별 상폐 리포트 JSON | ✅ 2026-06-28 |
| **g1** | `listing_events.json` (4,137종) | ✅ 2026-06-28 |
| **g2** | 190종 OHLCV (2020~2026) | ✅ 2026-06-28 |
| **g3** | 190종 merge·B·C·F | ✅ 2026-06-28 |
| **g4** | 검증 | ❌ 대기 |

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

## g4 — 검증 (대기)

```powershell
python -m scripts.archive_merge_validate_samples --symbols <delisted_sample>
python -m scripts.archive_enrich_validate_samples --symbols <delisted_sample>
```

---

## ⚠️ 알려진 설계 갭 — blank / fail 분류 (2026-06-28 합의 · **다음 채팅 우선**)

### 문제

g3 시총 **575 failed** = (종목, **연도**) task 실패 건수 (일별·종목 수 아님).  
현재 `build_mcap_tasks` / `enrich_market_cap`은 **`listing_events.json` 미참조** → 폐지 후·상장 전 연도도 task 생성 후 `empty` → **failed**로 집계.

**사용자 합의**: 폐지일 **이후** 데이터 없음 = **정상(`expected_blank`)**.  
폐지 후 **데이터 있음** = **anomaly** → 사용자 보고·원인 조사.  
거래 가능 구간 내 API 실패만 **failed**.

### 수정 방향 (구현 전 · [DESIGN.md](./DESIGN.md) §9 보완 예정)

| # | 작업 | 산출 |
|---|------|------|
| 1 | `core/listing_window.py` | `is_tradable(symbol, date\|year)` · skip reason enum |
| 2 | `build_mcap_tasks` + g3/Step C | task prune · empty 시 `expected_blank` vs `failed` |
| 3 | `scripts/verify_post_delist_spot.py` | 폐지 후 **소수 샘플**만 조회 · empty=ok · data=anomaly 리포트 |
| 4 | g4 status / `report_step_g_status` | done / expected_blank / partial / failed / anomaly 분리 |
| 5 | (선택) Phase 1 partial 980·none 381 | listing 기준 재라벨 |

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

### 신규 코드 (git)

| 파일 | 역할 |
|------|------|
| `core/delisted_universe.py` | FDR KRX-DELISTING 필터 (주권·SPAC·KONEX) |
| `core/listing_events.py` | pykrx listing + FDR delisting → JSON |
| `scripts/archive_listing_events.py` | g0/g1 CLI (`--g0` `--g1`; legacy `--g2`→g1) |
| `scripts/archive_plan_delisted.py` | g2 OHLCV task manifest (연도 prune) |
| `scripts/archive_g3_delisted.py` | g3 merge·derived·mcap·market 일괄 |
| `tests/test_delisted_universe.py` | 필터 unit test |
| `tests/test_listing_events.py` | payload builder test |

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
├── master/symbols_delisted_joo_2020_2026.json   # g0 · 190
├── master/listing_events.json                   # g1 · 4,137
├── config/chunks_delisted.json
├── manifest/tasks_delisted.jsonl
├── merged/{190 symbols}.json                    # g3
├── features/{190 symbols}.parquet               # g3
└── reports/merge_report_g3_* · enrich_*_g3_*
```

### 시총 소스 (g3)

- **pykrx** `get_market_cap_by_date` · method `pykrx_mcap` · `.env` KRX_ID/PW
- **Naver 시총 fallback 없음** (Step C 정책 동일)

---

## 구현 (코드)

| 모듈 | 역할 |
|------|------|
| `core/delisted_universe.py` | FDR 필터 (주권·SPAC·KONEX) |
| `core/listing_events.py` | pykrx listing + FDR delisting → JSON |
| `scripts/archive_listing_events.py` | g0/g1 CLI |
| `scripts/archive_plan_delisted.py` | g2 task manifest |
| `scripts/archive_g3_delisted.py` | g3 merge·enrich 일괄 |
| `scripts/archive_collect.py` | `--tasks-file`, `--chunk-config` 확장 |

`.env`: `KRX_ID`, `KRX_PW` (pykrx 상장일)

---

## 새 채팅 시작 문장

```
docs/STEP_G_HANDOFF.md · docs/NEXT_STEPS.md · .cursorrules 읽고 Step G 이어하기.

【완료】g0~g3 ✅ (190종 · KONEX 제외 · listing_events 4,137)
【다음 우선】listing_window + expected_blank vs failed (g3 mcap 575 재분류) → verify_post_delist_spot → g4 검증
【로컬】data/naver_daily_archive merged+features 190종 (git 제외)

chunk 일괄 for-loop 금지 · phase g0~g4.
```
