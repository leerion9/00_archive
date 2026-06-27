# 향후 작업 · 리마인더

> **AI/개발자**: ⏰ **Step G(상장폐지)** 시작 시 **반드시 먼저 리마인드**할 것.  
> **known failure(381+980)**: Step G 착수 시 [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) 와 **함께** 정책 확정 (2026-06-27 보류).

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-27 (Step D **B+C 검증 완료** — **다음: Step F 시장구분**)

**필독 문서**: [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) · [STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md) · [STEP_C_RUN_LOG.md](./STEP_C_RUN_LOG.md)

---

## ⏰ 상장폐지 종목 (Step G) — Step F **후**

**Step F(시장구분) 완료 후** 착수. **known failure(381+980)** 와 **함께** 유니버스·백테스트 정책 논의 (2026-06-27).

1. FDR `StockListing('KRX-DELISTING')` → 연도별 폐지 종목·건수 **보고**
2. 사용자 확인
3. 폐지 종목 OHLCV·메타 수집 → `master/listing_events.json`

→ [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) known failure 절 참고

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
| **F** | 일별 시장구분 KOSPI/KOSDAQ | ❌ **다음 작업** |
| **G** | 상장폐지 ⏰ + known failure 정책 | 보류 (F 후) |

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

## Step F — 시장구분 (다음)

- pykrx `get_market_ticker_list(date, market=KOSPI/KOSDAQ)` → sidecar `market`
- **선행**: Step D ✅ (2020~26)
- 구현: `scripts/archive_enrich_market` (예정)

---

## Git

원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`  
`data/` — git 제외 (로컬)

---

## 새 채팅 시작 문장 (Step F)

> `docs/NEXT_STEPS.md` · `docs/STEP_D_HANDOFF.md` 읽고 Step **F**(일별 KOSPI/KOSDAQ `market` sidecar enrich) 착수해줘. Step E 스킵. known failure 381+980·상장폐지(Step G)는 F 완료 후 함께 논의.
