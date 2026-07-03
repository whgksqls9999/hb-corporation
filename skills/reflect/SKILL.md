---
name: reflect
description: 코드 구현·수정·디버깅 작업이 끝난 뒤 이번 작업의 교훈을 추출해 헌법 게이트를 통과시킨 뒤 현재 프로젝트의 .hb/memory에 축적한다. "reflect", "회고", "이번 작업 정리해줘"로도 호출. 단순 잡담·투두 정리·질문에는 트리거하지 않는다.
---
# Reflect — 성장 루프 (GNOSIS inner loop 축소판)

방금 끝난 작업에서 교훈을 뽑아 현재 프로젝트의 `.hb/memory/`에 저장한다.
**교훈이 없으면 저장하지 않는다** (억지로 만들지 말 것). 폴더/INDEX가 없으면 만든다.

## 1. 교훈 추출
이번 작업에서:
- **문제**: 뭘 하려 했나
- **해법/패턴**: 어떻게 풀었나, 패턴 이름
- **버린 대안**: 왜 다른 방식을 안 썼나
- **결과**: 채택됐나 / revert됐나 / qa-manager 판정은?

## 2. 헌법 게이트 (핵심 단계)
주입된 헌법을 기준으로 outcome을 정한다.
outcome은 **재판단하지 말고** qa-manager 판정 + 실제 채택/revert 사실로 결정한다:
- L1 위반 있음 OR revert됨 OR qa-manager REJECT → `.hb/memory/anti-patterns/`에 "이렇게 하지 말 것"으로 저장
- L2 어긋남(qa "개선 여지") → `.hb/memory/patterns/`에 저장하되 note에 개선점 기록
- 위반 없음 + 채택 + PASS → `.hb/memory/patterns/`에 저장
- **성과가 좋아 보여도 L1 위반이면 pattern이 아니라 anti-pattern이다.** (크기 아닌 방향)

## 3. 저장 형식
`.hb/memory/patterns/<짧은-이름>.md` (또는 `.hb/memory/anti-patterns/`):
```
---
name: <패턴 이름>
tags: [관련, 키워드]
outcome: adopted | reverted | rejected
note: <L2 개선 여지 있으면 여기>
---
- 문제:
- 해법:
- 버린 대안:
- 근거/결과: (qa-manager 판정 인용)
```
그리고 `.hb/memory/INDEX.md`(없으면 생성)의 해당 섹션에 한 줄 추가:
`- [이름](patterns/파일.md) — 한 줄 요약 (tags)`

## 4. 안 할 것
- 교훈이 없으면 저장하지 않는다.
- 같은 패턴이 이미 있으면 새로 만들지 말고 기존 파일을 갱신한다.
