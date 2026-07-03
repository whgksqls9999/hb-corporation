# HB Corporation 🏢

클로드 코드 위에 올린 **멀티에이전트 회사 + 자가성장 코딩 어시스턴트** 플러그인

- Naver Mad Cat 구조에 영감

## 무엇을 하나

- **회사처럼 위임** — 리더(leader)가 요청을 simple/team으로 분류하고, 복잡하면 부서에 위임.
- **쓸수록 똑똑해짐** — 작업이 끝나면 교훈을 프로젝트의 `.hb/memory/`에 축적, 다음 작업에 재사용.
- **헌법 게이트** — 성과가 좋아 보여도 넘으면 안 되는 선(헌법)을 넘는 지식은 거부. 잘못된 방향으로 성장하는 것을 막음.

## 구조 (플러그인)

| 경로                                              | 역할                                                                       |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| `.claude-plugin/plugin.json` · `marketplace.json` | 플러그인/마켓플레이스 매니페스트                                           |
| `hooks/hooks.json`                                | SessionStart 훅 등록 (plugin.json이 가리킴)                                |
| `scripts/inject_company.py`                       | 세션 시작 시 규칙을 컨텍스트에 주입                                        |
| `constitution.md`                                 | 헌법 3층 (L1 절대 / L2 원칙 / L3 전략)                                     |
| `company.md`                                      | 리더 운영 규칙 (훅이 주입)                                                 |
| `agents/`                                         | 부서: `strategy-director`(설계) · `dev-manager`(구현) · `qa-manager`(검증) |
| `skills/reflect/`                                 | 성장 루프: 반성 → 헌법 게이트 → 저장                                       |
| `commands/recall.md`                              | 축적 지식 조회                                                             |

**메모리는 플러그인에 없다.** 각 프로젝트의 `.hb/memory/`에 쌓인다 (씨앗은 배포, 나무는 프로젝트마다).

## 설치

```
# 이 레포를 마켓플레이스로 등록
/plugin marketplace add <이 레포의 git URL 또는 로컬 경로>
# 설치
/plugin install hb-corporation@hb-corporation
```

설치 후 아무 프로젝트에서 세션을 열면 리더가 자동 활성화된다.

## 흐름

```
요청 → 리더가 simple/team 판정
  simple → 리더가 직접 처리
  team   → strategy-director(설계) → dev-manager(구현) → qa-manager(검증)
           REJECT면 1회 재작업(Reflexion) → 또 실패면 사용자에게(HITL)
작업 후 → 리더가 자동 reflect → 헌법 게이트 → .hb/memory/에 patterns / anti-patterns 축적
다음에 → /recall <주제> → 관련 지식 소환
```

## 로드맵

- [x] **1단계** — 헌법 3층 + 부서 3개 + reflect 성장 루프
- [x] **2단계(일부)+5단계** — 플러그인 패키징 (설치 가능, 전 라이프사이클 검증 완료)
- [x] **3단계(일부)** — Team 작업 후 자동 reflect
- [ ] **3단계(나머지)** — 세션 종료 개선 루프 (훅)
- [ ] **4단계** — 멀티 PC git 동기화
- [ ] 부서 확장 (frontend 등 필요할 때만)
