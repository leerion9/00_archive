# Step C — mcap retry handoff (Phase 1 known failure)

> **AI/개발자**: mcap retry **Session 1~5 ✅ 완료** (2026-06-28). 잔여 failed **23 task** = known edge case 4종.

**마지막 갱신**: 2026-06-28 (Session 3-pre~5 ✅ · failed **1,449 → 23**)

**선행**: Step G g0~g4 ✅ · `listing_window` / mcap taxonomy ✅ — [STEP_G_HANDOFF.md](./STEP_G_HANDOFF.md)

**관련**: [STEP_D_HANDOFF.md](./STEP_D_HANDOFF.md) · [STEP_C_HANDOFF.md](./STEP_C_HANDOFF.md)

---

## Session 3-pre — 코드 수정 ✅

| 변경 | 내용 |
|------|------|
| `listing_events.market=etf외` | `enrich_market_cap` → `fetch_market_cap_for_year(listing_market=…)` → **`etf_aum` 강제** |
| ETN API | pykrx `개별종목시세_ETF`는 **ETN empty** → **`MDCSTAT06601`** (`fetch_pykrx_etn_aum_krx`) 추가 |
| 라우팅 | `fetch_pykrx_etx_aum_krx` — EtxTicker `종류`로 ETF/ETN 분기 |
| 테스트 | `tests/test_market_cap_fetch.py` · `tests/test_enrich_market_cap.py` — **13 passed** |

---

## relabel 집계 (2026-06-28 · retry 후)

| 구분 | retry 전 | **retry 후** |
|------|----------|--------------|
| tradable complete | 3,754 | **4,131** (+377) |
| partial | 2 | **2** |
| none | 379 | **2** |
| **task failed** | 1,449 | **23** |

- `skipped_expected`: **4,769** (변화 없음)
- `expected_blank`: **9** (변화 없음)
- universe tasks: done **24,144** · failed **23**

```powershell
python -m scripts.report_step_c_status
# → reports/step_c_status_snapshot.json (schema v2)
```

---

## mcap retry Session 로그

### Session 1 — Pilot ✅ (2026-06-28 · 1차)

| 종목 | done | failed | 비고 |
|------|------|--------|------|
| `301410` | 0 | 7 | 3-pre **전** — pykrx_mcap 경로 |
| `422260` | 0 | 5 | 동일 |
| `461270` | 0 | 4 | 동일 |

### Session 2 — chunk 8-A ✅ (2026-06-28 · 1차)

- **95종** · done **0** / failed **410** (3-pre 전)
- **리포트**: `reports/enrich_market_cap_c8_retry_8a_20260628.json`

### Session 3 — 3-pre + 8-A 재실행 ✅ (2026-06-28)

- **3-pre** 코드 적용
- **8-A 95종** · done **410** / failed **0** · methods **`etf_aum` 410** · ~13분
- **리포트**: `reports/enrich_market_cap_c8_20260628.json` (8-A 구간)

### Session 4 — chunk 8-B ✅ (2026-06-28)

- **95종** · done **385** / failed **7** (`550043` 7yr)
- methods **`etf_aum` 385**

### Session 5 — chunk 8-C + 8-D + status ✅ (2026-06-28)

| Batch | 종목 | done | failed |
|-------|------|------|--------|
| **8-C** | 95 | **341** | 0 |
| **8-D** | 93 | **290** | 0 |

- Pilot 재시도(3-pre 후): `301410`/`422260`/`461270` — **여전히 failed** (아래 known edge)
- `report_step_c_status` 최종 스냅샷 반영

---

## chunk별 retry 후 상태

| chunk | relabeled failed | none | 비고 |
|-------|------------------|------|------|
| 0~4 | **0** | 0 | |
| 5 | **7** | 1 | `301410` |
| 6 | **5** | 0 | `422260` partial |
| 7 | **4** | 0 | `461270` partial |
| **8** | **7** | 1 | `550043` · **377종 복구** |

---

## 잔여 failed 23 task (known edge · 4종) — **무시 확정**

| 종목 | failed | 원인 |
|------|--------|------|
| `301410` | 7 | ETF이나 `listing_events.market` 없음 · EtxTicker/pykrx ISIN 미등록 |
| `422260` | 5 | VITA 힌트로 etf_aum 시도 · **get_etx_isin 실패** |
| `461270` | 4 | 회사채형 ETN · 이름에 ETN 없음 · ISIN 미등록 |
| `550043` | 7 | ETN(H) · ISIN 미등록 · `listing_events.market` 없음 |

→ Phase 1 본체(chunk 8 etf외 377종) **복구 완료**.  
→ **2026-06-28 사용자 확정**: 위 4종 **retry·조사 없이 무시** — 백테스트 시 시총 필터 제외. [PHASE1_HANDOFF.md](./PHASE1_HANDOFF.md)

---

## manifest (로컬)

```
data/naver_daily_archive/manifest/
├── mcap_retry_8a_symbols.json   # 95종
├── mcap_retry_8b_symbols.json   # 95종
├── mcap_retry_8c_symbols.json   # 95종
└── mcap_retry_8d_symbols.json   # 93종
```

```powershell
python -m scripts.run_mcap_retry_batch 8-A   # manifest 기반 실행
python -m scripts.gen_mcap_retry_manifests   # 8-B~D 재생성 (snapshot 기준)
python -m scripts.report_step_c_status
```

---

## 이번 기간 구현 코드 (git)

| 파일 | 역할 |
|------|------|
| `core/market_cap_fetch.py` | `should_use_etf_aum` · `fetch_pykrx_etn_aum_krx` · `fetch_pykrx_etx_aum_krx` |
| `core/enrich_market_cap.py` | `listing_market` → fetch 전달 |
| `core/listing_window.py` | `listing_market()` |
| `scripts/gen_mcap_retry_manifests.py` | 8-B~D manifest 생성 |
| `scripts/run_mcap_retry_batch.py` | manifest batch 실행 |
| `core/mcap_taxonomy.py` | mcap task/symbol taxonomy · relabel |
| `scripts/report_step_c_status.py` | v2 legacy + relabeled |

---

## 금지·운영

- `archive_enrich_market_cap --chunk N` — **완료분 skip 없음**
- **chunk 1~8 일괄 for-loop 금지** — batch(8-A/B/C/D) 또는 `--symbols`만
- KRX 세션 **~1시간** — batch당 ~10~15분 (etf_aum 성공 시)
- `data/` git 제외 · 코드만 commit (사용자 요청 시)
