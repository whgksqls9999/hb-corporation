"""SubagentStop 훅: 부서(서브에이전트) 작업이 끝날 때마다 최종 보고를 장부에 임시저장한다.
(LLM 개입 없이 기계적으로 저장, 유실 방지)

이 하네스는 Agent 스폰을 async 로 띄워 PostToolUse 가 '런치 ack'(prompt 되돌이)만 보므로,
완료 시점에 뜨는 SubagentStop 을 쓴다. 보고 텍스트는 페이로드 last_assistant_message 에 직접 온다
(트랜스크립트 파싱 불필요 — 2026-07-07 실측 확인)."""
import json
import os
import sys
import time

# Windows 콘솔 기본 인코딩(cp949) 문제 방지
sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")

DEPARTMENTS = ("strategy-director", "dev-manager", "qa-manager")
MAX_LEN = 4000  # 보고 저장 상한 (토큰 억제)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    # SubagentStop 페이로드: agent_type 로 부서만 골라낸다
    # (예: "hb-corporation:dev-manager" 또는 "dev-manager" — substring 매칭으로 둘 다 커버)
    agent = str(data.get("agent_type") or "")
    if not any(d in agent for d in DEPARTMENTS):
        return  # 부서 서브에이전트만 기록 (scribe-manager·기타 서브에이전트는 무시)

    report = data.get("last_assistant_message") or ""
    if not isinstance(report, str):
        report = json.dumps(report, ensure_ascii=False)

    entry = {
        "agent": agent,
        "agent_id": data.get("agent_id"),
        "report": report[:MAX_LEN],
    }

    cwd = data.get("cwd") or os.getcwd()
    hb = os.path.join(cwd, ".hb")
    scratch = os.path.join(hb, "scratch")
    os.makedirs(scratch, exist_ok=True)

    # 멀티 PC 동기화: memory는 커밋되고 scratch(임시 장부)만 git에서 제외되도록
    gitignore = os.path.join(hb, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write("scratch/\n")

    # 원자적 append: 기존 내용 전체를 읽어 새 라인을 붙인 뒤 임시파일에 쓰고 os.replace.
    # (단일 append 쓰기가 중단되면 파일이 truncate 되는 사고를 차단. 동시성 lost-update는 범위 밖.)
    pending = os.path.join(scratch, "pending.jsonl")
    try:
        with open(pending, encoding="utf-8") as f:
            existing = f.read()
    except OSError:
        existing = ""

    new_line = json.dumps(entry, ensure_ascii=False) + "\n"
    tmp = os.path.join(scratch, "pending.jsonl.tmp.%d_%d" % (os.getpid(), time.time_ns()))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(existing + new_line)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pending)


if __name__ == "__main__":
    main()
