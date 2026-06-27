# 00_archive — Naver Daily Archive

한국 주식 **일봉 OHLCV** 장기 아카이브 (네이버 `sise_day` 크롤링).

- **moa** (`cursor/03_moa`) 자동매매와 **별개** 프로젝트
- 특정 매매 전략·시총 필터를 전제하지 않음
- PC / 노트북 2 worker 병렬 수집 → merge

## 문서

| 경로 | 내용 |
|------|------|
| [docs/DESIGN.md](docs/DESIGN.md) | 전체 설계 (스키마, shard, merge, 이벤트, 운영) |
| [docs/COLLECTION_PLAN.md](docs/COLLECTION_PLAN.md) | **수집·보강 계획** (Step A~F, sidecar) |
| [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) | 향후 작업 · 리마인더 (폐지 종목 ⏰) |
| [docs/STEP_C_HANDOFF.md](docs/STEP_C_HANDOFF.md) | **Step C chunk별** 진행·partial 목록·실행 이력 |
| [docs/STEP_C_RUN_LOG.md](docs/STEP_C_RUN_LOG.md) | Step C **실행·partial retry** 로그 (누락 사유) |
| [docs/STEP_D_HANDOFF.md](docs/STEP_D_HANDOFF.md) | **Step D** 검증 결과 · known failure · Step F/G 연계 |
| [docs/STEP_F_HANDOFF.md](docs/STEP_F_HANDOFF.md) | **Step F** 시장구분 enrich · chunk 적재 가이드 |
| [reference/moa/](reference/moa/) | moa 원본 파일 사본 (참고용) |

## 빠른 시작

```powershell
cd c:\cursor\00_archive
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# .env 에 ARCHIVE_WORKER_ID=pc 또는 laptop 설정

python -m scripts.update_symbol_master
pytest
```

## 개발 순서 (DESIGN.md 기준)

1. **Phase 0** — `archive_plan`, 10종 수정주가 교차검증 ✅
2. **Phase 1** — `archive_collect` OHLCV (2020~2026 ✅, 2019~ 역순 예정)
3. **Phase 1b~1.5** — merge → sidecar enrich (거래대금·MA5·시총) — [COLLECTION_PLAN.md](docs/COLLECTION_PLAN.md)
4. **Phase 2** — listing_events, 상장폐지 OHLCV (⏰ enrich 후)
5. **Phase 3** — 백테스트 연동·추가 필드

## 디렉터리

```
core/           # 독립 실행 모듈 (moa 의존 없음)
scripts/        # CLI (구현 예정)
reference/moa/  # moa 원본 사본
docs/           # 설계 문서
data/           # 수집 데이터 (git 제외)
config/         # worker 설정 예시
```

## moa와의 관계

| moa | 00_archive |
|-----|------------|
| `data/history_cache/` (~320봉, 매일 증분) | `data/naver_daily_archive/` (장기 보관) |
| 운영·유니버스 빌드 | 백테스트 공용 데이터 |

재사용 로직은 `core/`에 moa 의존 없이 정리해 두었고, 원본은 `reference/moa/`에 보관.
