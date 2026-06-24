# 향후 작업 · 리마인더

> **AI/개발자**: 이 파일의 ⏰ 항목은 Phase 2(상장폐지) 시작 시 **반드시 먼저 리마인드**할 것.

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

---

## ⏰ 상장폐지 종목 (Phase 2 / Step F) — 순서 엄수

**2차 필드 enrich·merge 완료 후** 착수. OHLCV 수집 전에:

1. **연도별 상장폐지 종목 리스트** — FDR `StockListing('KRX-DELISTING')` + 폐지일 기준 연도별 집계
2. **연도별 몇 종목인지** 규모 파악 → 사용자에게 보고
3. 사용자 확인 후 폐지 종목 **가격·메타** 수집 (FDR / pykrx / 네이버 fallback)

**상장·폐지일 소스**

| 소스 | 내용 |
|------|------|
| FDR `StockListing('KRX')` | 현재 상장, 상장일 |
| FDR `StockListing('KRX-DELISTING')` | 폐지 종목, 폐지일·사유 |
| pykrx | 보조·교차검증 |
| KRX 정보데이터시스템 | 공식 (FDR 실패 시) |

→ `master/listing_events.json` (`archive_listing_events`, 구현 예정)

---

## Phase 1 OHLCV — **2020~2026 완료** (2026-06-23)

| 연도 | done | skipped | 상태 |
|------|------|---------|------|
| 2026 | 3,945 | 2 | ✅ |
| 2025 | 3,898 | 49 | ✅ |
| 2024 | 3,726 | 221 | ✅ |
| 2023 | 3,371 | 576 | ✅ |
| 2022 | 3,084 | 863 | ✅ |
| 2021 | 2,849 | 1,098 | ✅ |
| 2020 | 2,619 | 1,328 | ✅ |

---

## 다음 우선: **Step A — merge** (2020~2026)

→ 상세: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

| Step | 내용 | 상태 |
|------|------|------|
| A | `archive_merge` | ❌ |
| B | `archive_enrich_derived` (거래대금·MA5) | ❌ |
| C | `archive_enrich_market_cap` (pykrx 일별) | ❌ |
| D | 검증·status | ❌ |
| E | 2019→2000 OHLCV (역순) | ❌ |
| F | 상장폐지 ⏰ | 보류 |

---

## 종목 chunk 분할 (4등분, 코드순)

| chunk | 코드 범위 | 종목 수 |
|-------|-----------|---------|
| 0 | 000020 ~ 051500 | 1,000 |
| 1 | 051600 ~ 214330 | 1,000 |
| 2 | 214370 ~ 433500 | 1,000 |
| 3 | 433880 ~ 950250 | 947 |

---

## fail / retry 정책 (OHLCV)

| 단계 | 명령 | 실패 시 상태 |
|------|------|-------------|
| **1회차** | `archive_collect --chunk N` | `failed` |
| **2회차** | `archive_collect --chunk N --retry-failed` | **`skipped` (최종)** |

> `--retry-failed`는 **`--chunk`와 함께** 사용.

---

## Git

- 원격: [leerion9/00_archive](https://github.com/leerion9/00_archive)
- 브랜치: `master`
- 수집 데이터는 `.gitignore` — **PC 로컬 유지**
