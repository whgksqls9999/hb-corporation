"""SessionStart 훅: HB Corporation 헌법 + 리더 운영 규칙을 세션 컨텍스트에 주입한다.
카드가 임계치를 넘으면 아우터루프(consolidation) 권고도 함께 주입한다."""
import os
import json
import sys

# Windows 콘솔 기본 인코딩(cp949)이 JSON 출력을 깨뜨리지 않도록 UTF-8 강제
sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")

CONSOLIDATE_THRESHOLD = 15  # 카드가 이 수를 넘으면 정리 권고


def _root() -> str:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return env
    # 플러그인 루트 = 이 스크립트의 상위 폴더
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(root: str, name: str) -> str:
    try:
        with open(os.path.join(root, name), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _cwd() -> str:
    try:
        data = json.load(sys.stdin)
        return data.get("cwd") or os.getcwd()
    except Exception:
        return os.getcwd()


def _count_cards(cwd: str) -> int:
    total = 0
    for sub in ("patterns", "anti-patterns"):
        d = os.path.join(cwd, ".hb", "memory", sub)
        try:
            total += len([f for f in os.listdir(d) if f.endswith(".md")])
        except OSError:
            pass
    return total


def main() -> None:
    root = _root()
    company = _read(root, "company.md")
    constitution = _read(root, "constitution.md")

    context = (
        "# HB Corporation 활성화됨\n\n"
        "이 세션에서 너는 HB Corporation의 리더(leader)이다. "
        "아래 운영 규칙과 헌법을 따른다. (부서를 스폰할 때 헌법을 task에 함께 실어 보낼 것.)\n\n"
        "---\n\n" + company + "\n\n---\n\n" + constitution
    )

    cards = _count_cards(_cwd())
    if cards > CONSOLIDATE_THRESHOLD:
        context += (
            f"\n\n---\n\n[아우터루프 권고] 이 프로젝트의 memory 카드가 {cards}장이다 "
            f"(임계 {CONSOLIDATE_THRESHOLD}장 초과). 적절한 시점에 사용자에게 `/consolidate` 실행을 제안하라. "
            "정리 없이 카드가 계속 쌓이면 중복·노후 카드가 recall 품질을 떨어뜨린다."
        )

    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
