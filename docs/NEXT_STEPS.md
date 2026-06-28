# 향후 작업 · 리마인더

> **AI/개발자**: **Phase 1 (2020~2026) 수집·보강 완료** — 다음은 **백테스트**.  
> handoff: [PHASE1_HANDOFF.md](./PHASE1_HANDOFF.md) · [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**전체 수집·보강 로드맵**: [COLLECTION_PLAN.md](./COLLECTION_PLAN.md)

**마지막 handoff**: 2026-06-28 (**Phase 1 ✅** · mcap 4종 known edge **무시 확정**)

**필독 문서**: [PHASE1_HANDOFF.md](./PHASE1_HANDOFF.md) · [STEP_C_MCAP_RETRY_HANDOFF.md](./STEP_C_MCAP_RETRY_HANDOFF.md) · [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md)

---

## ⏭️ 다음 작업 — 백테스트

| 항목 | 내용 |
|------|------|
| 데이터 | `merged/` + `features/` · **4,135종** · **2020~2026** |
| 메타 | `master/listing_events.json` (로컬 4,137) |
| 시총 gap | 4종 (`301410` 등) — **필터 제외·null 처리** |
| Step E | 2019→2000 ⏸️ 스킵 (필요 시 별도 착수) |

```powershell
python -m scripts.report_step_c_status
python -m scripts.report_step_g_status
```

---

## Phase 1 완료 요약 ✅

| Step | 내용 | 상태 |
|------|------|------|
| OHLCV | 2020~2026 Naver 일봉 | ✅ failed **0** |
| **A** | merge 3,945 + 상폐 190 | ✅ **4,135** |
| **B** | derived sidecar | ✅ |
| **C** | market_cap (+ retry S1~5, ETN API) | ✅ failed **23** (4종 무시) |
| **D** | merge·derived QA | ✅ 3945/3945 |
| **E** | 2019→2000 | ⏸️ 스킵 |
| **F** | 일별 시장구분 | ✅ |
| **G** | listing_events + 상폐 enrich | ✅ g0~g4 |

**relabeled mcap**: complete **4,131** / partial **2** / none **2** · skipped_expected **4,769**

상세 연도·필드 표: [PHASE1_HANDOFF.md](./PHASE1_HANDOFF.md)

---

## Git

원격: [leerion9/00_archive](https://github.com/leerion9/00_archive), branch `master`

`data/` 대용량·수집본 — **git 제외** (PC 로컬). `symbols_active.json`·`config/chunks*.json` 만 추적.

---

## 새 채팅 시작 문장 (백테스트)

```
docs/PHASE1_HANDOFF.md · docs/NEXT_STEPS.md · .cursorrules 읽고 백테스트 이어하기.

【완료】Phase 1 (2020~2026) · 4,135종 · mcap 4종 known edge 무시
【로컬】data/naver_daily_archive/ merged + features + listing_events
【다음】백테스트 설계·실행
```
