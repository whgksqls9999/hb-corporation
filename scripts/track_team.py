"""PostToolUse 훅: 부서(서브에이전트) 작업이 끝날 때마다 보고를 장부에 임시저장한다.
(매드캣 gnosis_save_reflection 등가 — LLM 개입 없이 기계적으로 저장, 유실 방지)"""
import json
import os
import sys

# Windows 콘솔 기본 인코딩(cp949) 문제 방지
sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")

DEPARTMENTS = ("strategy-director", "dev-manager", "qa-manager")
MAX_LEN = 2000  # 보고 저장 상한 (토큰 억제)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input") or {}
    agent = str(tool_input.get("subagent_type") or tool_input.get("agent_type") or "")
    if not any(d in agent for d in DEPARTMENTS):
        return  # 부서 스폰만 기록 (scribe-manager, 기타 서브에이전트는 무시)

    output = data.get("tool_output") or data.get("tool_response") or ""
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False)
    prompt = str(tool_input.get("prompt") or "")

    entry = {
        "agent": agent,
        "task": prompt[:300],
        "report": output[:MAX_LEN],
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

    with open(os.path.join(scratch, "pending.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
