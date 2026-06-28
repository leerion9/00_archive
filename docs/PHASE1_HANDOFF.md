# Phase 1 수집·보강 — 완료 handoff (2020~2026)

> **AI/개발자**: **1차 수집 완료**. 새 채팅에서 **백테스트** 착수 시 이 파일 + [NEXT_STEPS.md](./NEXT_STEPS.md) + [COLLECTION_PLAN.md](./COLLECTION_PLAN.md) 를 먼저 읽을 것.

**마지막 갱신**: 2026-06-28 (mcap retry Session 1~5 ✅ · **Phase 1 종료**)

---

## 완료 범위 (사용자 확정)

| 구분 | 내용 |
|------|------|
| **기간** | **2020~2026** (Step E 2019→2000 ⏸️ 스킵) |
| **유니버스** | 현재상장 **3,945** merged + 상폐 **190** = **4,135** `merged/` · `features/` |
| **메타** | `listing_events.json` **4,137**종 (로컬) |
| **파이프라인** | OHLCV → A merge → B derived → C mcap → D 검증 → F market → G 상폐 |
| **시총 잔여** | **4종 23 task** — **무시·known edge** (사용자 2026-06-28 확정) |

---

## 로컬 데이터 경로 (git 제외)

```
data/naver_daily_archive/
├── raw/pc/{symbol}/{year}.json      # Phase 1 OHLCV 원본
├── merged/{symbol}.json             # 통합 bars (OHLCV)
├── features/{symbol}.parquet        # sidecar (B·C·F)
├── master/
│   ├── symbols_active.json          # git 추적 (3,947)
│   ├── listing_events.json          # 4,137종 상장·폐지·market
│   └── symbols_delisted_joo_2020_2026.json  # Step G 190종
├── manifest/                        # tasks, enrich_tasks, failures
└── reports/                         # step_c_status_snapshot.json 등
```

---

## Sidecar 스키마 (`features/*.parquet`)

| 컬럼 | Step | 설명 |
|------|------|------|
| `date` (index) | — | YYYYMMDD |
| *(merged)* open, high, low, close, volume | OHLCV | `merged/` bars |
| `trading_value` | B | close × volume |
| `value_ma5`, `close_ma5` | B | 5일 rolling (연초 4일 null 정상) |
| `market_cap`, `market_cap_method` | C | `pykrx_mcap` \| `etf_aum` · 단위 **원(₩)** |
| `shares_outstanding` | C | pykrx |
| `market` | F | `KOSPI` \| `KOSDAQ` \| `etf외` |

**종목명**: `master/symbols_active.json` · `listing_events` (row 아님)

---

## 연도별 커버리지 요약 (실측 2026-06-28)

### OHLCV task (현재상장 ~3,947종/연)

| 연도 | done | skip | failed |
|------|------|------|--------|
| 2026 | 3,945 | 2 | 0 |
| 2025 | 3,898 | 49 | 0 |
| 2024 | 3,726 | 221 | 0 |
| 2023 | 3,371 | 576 | 0 |
| 2022 | 3,084 | 863 | 0 |
| 2021 | 2,849 | 1,098 | 0 |
| 2020 | 2,619 | 1,328 | 0 |

skip = 상장 전·네이버 무자료 (`no bars fetched`) — **정상**

### 시총 task (relabeled · listing_window)

| 항목 | 건수 |
|------|------|
| done | **24,144** |
| skipped_expected | **4,769** (상장 전·폐지 후) |
| expected_blank | **9** (OHLCV 없음) |
| **failed** | **23** (4종 — **무시**) |

### tradable symbol (7yr relabel)

| complete | partial | none |
|----------|---------|------|
| **4,131** | **2** | **2** |

---

## 시총 known edge 4종 (무시 확정)

| 코드 | 종목 | failed | 비고 |
|------|------|--------|------|
| `301410` | PLUS 코스닥150 레버리지 | 7 | pykrx ISIN 미등록 |
| `422260` | VITA MZ소비재 | 5 | ISIN 미등록 (2020~21 blank 정상) |
| `461270` | ACE 회사채형 ETN | 4 | ISIN 미등록 (2020~22 blank 정상) |
| `550043` | N2 WTI ETN(H) | 7 | ISIN 미등록 |

백테스트: 시총 필터 사용 시 **제외 또는 null** 처리.

---

## mcap retry (Session 1~5) — 코드 요약

| 변경 | 파일 |
|------|------|
| `listing_events.market=etf외` → `etf_aum` | `core/enrich_market_cap.py`, `core/market_cap_fetch.py` |
| ETN API `MDCSTAT06601` | `fetch_pykrx_etn_aum_krx` |
| relabel taxonomy | `core/mcap_taxonomy.py`, `core/listing_window.py` |
| batch retry | `scripts/run_mcap_retry_batch.py`, `gen_mcap_retry_manifests.py` |

상세: [STEP_C_MCAP_RETRY_HANDOFF.md](./STEP_C_MCAP_RETRY_HANDOFF.md)

---

## Step G (상폐 190)

→ [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md) · tradable mcap **190/190**

---

## 상태 확인 CLI

```powershell
python -m scripts.report_step_c_status
python -m scripts.report_step_g_status
python -m scripts.archive_merge_validate_samples --all
python -m scripts.archive_enrich_validate_samples --all
```

---

## 백테스트 연동 (COLLECTION_PLAN)

| 백테스트 니즈 | 아카이브 필드 |
|---------------|---------------|
| 일별 시총 cross-section | `market_cap` + `date` |
| 거래대금·유동성 | `trading_value`, `value_ma5` |
| 5일선 | `close_ma5` |
| 시장 필터 | `market` (point-in-time) |
| OHLCV | `merged` bars |
| 상장·폐지 window | `listing_events.json` |

---

## 새 채팅 시작 문장 (백테스트)

```
docs/PHASE1_HANDOFF.md · docs/NEXT_STEPS.md · .cursorrules 읽고 백테스트 이어하기.

【완료】Phase 1 (2020~2026) OHLCV + A~G · 4,135종 · mcap 4종 known edge 무시
【로컬】data/naver_daily_archive/ merged + features + listing_events
【다음】백테스트 설계·실행
```
