"""manifest 실측 → docs/STEP_C_HANDOFF.md 갱신."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.report_step_c_status import analyze

WORK_NATURE = {
    0: "재적재 (test)",
    1: "재적재",
    2: "재적재",
    3: "재적재",
    4: "재적재",
    5: "재적재",
    6: "최초 적재",
    7: "최초 적재",
    8: "최초 적재",
}

TIMELINE = """
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
""".strip()

# partial retry 완료일 (chunk 전체 재실행 불필요)
_PARTIAL_RETRY_DONE = frozenset({1, 2, 3, 4, 5})
_CHUNK6_FULL_RUN_DONE = True


def _fmt_missing(missing: list[dict]) -> str:
    parts = []
    for m in missing:
        y = m["year"]
        st = m.get("status", "")
        meth = m.get("method") or "-"
        parts.append(f"{y}({st}/{meth})")
    return ", ".join(parts)


def _next_action(cid: int, s: dict) -> str:
    nature = WORK_NATURE[cid]
    ok, partial, none = s["complete_7yr"], s["partial"], s["none"]
    n = s["symbol_count"]
    if cid == 0:
        return "**완료 — 스킵**"
    if nature == "재적재":
        if partial == 0 and none == 0:
            return "**완료 — 스킵**"
        if cid in _PARTIAL_RETRY_DONE:
            note = f"partial {partial}"
            if none:
                note += f" + none {none}"
            return f"**partial retry 완료(6/27)** — {note} known failure → STEP_C_RUN_LOG.md"
        if partial <= 3 and none == 0:
            return (
                f"partial {partial}종 — **chunk 전체 재실행 불필요**. "
                f"`--symbols` 로 retry"
            )
        return f"partial {partial}종 + none {none} — `--symbols` partial retry 또는 chunk 재실행"
    # 최초 적재
    if cid == 6 and _CHUNK6_FULL_RUN_DONE:
        return f"**1회 전체 실행 완료(6/27)** — 7yr {ok}/{n} → **chunk 7**"
    if cid == 7:
        return f"**최초 적재** — chunk 7 **1회 전체 실행** (~90분+, KRX 세션 주의)"
    if cid == 8:
        return f"**최초 적재** — chunk 8 **1회 전체 실행** (6/26 중단, {ok}/{n} 7yr 완료)"


def render(stats: dict[int, dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_ok = sum(s["complete_7yr"] for s in stats.values())
    total_partial = sum(s["partial"] for s in stats.values())
    total_none = sum(s["none"] for s in stats.values())

    lines = [
        "# Step C — 시총 enrich handoff (chunk별 상세)",
        "",
        "> **AI/개발자**: Step C 작업 시 **이 파일을 chunk 번호별로** 읽을 것. "
        "chunk 1~5를 「재적재 잔여」로 **묶어서 요약하지 말 것**. "
        "실측 갱신: `python -m scripts.report_step_c_status` 후 `python -m scripts.update_step_c_handoff`.",
        "",
        f"**마지막 실측**: {now} (manifest `enrich_tasks.jsonl` 최신 줄 기준)",
        "",
        "**완료 기준**: 종목당 2020~2026 **7연도** 모두 `status=done` + `method` ∈ {`pykrx_mcap`, `etf_aum`}.",
        "",
        f"**전체 합계**: {total_ok} / 3,945종 7연도 완료 · partial {total_partial} · none {total_none}",
        "",
        "머신 리더블 스냅샷: `data/naver_daily_archive/reports/step_c_status_snapshot.json`",
        "",
        "**실행·partial retry 상세 로그**: [STEP_C_RUN_LOG.md](./STEP_C_RUN_LOG.md)",
        "",
        "---",
        "",
        "## 작업 경과 타임라인",
        "",
        TIMELINE,
        "",
        "---",
        "",
        "## chunk 요약표 (한눈에)",
        "",
        "| chunk | 코드 범위 | 성격 | 7yr 완료 | partial | none | fail_log | 다음 액션 |",
        "|-------|-----------|------|----------|---------|------|----------|-----------|",
    ]

    for cid in sorted(stats):
        s = stats[cid]
        lines.append(
            f"| **{cid}** | {s['from_symbol']}~{s['to_symbol']} | {WORK_NATURE[cid]} "
            f"| **{s['complete_7yr']}/{s['symbol_count']}** | {s['partial']} | {s['none']} "
            f"| {s['failure_log_unique_tasks']} | {_next_action(cid, s)} |"
        )

    lines.extend(["", "---", ""])

    for cid in sorted(stats):
        s = stats[cid]
        lines.extend([
            f"## Chunk {cid} — {WORK_NATURE[cid]}",
            "",
            f"- **범위**: `{s['from_symbol']}` ~ `{s['to_symbol']}` ({s['symbol_count']}종)",
            f"- **7연도 완료**: {s['complete_7yr']} · **partial**: {s['partial']} · **none**: {s['none']}",
            f"- **failure log** (고유 task): {s['failure_log_unique_tasks']}",
            f"- **다음 액션**: {_next_action(cid, s)}",
            "",
        ])

        if s["reports"]:
            lines.append("### 실행 이력 (reports)")
            lines.append("")
            lines.append("| 파일 | 시각 (UTC) | done | failed | methods |")
            lines.append("|------|------------|------|--------|---------|")
            for rep in s["reports"]:
                methods = ", ".join(f"{k}:{v}" for k, v in (rep.get("methods") or {}).items())
                lines.append(
                    f"| `{rep['file']}` | {rep.get('at_iso', '')} | {rep.get('done')} "
                    f"| {rep.get('failed')} | {methods} |"
                )
            lines.append("")

        if s.get("legacy_method_tasks_remaining"):
            lines.append(f"- **구방식 method 잔여 task**: {s['legacy_method_tasks_remaining']}")
            lines.append("")

        if s["partial_symbols"]:
            lines.append(f"### partial 종목 ({len(s['partial_symbols'])}개)")
            lines.append("")
            lines.append("| 종목 | 완료 연도 | 미완 연도·상태 |")
            lines.append("|------|-----------|----------------|")
            for ps in s["partial_symbols"]:
                lines.append(
                    f"| `{ps['symbol']}` | {ps['done_years']}/7 | {_fmt_missing(ps['missing'])} |"
                )
            lines.append("")

        if s["none_symbols"]:
            lines.append(f"### none 종목 ({len(s['none_symbols'])}개 — 7연도 중 유효 완료 0)")
            lines.append("")
            syms = ", ".join(f"`{x}`" for x in s["none_symbols"])
            lines.append(syms)
            lines.append("")

        lines.extend(["---", ""])

    lines.extend([
        "## 금지·운영",
        "",
        "- `archive_enrich_market_cap --chunk N` 은 **해당 chunk 전 종목 × 7연도 전부 API 호출** (완료분 skip 없음).",
        "- **chunk 1~8 일괄 for-loop 금지** — 사용자가 지정한 chunk만.",
        "- **한 세션 1~3 chunk** 권장.",
        "- KRX 세션 **~1시간** — chunk >1h 시 후반 failed 多.",
        "",
        "## 새 채팅 예시",
        "",
        "> `docs/STEP_C_HANDOFF.md` chunk **1** partial 2종만 점검해줘. chunk 일괄 실행 금지.",
        "",
        "> `docs/STEP_C_HANDOFF.md` 읽고 Step C **chunk 6 최초 적재만** 터미널 실행해줘.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    base = Path(__file__).resolve().parents[1] / "data" / "naver_daily_archive"
    payload = analyze(base)
    stats = {int(k): v for k, v in payload.get("chunks", {}).items()}
    out = Path(__file__).resolve().parents[1] / "docs" / "STEP_C_HANDOFF.md"
    out.write_text(render(stats), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
