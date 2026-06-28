# 향후 작업 · 리마인더

> **AI/개발자**: ⏰ **Step G(상장폐지)** 시작 시 **반드시 먼저 리마인드**할 것.  
> **known failure(381+980)**: Step G 착수 시 [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) 와 **함께** 정책 확정 (2026-06-27 보류).

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-28 (Step G **결정·프로세스 확정** — **실행 대기**)

**필독 문서**: [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md) · [STEP_F_HANDOFF.md](./STEP_F_HANDOFF.md) · [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md)

---

## ⏰ Step G — 상장/폐지 메타 + 상폐 주권 보강 (실행 대기)

**2026-06-28 사용자 결정** — 상세: [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md)

| 항목 | 내용 |
|------|------|
| 추가 유니버스 | FDR 상폐 **주권 389 − SPAC 133 = 254종** (2020~2026) |
| 통합 목표 | **4,199종** (3,945 + 254) · 2020~2026 |
| **순서** | **①** `listing_events.json` (전 종목 상장일·폐지일) → **②** 254종 OHLCV·merge·derived·시총·market |
| 제외 | SPAC · 채권·워런트·수익증권 |

known failure(381+980)는 3,945 기존 분 — [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md)

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
| **C** | `archive_enrich_market_cap` | ✅ chunk 0~8 |
| **D** | 검증·status | ✅ **B+C 완료** — [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) |
| **E** | 2019→2000 OHLCV | ⏸️ **스킵** (2026-06-27) |
| **F** | 일별 시장구분 (`KOSPI`/`KOSDAQ`/`etf외`) | ✅ **3,945종** — [STEP_F_HANDOFF.md](./STEP_F_HANDOFF.md) |
| **G** | listing_events + 상폐 주권 254 enrich | ❌ **다음 (프로세스 확정)** — [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md) |

---

## Step D 요약 (2026-06-27)

- **옵션 B**: 10종 PASS + parquet 집계 (~30초)
- **옵션 C**: merge **3945/3945**, derived **3945/3945** (~6.5분)
- **known failure**: partial **980** + none **381** = 1,361종 (시총 7yr 미완) → Step G와 함께 검토
- **조사 보류**: **301410** ETF AUM API 실패

```powershell
python -m scripts.archive_merge_validate_samples --all
python -m scripts.archive_enrich_validate_samples --all
python -m scripts.report_step_c_status
```

상세: [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md)

---

## Step C — chunk 요약 (완료)

| chunk | 7yr | partial | none | 상태 |
|-------|-----|---------|------|------|
| 0~5 | 재적재 | known failure | 1 (301410) | ✅ |
| 6 | 189/487 | 297 | 1 | ✅ |
| 7 | 0/487 | 486 | 1 | ✅ |
| 8 | 18/485 | 89 | 378 | ✅ |

**합계**: 2,584 / 3,945 · partial 980 · none 381

상세: [STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md)

---

## Step F — 시장구분 ✅ (2026-06-27)

- **3,945종** chunk 0~3 적재 + ETF/ETN **1,247종** → `market=etf외`
- `market` 값: `KOSPI` / `KOSDAQ` / `etf외` · row null **0.48%**
- 캐시: `master/market_daily/` 1,591일

상세: [STEP_F_HANDOFF.md](./STEP_F_HANDOFF.md)

---

## Step G — 실행 대기 (2026-06-28)

→ [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md) (Phase G0~G4 · 새 채팅 시작 문장)

---

## Git

원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`  
`data/` — git 제외 (로컬)

---

## 새 채팅 시작 문장 (Step G)

> `docs/STEP_G_HANDOFF.md` · `docs/NEXT_STEPS.md` · `.cursorrules` 읽고 Step G 착수. **G1 listing_events(4,199종) → G2~G3 254종 OHLCV·enrich 전체**. SPAC 제외 · Step E 스kip. handoff 하단 「새 채팅 작업 요청」 참고.
