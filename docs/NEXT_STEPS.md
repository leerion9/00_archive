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

설정: `config/chunks.json`  
실행:

```powershell
python -m scripts.archive_collect --worker pc --chunk 3 --max-tasks 0
python -m scripts.archive_collect --retry-failed   # failed만 명시적 재시도
python -m scripts.repair_overfetched --year 2025 --min-pages 35 --apply
python -m scripts.reset_stale_cursors
```

fetch 가드: date dedup, stale page stop, **30 page/task 상한** (`ARCHIVE_MAX_PAGES_PER_YEAR_TASK`)

---

## 완료 (2026-06-15 기준)

### 2026 OHLCV
- [x] 2026-01-01 ~ 2026-05-31: **3,945 done**, 2 skipped (6월 신규상장)
- [x] 수정주가 교차검증 10/10 PASS

### 2025 OHLCV (진행 중)
- [x] chunk 0·1·2 대부분 완료
- [x] 과다 page(789) 97종 repair + fetch 로직 수정 후 **85종 재수집**
- [ ] **chunk 3 pending ~328종** ← **내일 우선**
- [ ] failed 14종 (Naver 데이터 없음 → skip 검토)

**2025 전체: done 3,593 / 3,947 (91%)**

---

## 보류 / 다음에

- [ ] chunk 3 수집 완료
- [ ] 시총 pykrx enrich (Phase 1.5)
- [ ] 상장폐지: 연도별 리스트·건수 먼저 (⏰)
- [ ] 2024 이하 연도 (역순, cursor 활용)

---

## Git (2026-06-15)

- 로컬 커밋: `491698a` (master)
- **원격 미설정** — push는 GitHub repo URL 추가 후:
  ```powershell
  git remote add origin https://github.com/<user>/00_archive.git
  git push -u origin master
  ```
- 수집 데이터(`raw/`, `manifest/`)는 `.gitignore` — PC 로컬 유지

---

## 데이터 경로 (git 제외, PC 로컬 유지)

```
data/naver_daily_archive/raw/pc/{symbol}/{year}.json
data/naver_daily_archive/manifest/tasks.jsonl
data/naver_daily_archive/manifest/cursors/
```

노트북 이어하기 시 manifest + cursors + chunks.json 복사 필요.
