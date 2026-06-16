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

## fail / retry 정책 (2024부터 적용)

| 단계 | 명령 | 실패 시 상태 |
|------|------|-------------|
| **1회차** | `archive_collect` (chunk별) | `failed` → run summary 보고 |
| **2회차** | `archive_collect --retry-failed` | 동일 fetch 1회 → 또 실패 시 **`skipped` (최종)** |

```powershell
python -m scripts.archive_collect --worker pc --chunk 0 --max-tasks 0
python -m scripts.archive_collect --retry-failed --max-tasks 0   # failed → skipped
python -m scripts.reset_stale_cursors   # next_page>=800 커서 복구 (재시도 전 권장)
python -m scripts.repair_overfetched --year 2024 --min-pages 35 --apply
```

fetch 가드: date dedup, stale page stop, **30 page/task 상한** (`ARCHIVE_MAX_PAGES_PER_YEAR_TASK`)

---

## 완료 (2026-06-16 기준)

### 2026 OHLCV
- [x] 2026-01-01 ~ 2026-05-31: **3,945 done**, 2 skipped (6월 신규상장)
- [x] 수정주가 교차검증 10/10 PASS

### 2025 OHLCV — **완료**
- [x] chunk 0·1·2·3 전체 pending 수집 완료
- [x] 과다 page(789) repair + fetch 로직 수정 (dedup / stale stop / 30p cap)
- [x] failed 49종 `--retry-failed` → **skipped 49** (복구 0, 2026 상반기 상장·채권/ETF)

**2025 최종: done 3,898 + skipped 49 = 3,947 (100%)**

skipped 49종 (2026 신규상장·데이터 없음):  
`520102`, `580088` 등 — manifest `tasks.jsonl` status=skipped 참고

---

## 다음 우선: **2024 OHLCV**

```powershell
cd c:\cursor\00_archive
python -m scripts.archive_plan --years 2024 --append
python -m scripts.archive_collect --worker pc --chunk 0 --max-tasks 150   # chunk/day 권장
# chunk 0→3 순, 1회차 끝나면 failed 보고 → --retry-failed
```

- page cursor: 2025·2026 수집 후 `manifest/cursors/`에 next_page 저장됨 → 2024는 **cursor부터** fetch
- chunk당 ~1000종, `--max-tasks 150` 또는 chunk/day 운영

---

## 보류 / 이후

- [ ] 2024 수집 (역순, cursor 활용)
- [ ] 2023 이하 연도
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
