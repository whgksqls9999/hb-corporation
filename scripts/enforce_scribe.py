"""Stop 훅: 리더가 응답을 끝내려 할 때(=완료 판단), 미청산 팀 작업 기록이 있으면 종료를 차단한다.
scribe-manager가 기록을 마치고 장부를 비우면 통과한다."""
import json
import os
import sys

# Windows 콘솔 기본 인코딩(cp949)이 JSON 출력을 깨뜨리지 않도록 UTF-8 강제
sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    cwd = data.get("cwd") or os.getcwd()
    pending = os.path.join(cwd, ".hb", "scratch", "pending.jsonl")

    try:
        with open(pending, encoding="utf-8") as f:
            entries = [line for line in f if line.strip()]
    except OSError:
        return  # 장부 없음 = 팀 작업 없었음 → 통과

    if not entries:
        return  # 장부 비어 있음 = 이미 청산됨 → 통과

    agents = ", ".join(sorted({(json.loads(e).get("agent") or "?") for e in entries}))
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"[HB Corporation] 이번 세션의 팀 작업 기록이 아직 남지 않았다 (미청산 {len(entries)}건: {agents}). "
            "scribe-manager를 스폰해 .hb/scratch/pending.jsonl의 부서 보고를 종합·기록하게 한 뒤 종료하라. "
            "scribe-manager가 기록을 마치면 장부를 비워 이 차단이 해제된다."
        ),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
