# Step G — 상장/폐지 메타 + 상폐 주권 보강 handoff

> **AI/개발자**: Step G **실행 전 이 파일 전체** + [NEXT_STEPS.md](./NEXT_STEPS.md) 를 읽을 것.  
> **실제 수집·적재는 새 채팅에서** 사용자 지정 chunk/단계만 터미널 실행 (일괄 for-loop 금지).

**마지막 갱신**: 2026-06-28 (사용자 결정사항 반영 · 실행 **대기**)

**선행 완료**: Step A~D ✅ · Step F ✅ · Step E ⏸️ 스킵

---

## 사용자 결정사항 (2026-06-28)

| # | 결정 |
|---|------|
| 1 | FDR `KRX-DELISTING` 중 **2020~2026 상폐** · `SecuGroup=주권` **389건**에서 **SPAC 제외** → **254종**만 추가 유니버스 |
| 2 | 추가 254종도 기존 3,945종과 **동일 sidecar 수준**: OHLCV → merge → derived(거래대금·MA5) → 시총 → 시장구분 |
| 3 | **순서**: (A) 전 종목 **상장일·폐지일** 수집·저장 → (B) 254종 **OHLCV~enrich** 수집 |
| 4 | Step E(2019→2000) **스킵** 유지 · 2020~2026 구간 완성이 목표 |
| 5 | SPAC·채권·워런트·수익증권(1,014−389) **수집 제외** |

---

## 유니버스 규모 (FDR 실측 2026-06-28)

### 상폐 후보 (2020~2026, `DelistingDate`)

| 구분 | 건수 |
|------|------|
| 전체 상폐 (FDR) | 1,014 |
| `SecuGroup=주권` | 389 |
| 그중 SPAC (종목명) | 133 |
| **Step G 추가 대상 (주권 − SPAC, 6자리)** | **254** |
| 기존 `merged/` 와 겹침 | **0** (유일 겹침 `464440` 스팩 → 제외) |

**254종 시장**: KOSDAQ 132 · KOSPI 58 · KONEX 64

**연도별 상폐 (254종, DelistingDate 기준)**

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|------|------|------|------|------|------|------|
| 36 | 37 | 39 | 31 | 39 | 41 | 31 |

### 통합 유니버스 (Step G 완료 후 목표)

| 레이어 | 종목 수 | 비고 |
|--------|---------|------|
| Phase 1 (현재 상장 스냅샷) | 3,945 | `merged/` · `features/` |
| Step G 추가 (상폐 주권) | 254 | OHLCV·enrich **신규** |
| **합계** | **4,199** | 2020~2026 “주권” 백테스트 유니버스 |

---

## Step G 목표 (백테스트)

- **상장 전·상폐 후** blank를 `listing_date` / `delisting_date`로 **설명 가능**하게
- 2020~2026 동안 **거래 가능했던 주권(스팩 제외)** 에 대해 Phase 1과 **동일 필드** 보유
- `archive_event_check` (설계) 로 백테스트 구간 경고

---

## 실행 프로세스 (순서 엄수)

### Phase G0 — 준비 · 마스터 추출 (코드·리스트)

1. FDR `StockListing('KRX-DELISTING')` 재조회
2. 필터: `DelistingDate` ∈ 2020-01-01 ~ 2026-12-31 · `SecuGroup=주권` · 종목명 **SPAC/스팩 제외** · `Symbol` **6자리**
3. 저장 (git **코드만**; 데이터는 `data/` 로컬):
   - `master/symbols_delisted_joo_2020_2026.json` — 254종 `{symbol, name, market, listing_date, delisting_date, reason, ...}`
   - `reports/delisting_joo_ex_spac_2020_2026_by_year.json` — 연도별 리스트·건수·사유
4. (선택) `scripts/` 에 추출 CLI — `archive_listing_events` 또는 `export_delisted_universe`

### Phase G1 — **전 종목** 상장일·폐지일 (`listing_events.json`)

**대상**: 기존 **3,945** + 추가 **254** = **4,199종**

| 소스 | 필드 | 대상 |
|------|------|------|
| pykrx `get_market_ohlcv_by_market(market='ALL')` | `listing_date` | 현재 상장 3,945 (KRX 로그인 `.env`) |
| FDR `KRX-DELISTING` | `listing_date`, `delisting_date`, `reason` | 254종 (+ 3,945 중 상폐 이력 있는 경우 보강) |

**저장**: `master/listing_events.json` ([DESIGN.md](./DESIGN.md) §5.3 스키마)

```json
{
  "schema_version": 1,
  "updated_at_iso": "...",
  "source": "pykrx_listing+fdr_delisting",
  "symbols": {
    "005930": {
      "name": "삼성전자",
      "market": "KOSPI",
      "listing_date": "19750611",
      "delisting_date": null,
      "status": "listed",
      "events": []
    },
    "036490": {
      "listing_date": "...",
      "delisting_date": "20211227",
      "status": "delisted",
      "events": [{"type": "delisted", "date": "20211227", "reason": "...", "note": ""}]
    }
  }
}
```

**검증**: 4,199 키 존재 · 날짜 YYYYMMDD · 254종 `status=delisted` · pykrx/FDR 샘플 spot-check

**Phase G1 완료 전 OHLCV 대량 수집 착수 금지** (사용자 합의 순서).

### Phase G2 — 254종 OHLCV (2020~2026)

- **1차**: 네이버 `sise_day` (`archive_collect`) — 기존 Phase 1과 동일
- **fallback**: pykrx / FDR `DataReader` (네이버 0건·상폐 종목)
- **task**: `(symbol, year)` 2020~2026 · `archive_plan` 또는 delisted 전용 task manifest
- **저장**: `raw/{worker}/{symbol}/{year}.json` → `archive_merge` → `merged/{symbol}.json`
- **상장일 prune** (설계): `listing_date > {year}1231` → skip · `delisting_date < {year}0101` → skip

### Phase G3 — 254종 sidecar enrich (기존 Step A~F 동일)

| Step | 스크립트 | 산출 |
|------|----------|------|
| A | `archive_merge` | `merged/` |
| B | `archive_enrich_derived` | `trading_value`, `value_ma5`, `close_ma5` |
| C | `archive_enrich_market_cap` | `market_cap` (`pykrx_mcap` / `etf_aum` — 주권 위주) |
| F | `archive_enrich_market` | `market` (`KOSPI`/`KOSDAQ`/`etf외`) |

- chunk 분할: 254종 — **chunk 설계 후 1~3 chunk/세션** (기존 enrich chunk 정책 준수)
- KRX 세션 **~1시간** · Step C 장시간 주의 ([STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md))

### Phase G4 — 검증

```powershell
python -m scripts.archive_merge_validate_samples --symbols <delisted_sample>
python -m scripts.archive_enrich_validate_samples --symbols <delisted_sample>
python -m scripts.report_step_c_status   # 254종 반영 시 manifest 확장 후
```

- `listing_events` vs OHLCV `date_range` 교차 (상장 전·폐지 후 bars 없음 = 정상)
- 254종 features parquet 필수 컬럼 존재

---

## 기존 3,945종 known failure (별도 · Step G와 동시 정책)

Step C **partial 980 + none 381** — Step G **254 신규**와 **별개**.

| 구분 | 종목 | Step G 후 권장 |
|------|------|----------------|
| partial 980 | 일부 연도 `empty` (신규상장) | `listing_date`로 **정상 blank** 분류 |
| none 381 | ETF/ETN 시총 API failed 多 | 재시도 **선택** · 백테스트 exclude/null 정책 |
| Step F null 0.48% | 상장 전 `market` | `listing_date`로 설명 |

→ [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) known failure 절

---

## 데이터 경로 (Step G 추가)

```
data/naver_daily_archive/
├── master/
│   ├── symbols_active.json              # 기존 3,947 스냅샷
│   ├── symbols_delisted_joo_2020_2026.json   # G0 · 254종
│   └── listing_events.json              # G1 · 4,199종
├── reports/
│   └── delisting_joo_ex_spac_2020_2026_by_year.json
├── merged/{symbol}.json                 # +254
└── features/{symbol}.parquet            # +254 (B+C+F sidecar)
```

---

## 구현 메모 (새 채팅)

- `archive_listing_events` CLI **미구현** → G0/G1에서 `scripts/` 추가 예정
- `archive_collect` / `archive_plan` 은 **symbols_active** 기준 → 254종용 manifest 또는 `--symbols-file` 확장 검토
- delisted OHLCV: 네이버 실패 시 **pykrx·FDR fallback** ([DESIGN.md](./DESIGN.md) §3.2)
- `.env`: `KRX_ID`, `KRX_PW` 필수 (pykrx 상장일·시총)

---

## 새 채팅 시작 문장

아래 **「새 채팅 작업 요청」** 블록을 복사해 사용.

---

### 새 채팅 작업 요청 (복사용)

```
docs/STEP_G_HANDOFF.md · docs/NEXT_STEPS.md · .cursorrules 읽고 Step G 착수.

【결정사항】
- 상폐 추가: FDR KRX-DELISTING · 2020~2026 · SecuGroup=주권 · SPAC 제외 → 254종
- 순서: G1 listing_events(4,199종 상장일·폐지일) → G2~G3 254종 OHLCV·merge·derived·시총·market
- 254종도 3,945와 동일 sidecar 전부
- Step E 스킵 · known failure(381+980)는 별도 정책(문서만 참고)

【1세션】
1. Phase G0: 254종 마스터 + 연도별 상폐 리포트 JSON 생성
2. Phase G1: listing_events.json (pykrx 상장일 + FDR 폐지일) — 완료 후 handoff 갱신
3. G2 OHLCV는 G1 검증 후 사용자 확인 뒤 chunk 지정 실행

chunk 일괄 for-loop 금지 · 한 세션 1~3 chunk.
```

---

## 상태

| Phase | 내용 | 상태 |
|-------|------|------|
| G0 | 254종 마스터·연도별 리포트 | ❌ 대기 |
| G1 | `listing_events.json` (4,199) | ❌ 대기 |
| G2 | 254종 OHLCV | ❌ 대기 |
| G3 | 254종 merge·B·C·F | ❌ 대기 |
| G4 | 검증 | ❌ 대기 |
