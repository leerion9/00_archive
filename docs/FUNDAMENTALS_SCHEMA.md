# 재무 sidecar 스키마 (DART 1차) — 2026-07-12

> 합의: OHLCV `merged` 원본 불변. 재무는 **sidecar 2단**. 1차 소스 **OpenDART**.

---

## 0. 인증

| 항목 | 값 |
|------|-----|
| 필요 | `DART_API_KEY` (= OpenDART `crtfc_key`, 40자) |
| 발급 | https://opendart.fss.or.kr → 인증키 신청 |
| 일일 한도 | **40,000건** (하드). 수집기는 soft **35,000**에서 중단 (`master/dart_quota.json`) |
| 비고 | `KRX_ID`/`KRX_PW`는 **시총(pykrx/data.krx)용**. DART와 **별개**. |

```powershell
# .env
DART_API_KEY=발급받은40자키
```

---

## 1. 레이어 A — 이벤트 원본 (희소)

경로: `data/naver_daily_archive/fundamentals_events/{symbol}.parquet`

행 = 공시 1건 (종목 × 사업연도 × 보고서).

| 컬럼 | 타입 | 설명 |
|------|------|------|
| symbol | str | 6자리 |
| corp_code | str | DART 고유번호 8자리 |
| bsns_year | int | 사업연도 |
| reprt_code | str | 11013/11012/11014/11011 |
| reprt_name | str | 1Q/반기/3Q/사업 |
| rcept_no | str | 접수번호 14자리 |
| rcept_dt | str | **as-of 기준일** YYYYMMDD (= rcept_no[:8]) |
| fiscal_end | str | 당기일자(공시 본문, 참고용) |
| fs_div | str | CFS 우선, 없으면 OFS |
| revenue | float\|null | 매출액(원) |
| operating_income | float\|null | 영업이익 |
| net_income | float\|null | 당기순이익 |
| equity | float\|null | 자본총계 |
| assets | float\|null | 자산총계 (선택) |
| liabilities | float\|null | 부채총계 (선택) |
| eps | float\|null | 기본주당이익 (있으면) |
| source | str | `opendart_fnlttSinglAcnt` |
| fetched_at_iso | str | 수집 시각 |

**규칙**
- 연결(CFS) 우선, 동일 접수에 연결 없으면 별도(OFS)
- 백테스트 as-of = **`rcept_dt`** (분기말 `fiscal_end` 사용 금지)

---

## 2. 레이어 B — 일별 사용 컬럼 (features 확장)

경로: 테스트는 `fundamentals_daily_test/{symbol}.parquet`  
전량 적재 시: 기존 `features/{symbol}.parquet`에 조인/컬럼 추가.

| 컬럼 | 설명 |
|------|------|
| date | YYYYMMDD (기존 features index와 동일) |
| fund_asof_date | 해당일까지 알려진 최신 `rcept_dt` |
| fund_reprt_code | 그 공시의 보고서 코드 |
| revenue_asof | forward-fill |
| operating_income_asof | forward-fill |
| net_income_asof | forward-fill |
| equity_asof | forward-fill |
| eps_asof | 공시 EPS 또는 net_income/shares (방법 플래그) |
| bps_asof | equity_asof / shares_outstanding |
| per | close / eps_asof (eps≤0 → null) |
| pbr | close / bps_asof (bps≤0 → null) |
| eps_method | `dart_eps` \| `ni_over_shares` |

`close`·`shares_outstanding`는 기존 merged/features에서 조인.

---

## 3. 테스트 범위 (이번 실행)

| 항목 | 값 |
|------|-----|
| 종목 | 005930 (삼성전자) |
| 연도 | 2023, 2024 |
| 보고서 | 11013, 11012, 11014, 11011 |
| 산출 | `fundamentals_events/005930.parquet` + `fundamentals_daily_test/005930.parquet` |
| 전량 수집 | **하지 않음** |

```powershell
cd c:\cursor\00_archive
python -m scripts.archive_fundamentals_test --symbol 005930 --years 2023 2024
```

---

## 4. API

- 고유번호: `corpCode.xml` zip (`https://opendart.fss.or.kr/api/corpCode.xml`)
- 주요계정: `fnlttSinglAcnt.json`
- (향후) 전체계정·EPS 보강: `fnlttSinglAcntAll.json`
