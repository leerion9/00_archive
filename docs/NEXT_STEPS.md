# 향후 작업 · 리마인더

> **AI/개발자**: 이 파일의 ⏰ 항목은 사용자가 Phase 2를 시작할 때 **반드시 먼저 리마인드**할 것.

---

## ⏰ 상장폐지 종목 (Phase 2) — 순서 엄수

**시세(OHLCV) 수집 전에** 아래를 **먼저** 진행:

1. **연도별 상장폐지 종목 리스트** 추출 (FDR `StockListing('KRX-DELISTING')` + 폐지일 기준 연도별 집계)
2. **연도별 몇 종목인지** 규모 파악 → 사용자에게 보고
3. 사용자 확인 후에만 폐지 종목 **가격 데이터** 수집 착수 (FDR / pykrx / 네이버 fallback)

---

## 종목 chunk 분할 (4등분, 코드순)

| chunk | 코드 범위 | 종목 수 |
|-------|-----------|---------|
| 0 | 000020 ~ 051500 | 1,000 |
| 1 | 051600 ~ 214330 | 1,000 |
| 2 | 214370 ~ 433500 | 1,000 |
| 3 | 433880 ~ 950250 | 947 |

설정: `data/naver_daily_archive/config/chunks.json`

---

## fail / retry 정책

| 단계 | 명령 | 실패 시 상태 |
|------|------|-------------|
| **1회차** | `archive_collect --chunk N` | `failed` → run summary 보고 |
| **2회차** | `archive_collect --chunk N --retry-failed` | 동일 fetch 1회 → 또 실패 시 **`skipped` (최종)** |

```powershell
python -m scripts.archive_collect --worker pc --chunk 0 --max-tasks 0
python -m scripts.archive_collect --worker pc --chunk 0 --retry-failed --max-tasks 0
python -m scripts.reset_stale_cursors   # next_page>=800 커서 복구 (재시도 전 권장)
python -m scripts.repair_overfetched --year 2023 --min-pages 35 --apply
```

fetch 가드: date dedup, stale page stop, **30 page/task 상한** (`ARCHIVE_MAX_PAGES_PER_YEAR_TASK`)

> **주의**: `--retry-failed`는 **`--chunk`와 함께** 사용할 것. chunk 없이 실행하면 pending 전체가 섞일 수 있음.

---

## 완료 (2026-06-17 기준)

### 2026 OHLCV — **완료**
- [x] 2026-01-01 ~ 2026-05-31: **3,945 done**, 2 skipped
- [x] 수정주가 교차검증 10/10 PASS

### 2025 OHLCV — **완료**
- [x] chunk 0·1·2·3 + failed 49종 `--retry-failed` → skipped
- **최종: done 3,898 + skipped 49 = 3,947 (100%)**

### 2024 OHLCV — **완료**
- [x] chunk 0·1·2·3 (6/16, 약 6.5h wall clock)
- **최종: done 3,726 + skipped 221 = 3,947 (100%)**
- skipped: ETF·신규상장·채권 등 Naver 데이터 없음

---

## 진행 중: **2023 OHLCV** (50%)

| chunk | done | skipped | failed | pending | 상태 |
|-------|------|---------|--------|---------|------|
| 0 | 997 | 3 | 0 | 0 | ✅ 완료 (failed 3종 재시도 → skipped) |
| 1 | 974 | 0 | **26** | 0 | ⚠️ 1회차 완료, retry 대기 |
| 2 | 0 | 0 | 0 | 1,000 | ❌ 미착수 |
| 3 | 0 | 0 | 0 | 947 | ❌ 미착수 |

**2023 합계:** done 1,971 + skipped 3 + failed 26 + pending 1,947 = 3,947

chunk 0 skipped 3종: `014950`, `031210`, `036220`  
chunk 1 failed 26종: manifest `tasks.jsonl` status=failed 참고 (2024·2025 skip과 유사 유형 다수)

---

## 다음 우선 (내일): **2023 잔여**

```powershell
cd c:\cursor\00_archive

# 1) chunk 1 failed 26종 재시도 → skip
python -m scripts.archive_collect --worker pc --chunk 1 --retry-failed --max-tasks 0

# 2) chunk 2 수집
python -m scripts.archive_collect --worker pc --chunk 2 --max-tasks 0
# 1회차 끝나면 failed 보고 → --retry-failed

# 3) chunk 3 수집
python -m scripts.archive_collect --worker pc --chunk 3 --max-tasks 0
# 1회차 끝나면 failed 보고 → --retry-failed
```

- page cursor: 2024~2026 수집 후 `manifest/cursors/` 활용 → 2023도 **cursor부터** fetch
- chunk 0·1 각 ~85~88분/chunk (1000종 기준)

---

## 보류 / 이후

- [ ] 2023 chunk 1 retry + chunk 2·3
- [ ] 2022 이하 연도 (역순)
- [ ] 시총 pykrx enrich (Phase 1.5)
- [ ] 상장폐지: 연도별 리스트·건수 먼저 (⏰)

---

## Git

- 원격: [leerion9/00_archive](https://github.com/leerion9/00_archive)
- 브랜치: `master` (`origin/master` 추적)
- 수집 데이터(`raw/`, `manifest/`)는 `.gitignore` — **PC 로컬 유지**

---

## 데이터 경로 (git 제외, PC 로컬 유지)

```
data/naver_daily_archive/raw/pc/{symbol}/{year}.json
data/naver_daily_archive/manifest/tasks.jsonl
data/naver_daily_archive/manifest/cursors/
```

노트북 이어하기 시 manifest + cursors + chunks.json 복사 필요.
