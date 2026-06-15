# moa 프로젝트에서 가져온 참고 소스

원본 repo: `c:\cursor\03_moa`

`reference/moa/` 아래는 **moa 원본 그대로** 사본입니다.  
00_archive `core/` 모듈은 moa **의존 없이** 동작하도록 재구성했습니다.

## 복사된 파일

| moa 경로 | 00_archive 경로 | 용도 |
|----------|-----------------|------|
| `docs/naver_daily_archive/DESIGN.md` | `docs/DESIGN.md` | 설계 문서 |
| `docs/naver_daily_archive/README.md` | `docs/README.md` | 문서 안내 |
| `core/naver_universe.py` | `reference/moa/core/naver_universe.py` | sise_day 파싱·fetch |
| `core/history_cache.py` | `reference/moa/core/history_cache.py` | merge_bars, throttle, 캐시 |
| `core/naver_symbol_master.py` | `reference/moa/core/naver_symbol_master.py` | 종목 마스터 |
| `tests/test_history_cache.py` | `reference/moa/tests/test_history_cache.py` | merge 테스트 |
| `scripts/update_symbol_master.py` | `reference/moa/scripts/update_symbol_master.py` | moa용 (settings 의존) |

## 00_archive에서 재구현한 모듈

| 파일 | moa 대응 | 변경점 |
|------|----------|--------|
| `core/naver_daily.py` | `naver_universe` 일봉 부분 | `SymbolHistory` 제거, YYYYMMDD 정규화 |
| `core/bar_merge.py` | `history_cache.merge_bars` | `MAX_STORED_BARS` 제한 없음 |
| `core/throttle.py` | `HistoryCacheStore` throttle | 독립 클래스 |
| `core/naver_symbol_master.py` | 동명 | logger 이름만 `archive` |
| `core/shard.py` | (신규) | worker 분할 |
| `scripts/update_symbol_master.py` | moa script | settings 없이 `.env` |

## moa에 남겨 둔 것 (복사 안 함)

- `core/api_client.py` (KIS) — 아카이브와 무관
- `data/history_cache/` — 운영 캐시, 별도 경로
- gap_backfill / gap_collector — 분봉·갭 전략 전용

## 동기화

moa 쪽 `naver_universe` / `merge_bars`를 수정했을 때,  
필요하면 `reference/moa/`를 수동 갱신하고 `core/` 반영 여부를 검토.
