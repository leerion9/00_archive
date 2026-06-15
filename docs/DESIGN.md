# Naver 일봉 아카이브 — 설계 문서

> **문서 목적**: 한국 주식 일봉(OHLCV) 장기 아카이브를 네이버 금융에서 수집·보관·병합하고,
> 여러 매매 전략의 백테스트에 공통으로 활용하기 위한 **독립 프로젝트** 설계안.
>
> **moa와의 관계**: moa 자동매매 프로젝트와 **별개**로 구축한다.
> 특정 전략(52주 돌파, 시총 필터, RS 등)을 전제하지 않으며,
> moa의 `core/naver_universe.py`, `core/history_cache.merge_bars` 등은 **참고·재사용 가능**하나
> 운영 캐시(`data/history_cache/`)와 데이터 경로는 **분리**한다.
>
> **작성 기준일**: 2026-06-12

---

## 1. 목적 및 범위

### 1.1 목적

- **2000년 ~ 2026-05-31** 구간(역순 수집 우선)의 KOSPI/KOSDAQ **일봉 OHLCV** 아카이브 구축
- PC·노트북 **2 worker**가 서로 다른 수집 대상을 병렬 처리 후 **merge**
- 시총·발행주식수 등 **즉시 수집 어려운 필드**는 1차 완료 후 **2차 보강**
- 상장일·폐지일 등 **기업 이벤트 메타**를 별도 보관하고, 백테스트 기간과 겹치면 **경고**

### 1.2 1차 수집 범위 (Phase 1)

| 포함 | 미포함 (2차 이후) |
|------|-------------------|
| OHLCV (open, high, low, close, volume) | 시가총액 (과거 일별) |
| date (YYYYMMDD) | 발행주식수 (과거 일별) |
| symbol, 종목명(스냅샷) | 거래대금 (공식값; close×volume 근사 가능) |
| price_basis / volume_basis 메타 | 상장폐지 종목 전체 OHLCV |
| 상장일·폐지일 (events 마스터) | 분봉 |

### 1.3 수집 대상 종목 (Phase 1)

- **현재 상장** KOSPI/KOSDAQ 전체 (~3,900종+, `naver_symbol_master` 기준)
- 상장폐지 종목은 Phase 1에서 **제외** (필요 시 Phase 2에서 KRX/FDR 등으로 보강)

### 1.4 생존편향 (survivorship bias)

- Phase 1은 **현재 상장 종목**만 포함하므로, 과거 시점 유니버스와 차이가 날 수 있다.
- 이는 **전략·유니버스 정의에 따라** 백테스트 해석 시 별도 검토할 사항이며,
  아카이브 설계상 **Phase 2에서 상장폐지 종목 레이어 추가**로 보완 가능하도록 열어 둔다.
- 상장폐지 보강의 **우선순위·필요 여부**는 향후 백테스트할 전략의 유니버스 정의에 맡긴다.
  (아카이브 자체는 특정 시총·유동성 필터를 가정하지 않는다.)

---

## 2. 설계 원칙

| 원칙 | 설명 |
|------|------|
| **전략 중립** | 특정 매매 전략·필터·포지션 규칙을 전제하지 않음 |
| **역순 수집** | 2026 → 2025 → … → 2000 (연도 단위 우선순위) |
| **분산 수집** | PC·노트북이 **서로 다른 (symbol, year) task**만 처리 |
| **멱등성** | 동일 task 재실행 시 date dedup으로 결과 동일 |
| **운영 분리** | moa `history_cache`와 경로·용도·보관 기간 완전 분리 |
| **확장성** | `bars` / `meta` / `fields`(미래) / `events` 스키마 분리 |
| **이벤트 알림** | 상장·폐지일 별도 마스터; 백테스트 구간과 겹치면 경고 리포트 |

---

## 3. 데이터 소스

### 3.1 1차: 네이버 금융 `sise_day.naver`

- URL: `https://finance.naver.com/item/sise_day.naver?code={symbol}&page={n}`
- 페이지당 약 **10거래일**, page 1 = **최신**
- 장기 종목은 page **~650** 수준에서 2000년 초반 도달 (종목·상장일마다 다름)
- 네이버 page 상한 약 **800** (종목별 상이)

**수정주가**: 네이버 `sise_day`는 pykrx `adjusted=True` 및 FDR `NAVER:` 소스와
날짜별 종가가 일치하는 경우가 확인됨. Phase 0에서 **10종 교차검증 후** `price_basis=adjusted` 확정.

**거래량**: 네이버·pykrx 모두 **액면분할 미보정(raw) 거래량**인 경우가 많음.
스키마에 `volume_basis=raw` 명시.

### 3.2 상장폐지 종목 (Phase 2 참고)

| 소스 | 용도 |
|------|------|
| FinanceDataReader `StockListing('KRX-DELISTING')` | 폐지 종목 목록 (~4,000+) |
| FDR `KRX-DELISTING:{code}` / `NAVER:{code}` | 종목별 OHLCV (종목·시점마다 성공/실패) |
| pykrx `get_market_ohlcv_by_date` | 일봉·시총 등 |
| KRX 정보데이터시스템 | 공식 데이터 (수동/유료) |

네이버: **최근 상장폐지**는 일봉이 남는 경우 있으나, **오래된 폐지**는 0건인 경우 많음.
→ Phase 1은 현재 상장만, Phase 2에서 폐지 레이어 추가.

---

## 4. 디렉터리 구조

```
data/naver_daily_archive/
├── config/
│   ├── collection_plan.json      # 전역 계획 (연도 범위, 종료일)
│   ├── worker_pc.json            # worker_id=pc
│   └── worker_laptop.json        # worker_id=laptop
├── manifest/
│   ├── tasks.jsonl               # 전체 (symbol, year) task
│   └── progress.jsonl            # worker별 완료/실패 로그
├── master/
│   ├── symbols_active.json       # Phase 1 수집 대상 스냅샷
│   └── listing_events.json       # 상장/폐지/합병 등 이벤트
├── raw/
│   ├── pc/                       # worker별 원본 (merge 전)
│   │   └── {symbol}/
│   │       └── {year}.json
│   └── laptop/
│       └── {symbol}/{year}.json
├── merged/
│   └── {symbol}.json             # 종목별 통합 (백테스트 1차 입력)
├── reports/
│   ├── merge_report_{date}.json
│   └── backtest_event_warnings_{run_id}.json
└── logs/
    └── archive_{worker_id}_{date}.log
```

**git**: `data/naver_daily_archive/` 전체 제외 (용량·크롤링 산출물).

**PC ↔ 노트북 동기화**: USB / 클라우드 / rsync로 `raw/`, `manifest/`, `master/` 복사.
`merged/`는 어느 한쪽에서 merge 스크립트 실행 후 공유.

---

## 5. 데이터 스키마

### 5.1 연도 chunk — `raw/{worker}/{symbol}/{year}.json`

한 **task = (symbol, year)** 의 결과물.

```json
{
  "schema_version": 1,
  "task_id": "005930:2025",
  "symbol": "005930",
  "year": 2025,
  "source": "naver_sise_day",
  "price_basis": "adjusted",
  "volume_basis": "raw",
  "worker_id": "pc",
  "fetched_at_iso": "2026-06-12T10:30:00+09:00",
  "pages_fetched": [1, 2, 3, 45],
  "bar_count": 248,
  "date_range": {"from": "20250102", "to": "20251230"},
  "bars": [
    {
      "date": "20251230",
      "open": 53000,
      "high": 53500,
      "low": 52800,
      "close": 53200,
      "volume": 12345678
    }
  ]
}
```

- `date`: **YYYYMMDD** (네이버 `YYYY.MM.DD` → 파싱 시 변환)
- `bars` 정렬: **최신순** (merge 시 dedup 기준 통일)

### 5.2 종목 통합 — `merged/{symbol}.json`

```json
{
  "schema_version": 1,
  "symbol": "005930",
  "name": "삼성전자",
  "source": "naver_sise_day",
  "price_basis": "adjusted",
  "volume_basis": "raw",
  "updated_at_iso": "2026-06-12T15:00:00+09:00",
  "years_complete": [2026, 2025, 2024],
  "years_pending": [2023, 2022],
  "bar_count": 620,
  "date_range": {"from": "20240102", "to": "20260612"},
  "bars": [],
  "fields": {
    "market_cap": {"status": "empty", "source": null, "updated_at": null},
    "shares_outstanding": {"status": "empty", "source": null, "updated_at": null},
    "trading_value": {"status": "empty", "source": null, "updated_at": null}
  }
}
```

`fields.*.status`: `empty` | `partial` | `complete`

대용량 fundamental은 sidecar 허용:

```
merged/{symbol}_fundamentals.parquet   # date index: mcap, shares, ...
```

### 5.3 상장/폐지 이벤트 — `master/listing_events.json`

백테스트 **사전 경고**용. OHLCV 수집과 **독립 갱신**.

```json
{
  "schema_version": 1,
  "updated_at_iso": "2026-06-12T09:00:00+09:00",
  "source": "krx_listing+fdr_delisting",
  "symbols": {
    "005930": {
      "name": "삼성전자",
      "market": "KOSPI",
      "listing_date": "19750611",
      "delisting_date": null,
      "status": "listed",
      "events": []
    },
    "051170": {
      "name": "example",
      "market": "KOSDAQ",
      "listing_date": "20000101",
      "delisting_date": "20190428",
      "status": "delisted",
      "events": [
        {"type": "delisted", "date": "20190428", "reason": "상장폐지", "note": ""}
      ]
    }
  }
}
```

**이벤트 type (확장 가능)**

| type | 의미 | 백테스트 시 |
|------|------|-------------|
| `listed` | 상장일 | 상장 전 구간 데이터 없음 |
| `delisted` | 폐지일 | 폐지 후 거래 불가 |
| `suspended` | 거래정지 | 해당 기간 신호 왜곡 가능 |
| `merged` | 합병/인수 | 가격·코드 연속성 단절 |
| `code_change` | 코드 변경 | 동일 기업, 다른 ticker |

---

## 6. Task · Manifest

### 6.1 Task 정의

**단위: `(symbol, year)`** — worker 분할·merge에 최적.

```json
{"task_id":"005930:2025","symbol":"005930","year":2025,"priority":2025,"status":"pending"}
```

| 필드 | 설명 |
|------|------|
| `priority` | = `year` (큰 값 먼저: 2026 → 2000) |
| `status` | `pending` / `running` / `done` / `failed` / `skipped` |

**task 규모**: ~3,947 symbol × 27 year ≈ **106,000 task**

### 6.2 Task 생성 (`archive_plan`)

1. `symbols_active.json` ← 네이버 종목 마스터 스냅샷
2. `year = YEAR_TO .. YEAR_FROM` 역순 task 생성
3. **선택 prune**: `listing_date > {year}1231` → `skipped` (상장 전 연도)
4. `tasks.jsonl` 저장 (1회 생성 후 PC·노트북 공유)

### 6.3 Shard — PC / 노트북

**권장: symbol 코드 결정적 분할**

```python
def assign_worker(symbol: str, worker_id: str) -> bool:
    bucket = int(symbol) % 2
    return (bucket == 0 and worker_id == "pc") or (bucket == 1 and worker_id == "laptop")
```

| worker | 담당 | task 수 (approx) |
|--------|------|------------------|
| pc | `int(symbol) % 2 == 0` | ~53,000 |
| laptop | `int(symbol) % 2 == 1` | ~53,000 |

**금지**: 동일 `(symbol, year)` 를 두 worker가 동시 처리.

**“이어하기”**: 한 worker가 중단됐을 때 **같은 worker**로 재실행 → `pending` task만 처리.
병렬 분할과 별개 개념.

---

## 7. Worker 동작 (`archive_collect`)

### 7.1 실행 예

```bash
python -m scripts.archive_collect --worker pc --max-tasks 500
python -m scripts.archive_collect --worker laptop --max-tasks 200
```

### 7.2 Task 1건 처리 흐름

```
1. manifest: status=pending, 내 shard, priority DESC → 1건 pick
2. status → running; progress.jsonl append
3. Naver sise_day page=1,2,3,... fetch
4. bar.date < {year}0101 이면 중단 (해당 연도 수집 완료)
5. bar.date > {year}1231 이면 저장 제외 (다음 연도 task)
6. raw/{worker}/{symbol}/{year}.json 저장
7. status → done (실패 시 failed + error)
8. throttle
```

### 7.3 Throttle (네이버 차단 방지)

| 항목 | 권장값 |
|------|--------|
| delay_sec | 0.08 |
| jitter_sec | 0.03 |
| batch_size | 50 |
| batch_pause_sec | 3.0 |
| retry | 4회, backoff 5/15/30/60s |
| 일일 상한 | `--max-tasks` 로 worker별 제한 |

moa `HistoryCacheStore` 패턴 참고.

### 7.4 역순 연도와 HTTP 효율

- page 1 = 최신 → **2026 task**는 소수 page로 완료
- **2000 task**는 deep pagination → 수집 후반에 시간 집중
- 최근 연도부터 전 종목 커버 → **조기 중단해도 유용한 구간** 확보

---

## 8. Merge (`archive_merge`)

```
for symbol in symbols_active:
  chunks = raw/pc/{symbol}/*.json + raw/laptop/{symbol}/*.json
  bars = merge_by_date(all chunks)    # date dedup, newest-first
  write merged/{symbol}.json
  update years_complete / years_pending
  append merge_report
```

**규칙**

- 동일 `(symbol, year)` chunk가 양 worker에 존재 → **경고**, `fetched_at_iso` 최신 wins
- date dedup: 동일 date → **나중 merge wins** (또는 명시적 merge policy 문서화)
- `years_pending`: 2000~YEAR_TO 중 chunk 없는 연도

---

## 9. 상장/폐지 이벤트 · 백테스트 경고

### 9.1 이벤트 수집 (`archive_listing_events`)

| Phase | 소스 |
|-------|------|
| v1 | FDR `StockListing('KRX')` + 현재 상장 마스터 |
| v2 | FDR `StockListing('KRX-DELISTING')` |

→ `listing_events.json` 갱신 (수집 주기: plan 시 1회 + 분기/필요 시)

### 9.2 백테스트 전 검사 (`archive_event_check`)

입력: `symbols[]`, `from_ymd`, `to_ymd`, `listing_events.json`

| code | 조건 | 메시지 예 |
|------|------|-----------|
| `E_LISTING_IN_RANGE` | listing_date ∈ [from, to] | 상장일이 구간 내 — 상장 전 데이터 없음 |
| `E_DELIST_IN_RANGE` | delisting_date ∈ [from, to] | 폐지일이 구간 내 — 폐지 후 거래 불가 |
| `E_NOT_LISTED_YET` | from < listing_date | 구간 시작이 상장일 이전 |
| `E_ALREADY_DELISTED` | to > delisting_date | 구간 종료가 폐지일 이후 |

출력: `reports/backtest_event_warnings_{run_id}.json` + 콘솔 요약

**정책 (백테스트 엔진 설정)**

- `event_check=warn` (기본): 경고만, 실행 계속
- `event_check=strict`: 해당 종목 제외 또는 run 중단

---

## 10. Phase 2 — 필드 보강 (1차 완료 후)

| 필드 | 1차 | 2차 소스 | 저장 |
|------|-----|----------|------|
| OHLCV | Naver | — | `bars` |
| listing/delisting | events 마스터 | KRX-DELISTING | `listing_events.json` |
| market_cap | empty | pykrx | `fields` or parquet |
| shares_outstanding | empty | pykrx | `fields` or parquet |
| trading_value | empty | pykrx or close×volume | `fields` |
| delisted OHLCV | — | FDR/pykrx | `merged/` or `merged_delisted/` |

---

## 11. 제안 모듈 · 스크립트

> 새 프로젝트 폴더에서 구현 시 이름·경로는 자유롭게 변경 가능.
> moa에서 재사용할 코드는 아래 "참고" 항목.

| 파일 | 역할 |
|------|------|
| `core/archive_schema.py` | schema_version, task_id, chunk/merged payload |
| `core/archive_shard.py` | worker assign, task pick |
| `core/archive_merge.py` | chunk → merged, dedup |
| `core/archive_event_check.py` | listing/delisting vs backtest range |
| `core/archive_fetch.py` | Naver sise_day pagination (throttle) |
| `scripts/archive_plan.py` | tasks.jsonl 생성 |
| `scripts/archive_collect.py` | worker 실행 |
| `scripts/archive_merge.py` | raw → merged |
| `scripts/archive_listing_events.py` | listing_events 갱신 |
| `scripts/archive_status.py` | 진행률 (연도별 coverage) |

**moa 참고 (재사용 후보, 복사 또는 의존)**

- `core/naver_universe.fetch_symbol_history_naver`, `_parse_daily_bars_html`
- `core/history_cache.merge_bars`
- `core/naver_symbol_master.fetch_kr_symbol_master`

---

## 12. 설정

```env
ARCHIVE_BASE_DIR=data/naver_daily_archive
ARCHIVE_WORKER_ID=pc                    # pc | laptop
ARCHIVE_DELAY_SEC=0.08
ARCHIVE_JITTER_SEC=0.03
ARCHIVE_BATCH_SIZE=50
ARCHIVE_BATCH_PAUSE_SEC=3.0
ARCHIVE_MAX_TASKS_PER_RUN=0             # 0 = unlimited
ARCHIVE_YEAR_FROM=2000
ARCHIVE_YEAR_TO=2026
ARCHIVE_END_DATE=20260531               # 2026 chunk 상한 (YYYYMMDD)
```

---

## 13. 운영 시나리오

### Phase 0 — 준비 (약 1일)

1. `archive_plan` → `tasks.jsonl`, `symbols_active.json`
2. `archive_listing_events` → `listing_events.json`
3. PC·노트북 `config/worker_*.json` 배치
4. **P0 검증**: 10종 × pykrx adjusted 종가 diff = 0

### Phase 1 — 수집 (2~4주, 2 worker 병렬)

- PC: `--worker pc`, 노트북: `--worker laptop`
- 중단 시 동일 worker 재실행
- `raw/`, `manifest/` 주 1~2회 동기화

### Phase 1b — Merge (수시 / 1일 1회)

- `archive_merge` → `merged/`
- `archive_status`로 연도별 coverage 확인

### Phase 2 — 백테스트 연동

- `merged/` 또는 Parquet export를 백테스트 엔진 입력으로 사용
- run 전 `archive_event_check` → warnings 리포트

### Phase 3 — 2차 필드 (필요 시)

- pykrx batch로 시총·발행주식수
- 선택: KRX-DELISTING OHLCV 레이어

---

## 14. 용량 · 소요 시간 추산

| 항목 | 추정 |
|------|------|
| 종목 수 (Phase 1) | ~3,947 |
| HTTP 요청 (Phase 1) | ~120만 ~ 180만 |
| 2 worker 분할 | 각 ~60万 ~ 90万 |
| JSON 용량 (merged) | ~1.5 ~ 3 GB |
| Parquet (선택) | ~300 ~ 800 MB |
| 연속 가동 (2 worker) | ~2 ~ 4주 |
| 여유 throttle + 차단 | ~3 ~ 6주 |

---

## 15. 리스크 · 완화

| 리스크 | 완화 |
|--------|------|
| 네이버 429/403 | batch pause, max-tasks/일, failed→재시도 |
| manifest 불일치 | tasks.jsonl 1회 생성 후 공유 |
| chunk 중복 | merge 경고 + 최신 wins |
| 수정주가 미검증 | Phase 0 교차검증 필수 |
| 거래량 raw | `volume_basis` 메타; 전략별 해석은 백테스트 측 |
| 생존편향 | Phase 2 delisted 레이어; event_check로 상장/폐지 구간 표시 |
| 코드 재사용·합병 | listing_events `merged`/`code_change` 기록 |

---

## 16. 진행률 status 출력 예

```
Naver Daily Archive Status (2026-06-12)
Workers: pc + laptop
Tasks: done=42,300  pending=65,100  failed=120
By year:
  2026: 98.2%  |  2025: 95.1%  |  2024: 88.0%  |  ...  |  2000: 12.3%
Merged symbols: 3,820 / 3,947
Listing events: 3,947 listed (delisted layer: not loaded)
```

---

## 17. 결정 사항 체크리스트

- [x] Task 단위: `(symbol, year)`
- [x] 수집 순서: 연도 역순 (2026 → 2000)
- [x] Worker 분할: `int(symbol) % 2`
- [x] 1차: OHLCV + listing_events; 시총 등 2차
- [x] price_basis: adjusted (P0 검증 후)
- [x] volume_basis: raw
- [x] moa history_cache와 경로 분리
- [x] 전략·시총 필터 등 특정 전략 전제 없음
- [x] 새 프로젝트 repo/폴더명: `cursor/00_archive`
- [ ] merge conflict policy (최신 wins) — 구현 시 코드 주석으로 고정
- [ ] Parquet export 시점 (merge 직후 vs 백테스트 직전)

---

## 18. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-12 | 초안 작성 (moa 대화 기반, 전략 중립 버전) |

---

## 부록 A — 프로젝트 위치

- **프로젝트 루트**: `cursor/00_archive`
- moa 원본 사본: `reference/moa/`
- 독립 실행 모듈: `core/` (`naver_daily.py`, `bar_merge.py`, `throttle.py`, `shard.py`)
- 다음 구현: `scripts/archive_plan.py`, `archive_collect.py`, `archive_merge.py`

## 부록 B — moa와 공존 시

- moa `data/history_cache/`: 운영용 ~320봉, 매일 page1 증분
- 아카이브 `data/naver_daily_archive/`: 백테스트용 장기 보관
- **양방향 sync 불필요**; 아카이브 merge 결과를 필요 시 moa로 import하는 일회성 도구만 선택 구현
