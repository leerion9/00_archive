# Step C — 시총 enrich handoff (chunk별 상세)

> **AI/개발자**: Step C 작업 시 **이 파일을 chunk 번호별로** 읽을 것. chunk 1~5를 「재적재 잔여」로 **묶어서 요약하지 말 것**. 실측 갱신: `python -m scripts.report_step_c_status` 후 `python -m scripts.update_step_c_handoff`.

**마지막 실측**: 2026-06-27 03:05 UTC (manifest `enrich_tasks.jsonl` 최신 줄 기준)

**완료 기준**: 종목당 2020~2026 **7연도** 모두 `status=done` + `method` ∈ {`pykrx_mcap`, `etf_aum`}.

**전체 합계**: 2584 / 3,945종 7연도 완료 · partial 980 · none 381

머신 리더블 스냅샷: `data/naver_daily_archive/reports/step_c_status_snapshot.json`

**실행·partial retry 상세 로그**: [STEP_C_RUN_LOG.md](./STEP_C_RUN_LOG.md)

---

## 작업 경과 타임라인

| 일자 | chunk | 내용 |
|------|-------|------|
| **6/24** | 0~5 | 1차 실행 — 구방식 (`shares_x_close`/`etf_nav` 등) → **재적재 대상** |
| **6/25 14:41** | 0 | 수정 코드(`etf_aum`/`pykrx_mcap`) **재적재 완료** ✅ |
| **6/25 11:09~** | 1 | 재적재 시작 → **중단** (~1050/3416 task) |
| **6/25** | 1~5 | chunk별 2차 실행 — chunk 4·5 KRX 세션 만료 failed 多 |
| **6/26 11:28~18:47** | 1~8 | ⚠️ AI **일괄 실행** (의도: chunk 1만) |
| **6/26 18:49~22:45** | 4~8 | ⚠️ AI **재일괄** → chunk 8 **사용자 중단** |
| **6/27** | 1~2 | **partial retry** (`--symbols`) — known failure, 변화 없음 |
| **6/27** | 3~5 | **partial+none retry** — chunk 4 **117690** ETF `etf_aum` 완료 (+1) |
| **6/27** | 6 | **최초 적재 전체** (~50분) — 7yr **189/487**, failed 599 |
| **6/27** | — | **chunk 0~6 handoff·RUN_LOG 저장**, **chunk 7~8 → 새 채팅** |
| **6/27** | 7 | **최초 적재 전체** (~42분) — 7yr **0/487**, partial 486 (신규상장·ETF) |
| **6/27** | 8 | **최초 적재 전체** (~19분) — 7yr **18/485**, partial 89, none 378 |
| **6/27** | — | **Step C chunk 0~8 실행 완료** → Step D |

---

## chunk 요약표 (한눈에)

| chunk | 코드 범위 | 성격 | 7yr 완료 | partial | none | fail_log | 다음 액션 |
|-------|-----------|------|----------|---------|------|----------|-----------|
| **0** | 000020~000815 | 재적재 (test) | **50/50** | 0 | 0 | 0 | **완료 — 스킵** |
| **1** | 000850~014950 | 재적재 | **486/488** | 2 | 0 | 8 | **partial retry 완료(6/27)** — partial 2 known failure → STEP_C_RUN_LOG.md |
| **2** | 014970~053050 | 재적재 | **484/487** | 3 | 0 | 12 | **partial retry 완료(6/27)** — partial 3 known failure → STEP_C_RUN_LOG.md |
| **3** | 053060~101670 | 재적재 | **471/487** | 16 | 0 | 52 | **partial retry 완료(6/27)** — partial 16 known failure → STEP_C_RUN_LOG.md |
| **4** | 101680~214320 | 재적재 | **443/487** | 44 | 0 | 131 | **partial retry 완료(6/27)** — partial 44 known failure → STEP_C_RUN_LOG.md |
| **5** | 214330~305720 | 재적재 | **443/487** | 43 | 1 | 120 | **partial retry 완료(6/27)** — partial 43 + none 1 known failure → STEP_C_RUN_LOG.md |
| **6** | 306040~425040 | 최초 적재 | **189/487** | 297 | 1 | 599 | **1회 전체 실행 완료(6/27)** |
| **7** | 425420~488720 | 최초 적재 | **0/487** | 486 | 1 | 1634 | **1회 전체 실행 완료(6/27)** — 7yr 0 = bars 부재 known |
| **8** | 488770~950250 | 최초 적재 | **18/485** | 89 | 378 | 3011 | **1회 전체 실행 완료(6/27)** — none 378 = merged 없음 |

---

## Chunk 0 — 재적재 (test)

- **범위**: `000020` ~ `000815` (50종)
- **7연도 완료**: 50 · **partial**: 0 · **none**: 0
- **failure log** (고유 task): 0
- **다음 액션**: **완료 — 스킵**

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c0_20260624.json` | 2026-06-24T09:52:21+00:00 | 350 | 0 | pykrx_mcap:350 |
| `enrich_market_cap_c0_20260625.json` | 2026-06-25T14:41:47+00:00 | 350 | 0 | pykrx_mcap:350 |

---

## Chunk 1 — 재적재

- **범위**: `000850` ~ `014950` (488종)
- **7연도 완료**: 486 · **partial**: 2 · **none**: 0
- **failure log** (고유 task): 8
- **다음 액션**: **partial retry 완료(6/27)** — partial 2 known failure → STEP_C_RUN_LOG.md

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c1_20260625.json` | 2026-06-25T11:09:30+00:00 | 3408 | 8 | pykrx_mcap:3408 |
| `enrich_market_cap_c1_20260626.json` | 2026-06-26T02:28:32+00:00 | 3408 | 8 | pykrx_mcap:3408 |
| `enrich_market_cap_c1_20260627.json` | 2026-06-27T00:46:33+00:00 | 6 | 8 | pykrx_mcap:6 |

### partial 종목 (2개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `012210` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `014950` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |

---

## Chunk 2 — 재적재

- **범위**: `014970` ~ `053050` (487종)
- **7연도 완료**: 484 · **partial**: 3 · **none**: 0
- **failure log** (고유 task): 12
- **다음 액션**: **partial retry 완료(6/27)** — partial 3 known failure → STEP_C_RUN_LOG.md

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c2_20260625.json` | 2026-06-25T11:38:11+00:00 | 3397 | 12 | pykrx_mcap:3397 |
| `enrich_market_cap_c2_20260626.json` | 2026-06-26T02:59:43+00:00 | 3397 | 12 | pykrx_mcap:3397 |
| `enrich_market_cap_c2_20260627.json` | 2026-06-27T00:46:44+00:00 | 9 | 12 | pykrx_mcap:9 |

### partial 종목 (3개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `017860` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `031210` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `036220` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |

---

## Chunk 3 — 재적재

- **범위**: `053060` ~ `101670` (487종)
- **7연도 완료**: 471 · **partial**: 16 · **none**: 0
- **failure log** (고유 task): 52
- **다음 액션**: **partial retry 완료(6/27)** — partial 16 known failure → STEP_C_RUN_LOG.md

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c3_20260625.json` | 2026-06-25T12:06:27+00:00 | 3287 | 122 | pykrx_mcap:3287 |
| `enrich_market_cap_c3_20260626.json` | 2026-06-26T03:28:53+00:00 | 3357 | 52 | pykrx_mcap:3287, etf_aum:70 |
| `enrich_market_cap_c3_20260627.json` | 2026-06-27T00:50:39+00:00 | 60 | 52 | pykrx_mcap:60 |

### partial 종목 (16개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `059270` | 6/7 | 2020(failed/empty) |
| `061090` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `062040` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `064400` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `068100` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `079900` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `081180` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `086710` | 6/7 | 2020(failed/empty) |
| `088280` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `088340` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `089860` | 6/7 | 2020(failed/empty) |
| `092790` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `096250` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `098070` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `099390` | 6/7 | 2020(failed/empty) |
| `099430` | 6/7 | 2020(failed/empty) |

---

## Chunk 4 — 재적재

- **범위**: `101680` ~ `214320` (487종)
- **7연도 완료**: 443 · **partial**: 44 · **none**: 0
- **failure log** (고유 task): 131
- **다음 액션**: **partial retry 완료(6/27)** — partial 44 known failure → STEP_C_RUN_LOG.md

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c4_20260625.json` | 2026-06-25T12:37:49+00:00 | 2510 | 899 | pykrx_mcap:2510 |
| `enrich_market_cap_c4_20260626.json` | 2026-06-26T09:49:20+00:00 | 3279 | 130 | pykrx_mcap:2510, etf_aum:769 |
| `enrich_market_cap_c4_20260627.json` | 2026-06-27T00:52:29+00:00 | 186 | 129 | pykrx_mcap:179, etf_aum:7 |

### partial 종목 (44개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `101970` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `102370` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `105760` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `107600` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `109670` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `111380` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `112290` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `114840` | 6/7 | 2020(failed/empty) |
| `125020` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `125490` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `126720` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `126730` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `127980` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `129920` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `136150` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `136410` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `137080` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `137310` | 6/7 | 2020(failed/empty) |
| `139990` | 6/7 | 2020(failed/empty) |
| `140430` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `145170` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `146060` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `146320` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `148930` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `159010` | 6/7 | 2020(failed/empty) |
| `160190` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `162300` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `163280` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `163730` | 6/7 | 2020(failed/empty) |
| `168360` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `172670` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `177900` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `187660` | 6/7 | 2020(failed/empty) |
| `188040` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `188260` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `195940` | 6/7 | 2020(failed/empty) |
| `198940` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `199430` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `199480` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `199550` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `199730` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `204610` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `209640` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `212710` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |

---

## Chunk 5 — 재적재

- **범위**: `214330` ~ `305720` (487종)
- **7연도 완료**: 443 · **partial**: 43 · **none**: 1
- **failure log** (고유 task): 120
- **다음 액션**: **partial retry 완료(6/27)** — partial 43 + none 1 known failure → STEP_C_RUN_LOG.md

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c5_20260625.json` | 2026-06-25T13:34:58+00:00 | 1980 | 1429 | pykrx_mcap:1980 |
| `enrich_market_cap_c5_20260626.json` | 2026-06-26T10:48:56+00:00 | 3289 | 120 | pykrx_mcap:1980, etf_aum:1309 |
| `enrich_market_cap_c5_20260627.json` | 2026-06-27T01:02:23+00:00 | 188 | 120 | pykrx_mcap:188 |

### partial 종목 (43개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `217590` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `226590` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `234030` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `236810` | 6/7 | 2020(failed/empty) |
| `240550` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `240600` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `247660` | 6/7 | 2020(failed/empty) |
| `248070` | 6/7 | 2020(failed/empty) |
| `251120` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `252990` | 6/7 | 2020(failed/empty) |
| `254490` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `257720` | 6/7 | 2020(failed/empty) |
| `259960` | 6/7 | 2020(failed/empty) |
| `261520` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `261780` | 6/7 | 2020(failed/empty) |
| `262840` | 6/7 | 2020(failed/empty) |
| `271830` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `271940` | 6/7 | 2020(failed/empty) |
| `273640` | 6/7 | 2020(failed/empty) |
| `274400` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `276040` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `276730` | 6/7 | 2020(failed/empty) |
| `277810` | 6/7 | 2020(failed/empty) |
| `278470` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `279570` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `282720` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `285800` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `287840` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `288180` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `288980` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `289220` | 6/7 | 2020(failed/empty) |
| `289930` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `290090` | 6/7 | 2020(failed/empty) |
| `290560` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `291810` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `294570` | 6/7 | 2020(failed/empty) |
| `295310` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `296640` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `298830` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `302440` | 6/7 | 2020(failed/empty) |
| `303530` | 6/7 | 2020(failed/empty) |
| `303810` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `304360` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |

### none 종목 (1개 — 7연도 중 유효 완료 0)

`301410`

---

## Chunk 6 — 최초 적재

- **범위**: `306040` ~ `425040` (487종)
- **7연도 완료**: 189 · **partial**: 297 · **none**: 1
- **failure log** (고유 task): 599
- **다음 액션**: **1회 전체 실행 완료(6/27)** — 7yr 189/487 → **chunk 7**

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c6_20260626.json` | 2026-06-26T12:03:58+00:00 | 2810 | 599 | pykrx_mcap:1661, etf_aum:1149 |
| `enrich_market_cap_c6_20260627.json` | 2026-06-27T01:08:43+00:00 | 2810 | 599 | pykrx_mcap:1661, etf_aum:1149 |

### partial 종목 (297개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `308080` | 6/7 | 2020(failed/empty) |
| `308430` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `309710` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `309960` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `310210` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `311320` | 6/7 | 2020(failed/empty) |
| `314140` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `314930` | 6/7 | 2020(failed/empty) |
| `315640` | 6/7 | 2020(failed/empty) |
| `317450` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `318060` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `318160` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `321370` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `321820` | 6/7 | 2020(failed/empty) |
| `322310` | 6/7 | 2020(failed/empty) |
| `323410` | 6/7 | 2020(failed/empty) |
| `328130` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `329180` | 6/7 | 2020(failed/empty) |
| `330730` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `331740` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `333620` | 6/7 | 2020(failed/empty) |
| `334970` | 6/7 | 2020(failed/empty) |
| `336680` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `338220` | 6/7 | 2020(failed/empty) |
| `338840` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `340450` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `340810` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `340930` | 6/7 | 2020(failed/empty) |
| `342870` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `347700` | 6/7 | 2020(failed/empty) |
| `347850` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `348030` | 6/7 | 2020(failed/empty) |
| `348080` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `348340` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `348370` | 6/7 | 2020(failed/empty) |
| `351330` | 6/7 | 2020(failed/empty) |
| `351870` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `352090` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `352480` | 6/7 | 2020(failed/empty) |
| `352700` | 6/7 | 2020(failed/empty) |
| `352910` | 6/7 | 2020(failed/empty) |
| `353590` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `354320` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `355390` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `355690` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `356680` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `356890` | 6/7 | 2020(failed/empty) |
| `357230` | 6/7 | 2020(failed/empty) |
| `357430` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `357580` | 6/7 | 2020(failed/empty) |
| `357880` | 6/7 | 2020(failed/empty) |
| `358570` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `360070` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `360350` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `361390` | 6/7 | 2020(failed/empty) |
| `361570` | 6/7 | 2020(failed/empty) |
| `361610` | 6/7 | 2020(failed/empty) |
| `361670` | 6/7 | 2020(failed/empty) |
| `362320` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `362990` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `363250` | 6/7 | 2020(failed/empty) |
| `363260` | 6/7 | 2020(failed/empty) |
| `364950` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `365270` | 6/7 | 2020(failed/empty) |
| `365330` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `365340` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `365900` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `366030` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `367000` | 6/7 | 2020(failed/empty) |
| `368600` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `368770` | 6/7 | 2020(failed/empty) |
| `368970` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `370090` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `371950` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `372170` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `372320` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `372800` | 6/7 | 2020(failed/empty) |
| `372910` | 6/7 | 2020(failed/empty) |
| `373110` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `373160` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `373170` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `373200` | 6/7 | 2020(failed/empty) |
| `373220` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `375270` | 6/7 | 2020(failed/empty) |
| `375500` | 6/7 | 2020(failed/empty) |
| `375760` | 6/7 | 2020(failed/empty) |
| `375770` | 6/7 | 2020(failed/empty) |
| `376180` | 6/7 | 2020(failed/empty) |
| `376270` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `376290` | 6/7 | 2020(failed/empty) |
| `376300` | 6/7 | 2020(failed/empty) |
| `376410` | 6/7 | 2020(failed/empty) |
| `376900` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `376930` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `376980` | 6/7 | 2020(failed/empty) |
| `377030` | 6/7 | 2020(failed/empty) |
| `377190` | 6/7 | 2020(failed/empty) |
| `377220` | 6/7 | 2020(failed/empty) |
| `377300` | 6/7 | 2020(failed/empty) |
| `377330` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `377450` | 6/7 | 2020(failed/empty) |
| `377460` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `377480` | 6/7 | 2020(failed/empty) |
| `377740` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `377990` | 6/7 | 2020(failed/empty) |
| `378340` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `378800` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `378850` | 6/7 | 2020(failed/empty) |
| `379780` | 6/7 | 2020(failed/empty) |
| `379790` | 6/7 | 2020(failed/empty) |
| `379800` | 6/7 | 2020(failed/empty) |
| `379810` | 6/7 | 2020(failed/empty) |
| `380340` | 6/7 | 2020(failed/empty) |
| `380540` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `380550` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `381170` | 6/7 | 2020(failed/empty) |
| `381180` | 6/7 | 2020(failed/empty) |
| `381560` | 6/7 | 2020(failed/empty) |
| `381570` | 6/7 | 2020(failed/empty) |
| `381620` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `381970` | 6/7 | 2020(failed/empty) |
| `382150` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `382480` | 6/7 | 2020(failed/empty) |
| `382800` | 6/7 | 2020(failed/empty) |
| `382840` | 6/7 | 2020(failed/empty) |
| `382900` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `383220` | 6/7 | 2020(failed/empty) |
| `383310` | 6/7 | 2020(failed/empty) |
| `383800` | 6/7 | 2020(failed/empty) |
| `383930` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `384470` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `385510` | 6/7 | 2020(failed/empty) |
| `385520` | 6/7 | 2020(failed/empty) |
| `385540` | 6/7 | 2020(failed/empty) |
| `385550` | 6/7 | 2020(failed/empty) |
| `385560` | 6/7 | 2020(failed/empty) |
| `385590` | 6/7 | 2020(failed/empty) |
| `385600` | 6/7 | 2020(failed/empty) |
| `385710` | 6/7 | 2020(failed/empty) |
| `385720` | 6/7 | 2020(failed/empty) |
| `387270` | 6/7 | 2020(failed/empty) |
| `387280` | 6/7 | 2020(failed/empty) |
| `387570` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `388050` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `388210` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `388280` | 6/7 | 2020(failed/empty) |
| `388420` | 6/7 | 2020(failed/empty) |
| `388610` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `388720` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `388790` | 6/7 | 2020(failed/empty) |
| `388870` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `389020` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `389030` | 6/7 | 2020(failed/empty) |
| `389140` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `389260` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `389470` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `389500` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `389650` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `389680` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `390390` | 6/7 | 2020(failed/empty) |
| `390400` | 6/7 | 2020(failed/empty) |
| `391600` | 6/7 | 2020(failed/empty) |
| `391670` | 6/7 | 2020(failed/empty) |
| `391710` | 6/7 | 2020(failed/empty) |
| `393210` | 6/7 | 2020(failed/empty) |
| `393890` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `393970` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `394280` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `394420` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `394660` | 6/7 | 2020(failed/empty) |
| `394670` | 6/7 | 2020(failed/empty) |
| `394800` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `395150` | 6/7 | 2020(failed/empty) |
| `395160` | 6/7 | 2020(failed/empty) |
| `395170` | 6/7 | 2020(failed/empty) |
| `395270` | 6/7 | 2020(failed/empty) |
| `395280` | 6/7 | 2020(failed/empty) |
| `395290` | 6/7 | 2020(failed/empty) |
| `395400` | 6/7 | 2020(failed/empty) |
| `395750` | 6/7 | 2020(failed/empty) |
| `395760` | 6/7 | 2020(failed/empty) |
| `396270` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `396300` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `396470` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `396500` | 6/7 | 2020(failed/empty) |
| `396510` | 6/7 | 2020(failed/empty) |
| `396520` | 6/7 | 2020(failed/empty) |
| `396690` | 6/7 | 2020(failed/empty) |
| `397030` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `397420` | 6/7 | 2020(failed/empty) |
| `397810` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `398120` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `399110` | 6/7 | 2020(failed/empty) |
| `399580` | 6/7 | 2020(failed/empty) |
| `399720` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `400570` | 6/7 | 2020(failed/empty) |
| `400580` | 6/7 | 2020(failed/empty) |
| `400590` | 6/7 | 2020(failed/empty) |
| `400760` | 6/7 | 2020(failed/empty) |
| `400970` | 6/7 | 2020(failed/empty) |
| `401170` | 6/7 | 2020(failed/empty) |
| `401470` | 6/7 | 2020(failed/empty) |
| `401590` | 6/7 | 2020(failed/empty) |
| `402030` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `402340` | 6/7 | 2020(failed/empty) |
| `402460` | 6/7 | 2020(failed/empty) |
| `402490` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `402970` | 6/7 | 2020(failed/empty) |
| `403490` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `403550` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `403790` | 6/7 | 2020(failed/empty) |
| `403850` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `403870` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `404120` | 6/7 | 2020(failed/empty) |
| `404260` | 6/7 | 2020(failed/empty) |
| `404540` | 6/7 | 2020(failed/empty) |
| `404650` | 6/7 | 2020(failed/empty) |
| `404990` | 6/7 | 2020(failed/empty) |
| `405000` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `405100` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `405920` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `406820` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `407300` | 6/7 | 2020(failed/empty) |
| `407310` | 6/7 | 2020(failed/empty) |
| `407400` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `407820` | 6/7 | 2020(failed/empty) |
| `407830` | 6/7 | 2020(failed/empty) |
| `408470` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `408900` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `408920` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `409810` | 6/7 | 2020(failed/empty) |
| `409820` | 6/7 | 2020(failed/empty) |
| `410870` | 6/7 | 2020(failed/empty) |
| `411060` | 6/7 | 2020(failed/empty) |
| `411080` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `411420` | 6/7 | 2020(failed/empty) |
| `411540` | 6/7 | 2020(failed/empty) |
| `411860` | 6/7 | 2020(failed/empty) |
| `412350` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `412540` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `412560` | 6/7 | 2020(failed/empty) |
| `412570` | 6/7 | 2020(failed/empty) |
| `412770` | 6/7 | 2020(failed/empty) |
| `413220` | 6/7 | 2020(failed/empty) |
| `413390` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `413630` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `413640` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `413930` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `414270` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `414780` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `415340` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `415380` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `415640` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `415760` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `415920` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `416090` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `416180` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `417010` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `417180` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `417200` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `417310` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `417450` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `417500` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `417630` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `417790` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `417840` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `417860` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `417970` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `418250` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `418420` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `418470` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `418550` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `418620` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `418660` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `418670` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419050` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `419080` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419120` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419420` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419430` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419530` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419540` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419650` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `419890` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `420570` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `420770` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `421320` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `422420` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `423160` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `423170` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `423920` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `424460` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `424760` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `424870` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `424960` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `424980` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `425040` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |

### none 종목 (1개 — 7연도 중 유효 완료 0)

`422260`

---

## Chunk 7 — 최초 적재

- **범위**: `425420` ~ `488720` (487종)
- **7연도 완료**: 0 · **partial**: 486 · **none**: 1
- **failure log** (고유 task): 1634
- **다음 액션**: **최초 적재** — chunk 7 **1회 전체 실행** (~90분+, KRX 세션 주의)

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c7_20260626.json` | 2026-06-26T12:57:47+00:00 | 1776 | 1633 | pykrx_mcap:530, etf_aum:1246 |
| `enrich_market_cap_c7_20260627.json` | 2026-06-27T02:03:31+00:00 | 1776 | 1633 | pykrx_mcap:530, etf_aum:1246 |

### partial 종목 (486개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `425420` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `426020` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `426030` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `426150` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `427120` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `428510` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `428560` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `429000` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `429010` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `429270` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `429740` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `429760` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `429980` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `430500` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `430690` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `431190` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `432320` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `432430` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `432470` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `432600` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `432720` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `432840` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `432980` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `433220` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `433250` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `433330` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `433500` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `433880` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `433970` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `433980` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `434060` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `434480` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `434730` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `434960` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `435040` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `435420` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `435530` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `435540` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `435550` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `435570` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `436140` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `437070` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `437080` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `437350` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `437370` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `437730` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `438080` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438100` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438320` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438330` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438560` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438570` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438700` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `438740` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `438900` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `439090` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `439260` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `439580` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `439860` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `439870` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `439960` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `440110` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `440290` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `440320` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `440340` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `440640` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `440650` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `440910` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `441270` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `441540` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `441640` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `441680` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `441800` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442090` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442260` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442320` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442550` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442560` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442570` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `442580` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `443060` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `443250` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `443670` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `444200` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `444490` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `444530` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `445090` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `445150` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `445180` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `445290` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `445680` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `445690` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `445910` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `446070` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `446540` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `446690` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `446700` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `446720` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `446770` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `446840` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `447430` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `447620` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `447660` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `447770` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448100` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448280` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `448290` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448300` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448330` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448490` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448540` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448570` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448630` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `448710` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `448730` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `448900` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `449170` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449180` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449190` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449450` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `449580` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449680` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449690` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449770` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `449780` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `450080` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `450180` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `450190` | 5/7 | 2020(failed/empty), 2021(failed/empty) |
| `450330` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `450520` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `450910` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `450950` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `451000` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451060` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451150` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451220` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451250` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `451530` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451540` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451600` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451670` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451760` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `451800` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452160` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452190` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `452200` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `452250` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452260` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452280` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452300` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452360` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `452400` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `452430` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `452450` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `453010` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453060` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453080` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453330` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453340` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453450` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `453630` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453640` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453650` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453660` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453810` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453820` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453850` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453860` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453870` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `453950` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `454180` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `454320` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `454780` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `454910` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `455030` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `455180` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `455660` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `455850` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `455860` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `455890` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `455900` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `455960` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456010` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `456040` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456070` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `456160` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `456200` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456250` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456600` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456610` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456680` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `456880` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `457190` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `457370` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `457480` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `457550` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `457600` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `457690` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `457700` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `457930` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `457990` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458030` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458210` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458250` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458260` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458350` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `458650` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `458730` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458750` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458760` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `458870` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `459100` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `459510` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `459550` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `459560` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `459580` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `459750` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `459790` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `460270` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `460470` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `460660` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `460850` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `460860` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `460870` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `460930` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `460940` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `460960` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461030` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `461300` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `461340` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461450` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461460` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461490` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461500` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461580` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461600` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461900` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461910` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `461950` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `462010` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `462310` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `462330` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `462340` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `462350` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `462510` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `462520` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `462860` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `462870` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `462900` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `462980` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `463020` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `463050` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `463250` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `463290` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `463300` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `463480` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `463640` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `463680` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `463690` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `464240` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464280` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `464310` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464440` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464470` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464490` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `464500` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `464580` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `464600` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464610` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464920` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `464930` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465320` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465330` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465350` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465480` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `465580` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465610` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465620` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465660` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465670` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465770` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `465780` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `466100` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `466410` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `466690` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `466810` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `466920` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `466930` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `466940` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `466950` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `467930` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `468370` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `468380` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `468530` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `468630` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `468760` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `469050` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469060` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469070` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469150` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469160` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469170` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469480` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `469530` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469610` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `469750` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `469790` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469830` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469880` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `469900` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `470310` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `471040` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `471050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `471230` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `471460` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `471760` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `471780` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `471820` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `471990` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472150` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472160` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472170` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472220` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `472230` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `472720` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472830` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472840` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472850` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `472870` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `472920` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473000` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `473050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `473290` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473330` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473440` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473460` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473490` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473590` | 4/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty) |
| `473640` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `473950` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `473980` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474170` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474220` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474390` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474490` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474590` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474610` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474650` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `474660` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474800` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474920` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `474930` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475070` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475150` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475230` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `475240` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475250` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475260` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475270` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475280` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475300` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475310` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475350` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475380` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475400` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475430` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `475460` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `475560` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475580` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475630` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475660` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475720` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `475830` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `475960` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476000` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476030` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476040` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `476060` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476070` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476260` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476310` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476450` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476550` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476690` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476750` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476760` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476800` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `476830` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `476850` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477340` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477380` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477470` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477490` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477730` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477760` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `477850` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `478110` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `478150` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `478340` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `478390` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `478440` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `478560` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `479080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `479520` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `479620` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `479730` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `479850` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `479880` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `479960` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `480020` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `480030` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `480040` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `480260` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `480310` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `480370` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `480460` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481060` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481070` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `481180` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481190` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481340` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481430` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481850` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `481890` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `482030` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `482520` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `482630` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `482680` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `482690` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `482730` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483020` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483030` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483280` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483290` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483320` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483330` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483340` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483420` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483570` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `483650` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `484120` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `484130` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `484590` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `484790` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `484810` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `484870` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `484880` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `484890` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `485540` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `485690` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `485810` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `486240` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `486290` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `486450` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `486630` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `486830` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `486990` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `487130` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487230` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487240` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487340` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487360` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487570` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487580` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `487720` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487750` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487830` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487910` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487920` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `487950` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488060` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488200` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488210` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488280` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `488290` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488480` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488500` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488720` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |

### none 종목 (1개 — 7연도 중 유효 완료 0)

`461270`

---

## Chunk 8 — 최초 적재

- **범위**: `488770` ~ `950250` (485종)
- **7연도 완료**: 18 · **partial**: 89 · **none**: 378
- **failure log** (고유 task): 3011
- **다음 액션**: **최초 적재** — chunk 8 **1회 전체 실행** (6/26 중단, 18/485 7yr 완료)

### 실행 이력 (reports)

| 파일 | 시각 (UTC) | done | failed | methods |
|------|------------|------|--------|---------|
| `enrich_market_cap_c8_20260626.json` | 2026-06-26T13:45:33+00:00 | 384 | 3011 | etf_aum:206, pykrx_mcap:178 |
| `enrich_market_cap_c8_20260627.json` | 2026-06-27T02:46:42+00:00 | 384 | 3011 | etf_aum:206, pykrx_mcap:178 |

### partial 종목 (89개)

| 종목 | 완료 연도 | 미완 연도·상태 |
|------|-----------|----------------|
| `488770` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `488900` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `488980` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489000` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489010` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489030` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489210` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489250` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489290` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489460` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `489480` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489500` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `489730` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489790` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `489860` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `490090` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `490330` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `490470` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `490480` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `490490` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `490590` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `490600` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491000` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `491010` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491090` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491220` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491230` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491510` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491610` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491620` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491630` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491700` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491820` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `491830` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `492220` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `492500` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `493280` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `493330` | 1/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty), 2025(failed/empty) |
| `493420` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `493790` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `493810` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494120` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `494180` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494210` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494220` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494300` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494310` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494330` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494340` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494410` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494420` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494670` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494840` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `494890` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495040` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495060` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495230` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495330` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495550` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495750` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495850` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `495940` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `496020` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `496070` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `496080` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `496090` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `496120` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `496130` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `496770` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `497510` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `497520` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `497570` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `497780` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `497880` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `498050` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `498180` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `498270` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `498390` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `498400` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `498410` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `498610` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |
| `498860` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `499150` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `499660` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `499790` | 3/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty) |
| `950210` | 6/7 | 2020(failed/empty) |
| `950220` | 6/7 | 2020(failed/empty) |
| `950250` | 2/7 | 2020(failed/empty), 2021(failed/empty), 2022(failed/empty), 2023(failed/empty), 2024(failed/empty) |

### none 종목 (378개 — 7연도 중 유효 완료 0)

`500020`, `500023`, `500024`, `500028`, `500029`, `500030`, `500035`, `500036`, `500037`, `500038`, `500040`, `500041`, `500050`, `500051`, `500061`, `500063`, `500067`, `500068`, `500069`, `500071`, `500072`, `500085`, `500086`, `500091`, `500093`, `500094`, `500095`, `500096`, `500097`, `500098`, `500099`, `500100`, `500101`, `500102`, `510027`, `510043`, `510044`, `510045`, `520037`, `520038`, `520039`, `520040`, `520046`, `520047`, `520054`, `520056`, `520057`, `520064`, `520065`, `520066`, `520068`, `520069`, `520072`, `520073`, `520074`, `520075`, `520076`, `520077`, `520078`, `520079`, `520080`, `520081`, `520082`, `520083`, `520084`, `520085`, `520086`, `520087`, `520088`, `520089`, `520090`, `520091`, `520092`, `520093`, `520094`, `520097`, `520098`, `520099`, `520100`, `520101`, `530031`, `530036`, `530055`, `530056`, `530060`, `530061`, `530062`, `530063`, `530064`, `530067`, `530083`, `530084`, `530089`, `530090`, `530092`, `530094`, `530095`, `530096`, `530104`, `530106`, `530107`, `530112`, `530113`, `530114`, `530115`, `530116`, `530117`, `530118`, `530119`, `530120`, `530121`, `530122`, `530123`, `530124`, `530125`, `530126`, `530127`, `530128`, `530129`, `530130`, `530131`, `530132`, `530133`, `530134`, `530135`, `530136`, `530137`, `530138`, `530139`, `530140`, `530141`, `530142`, `530143`, `530145`, `550041`, `550043`, `550062`, `550063`, `550064`, `550069`, `550070`, `550082`, `550084`, `550085`, `550087`, `550088`, `550089`, `550091`, `550092`, `550093`, `550095`, `550096`, `550097`, `550098`, `550099`, `550100`, `570019`, `570022`, `570023`, `570029`, `570047`, `570050`, `570051`, `570059`, `570060`, `570061`, `570063`, `570064`, `570065`, `570066`, `570069`, `570070`, `570071`, `570072`, `570073`, `570074`, `570081`, `570082`, `570085`, `570090`, `570091`, `570092`, `570094`, `570095`, `570096`, `570097`, `570098`, `570099`, `570100`, `570101`, `570102`, `570103`, `570104`, `570105`, `570106`, `570107`, `570108`, `570109`, `570110`, `570111`, `570114`, `570115`, `570116`, `570117`, `570118`, `570119`, `570120`, `570121`, `570122`, `570123`, `570124`, `580010`, `580022`, `580023`, `580026`, `580032`, `580033`, `580034`, `580035`, `580039`, `580043`, `580044`, `580047`, `580048`, `580049`, `580050`, `580051`, `580052`, `580053`, `580054`, `580056`, `580057`, `580058`, `580059`, `580060`, `580061`, `580062`, `580063`, `580064`, `580065`, `580066`, `580067`, `580068`, `580069`, `580070`, `580071`, `580072`, `580073`, `580074`, `580075`, `580076`, `580077`, `580078`, `580079`, `580080`, `580081`, `580082`, `580083`, `580084`, `580085`, `580086`, `580087`, `610001`, `610003`, `610007`, `610008`, `610009`, `610012`, `610013`, `610018`, `610020`, `610022`, `610023`, `610024`, `610025`, `610028`, `610029`, `610030`, `610034`, `610035`, `610036`, `610037`, `610038`, `610039`, `610040`, `610045`, `610047`, `610049`, `610051`, `610055`, `610056`, `610057`, `610058`, `610059`, `610060`, `610061`, `610062`, `610063`, `610064`, `610066`, `610068`, `610069`, `610070`, `610071`, `610072`, `610073`, `610074`, `610075`, `610076`, `610077`, `610078`, `610079`, `610080`, `610081`, `610082`, `610083`, `610084`, `610085`, `610086`, `610087`, `610088`, `610089`, `610090`, `610091`, `610092`, `610093`, `610094`, `610095`, `610096`, `610097`, `610098`, `610099`, `610100`, `610101`, `700011`, `700012`, `700013`, `700014`, `700017`, `700018`, `700022`, `700023`, `700026`, `700027`, `700028`, `700029`, `700030`, `700031`, `700032`, `700033`, `700034`, `700035`, `700036`, `760004`, `760005`, `760006`, `760007`, `760008`, `760009`, `760010`, `760011`, `760012`, `760013`, `760014`, `760015`, `760016`, `760017`, `760018`, `760019`, `760020`, `760021`, `760022`, `760023`, `760024`, `760025`, `760026`, `760027`, `760028`

---

## 금지·운영

- `archive_enrich_market_cap --chunk N` 은 **해당 chunk 전 종목 × 7연도 전부 API 호출** (완료분 skip 없음).
- **chunk 1~8 일괄 for-loop 금지** — 사용자가 지정한 chunk만.
- **한 세션 1~3 chunk** 권장.
- KRX 세션 **~1시간** — chunk >1h 시 후반 failed 多.

## 새 채팅 예시

> `docs/STEP_C_HANDOFF.md` chunk **1** partial 2종만 점검해줘. chunk 일괄 실행 금지.

> `docs/STEP_C_HANDOFF.md` 읽고 Step C **chunk 6 최초 적재만** 터미널 실행해줘.
