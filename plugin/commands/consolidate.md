---
description: 아우터루프 — 쌓인 memory 카드를 정리한다 (중복 병합·모순 해소·노후 카드 아카이브). scribe-manager를 정리 모드로 스폰한다.
---
Agent 도구로 `scribe-manager`를 스폰하되, task에 **"consolidation 정리 모드"**임을 명시한다.
task에 함께 실어 보낼 것:
- 헌법 요지 (특히 "망각은 삭제가 아니라 archive/ 이동" 원칙)
- 사용자가 준 추가 지시(`$ARGUMENTS`)가 있으면 그대로

서기의 보고(병합/아카이브/잔여 카드 수)를 사용자에게 전달한다.
