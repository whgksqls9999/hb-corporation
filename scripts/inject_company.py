"""SessionStart 훅: HB Corporation 헌법 + 리더 운영 규칙 + 프로젝트 L3(project.md)를
세션 컨텍스트에 주입한다. 카드가 임계치를 넘으면 아우터루프(consolidation) 권고도 함께 주입한다.

- 헌법(company.md/constitution.md): 플러그인 루트에서 읽어 항상 주입.
- L3(<cwd>/.hb/project.md): 헌법만 강제되던 빈틈 보완. 작으면 통째, 크면 목차+강제 Read 지시.
- memory 인덱스(<cwd>/.hb/memory/INDEX.md): 리더가 관련 패턴을 골라 위임하도록 목록 노출. 작으면 통째, 크면 /recall 안내."""
import os
import json
import sys

# Windows 콘솔 기본 인코딩(cp949)이 JSON 출력을 깨뜨리지 않도록 UTF-8 강제
sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8")

CONSOLIDATE_THRESHOLD = 15  # 카드가 이 수를 넘으면 정리 권고
L3_MAX_BYTES_DEFAULT = 24000  # project.md 가 이보다 크면 통째 대신 목차만 주입
INDEX_MAX_BYTES_DEFAULT = 12000  # INDEX.md 가 이보다 크면 통째 대신 /recall 안내만


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


def _project_l3(cwd: str) -> str:
    """L3(project.md) 주입 블록. 작으면 통째, 크면 목차+강제 Read 지시(컨텍스트 폭주 방지)."""
    try:
        with open(os.path.join(cwd, ".hb", "project.md"), encoding="utf-8") as f:
            text = f.read().strip()
    except OSError:
        return ""  # L3 없음 → 주입 안 함
    if not text:
        return ""

    try:
        max_bytes = int(os.environ.get("HB_L3_MAX_BYTES", str(L3_MAX_BYTES_DEFAULT)))
    except ValueError:
        max_bytes = L3_MAX_BYTES_DEFAULT

    header = "\n\n---\n\n# L3 전략층 — 이 워크스페이스 하드 제약 (`.hb/project.md`)\n\n"
    size = len(text.encode("utf-8"))

    if size <= max_bytes:
        return (
            header + text +
            "\n\n[강제] 위 L3 는 이 프로젝트의 하드 제약이다. 트리아지·위임 시 "
            "건드리는 레포/주제의 섹션을 반드시 반영하고, 부서 스폰 task 에 실어 보내라."
        )

    # 대형 파일: 통째 주입 대신 목차(헤더 라인)만 + 강제 Read 지시
    toc = "\n".join(ln for ln in text.splitlines() if ln.lstrip().startswith("#"))
    return (
        header +
        f"[주의] L3 파일이 큼({size}B > {max_bytes}B) → 전체 대신 목차만 주입한다.\n\n"
        + toc +
        "\n\n[강제] 트리아지에서 건드리는 레포/주제에 해당하는 섹션을 `.hb/project.md` 에서 "
        "Read 로 직접 읽어 반영하라. 목차에 있는 제약을 '못 봤다'는 변명은 없다."
    )


def _memory_index(cwd: str) -> str:
    """memory 카드 인덱스(INDEX.md) 주입. 리더가 지금 작업과 관련된 패턴을 골라
    부서 task 에 실을 수 있도록 목록을 노출한다. 작으면 통째, 크면 /recall 안내만(컨텍스트 폭주 방지)."""
    try:
        with open(os.path.join(cwd, ".hb", "memory", "INDEX.md"), encoding="utf-8") as f:
            text = f.read().strip()
    except OSError:
        return ""  # 인덱스 없음 → 주입 안 함
    if not text:
        return ""

    try:
        max_bytes = int(os.environ.get("HB_INDEX_MAX_BYTES", str(INDEX_MAX_BYTES_DEFAULT)))
    except ValueError:
        max_bytes = INDEX_MAX_BYTES_DEFAULT

    header = "\n\n---\n\n# memory 카드 인덱스 (`.hb/memory/INDEX.md`)\n\n"
    size = len(text.encode("utf-8"))

    if size <= max_bytes:
        return (
            header + text +
            "\n\n[활용] 위는 이 프로젝트에 축적된 패턴/안티패턴 목록이다. 지금 작업과 관련된 것만 "
            "골라 부서 스폰 task 에 실어라(전부 아님). 상세는 해당 카드 파일을 Read 하거나 `/recall`."
        )

    return (
        header +
        f"[주의] 인덱스가 큼({size}B > {max_bytes}B) → 전체 대신 안내만. "
        "지금 작업과 관련된 패턴은 `/recall <주제>` 로 조회하라."
    )


def main() -> None:
    root = _root()
    cwd = _cwd()
    company = _read(root, "company.md")
    constitution = _read(root, "constitution.md")

    context = (
        "# HB Corporation 활성화됨\n\n"
        "이 세션에서 너는 HB Corporation의 리더(leader)이다. "
        "아래 운영 규칙과 헌법을 따른다. (부서를 스폰할 때 헌법을 task에 함께 실어 보낼 것.)\n\n"
        "---\n\n" + company + "\n\n---\n\n" + constitution
    )

    # L3(project.md) 강제 주입 — 헌법만 강제하던 빈틈 보완
    context += _project_l3(cwd)

    # memory 카드 인덱스 주입 — 리더가 관련 패턴을 골라 부서 task 에 실을 수 있도록 목록 노출
    context += _memory_index(cwd)

    cards = _count_cards(cwd)
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
