# `.hb-rules.mjs` 규약 (Convention Dispatcher Contract)

`agentRulesApi: 1`

hb-corporation 플러그인(v0.6.0+)은 **엔진(mechanism)** 만 담는다. 규칙(policy)은 각
프로젝트가 자기 git 레포에 `.hb-rules.mjs` 로 채운다. 이 문서는 그 둘 사이의 계약이다.

- **디스패처(엔진):** `${CLAUDE_PLUGIN_ROOT}/hooks/conventions-dispatch.mjs`
  플러그인이 `PreToolUse`(matcher `Write|Edit`) 로 등록한다. 규칙은 0개다.
- **규칙 파일(정책):** `<any-dir>/.hb-rules.mjs`
  대상 파일의 디렉터리에서 `CLAUDE_PROJECT_DIR` 까지 walk-up 하며 발견되는 모든
  `.hb-rules.mjs` 를 수집·병합한다.

---

## 1. 디스패처가 하는 일

1. `PreToolUse` 이벤트를 stdin 으로 읽는다 (`Write` / `Edit` 만).
2. 도구 입력으로 **최종 파일 내용**을 재구성한다.
   - `Write` → `content` = 새로 쓸 내용, `previousContent` = 기존 파일(없으면 `null`).
   - `Edit` → `old_string`/`new_string`/`replace_all` 을 현재 파일에 적용한 결과가 `content`,
     적용 전 파일이 `previousContent`.
3. 대상 파일 디렉터리부터 `CLAUDE_PROJECT_DIR` 까지 올라가며 `.hb-rules.mjs` 를 모은다.
4. 각 모듈의 `default` 배열(= `RuleModule[]`)을 돌려 `validate()` 를 호출한다.
5. **위반이 하나라도 있으면 deny**(deny-wins), 아니면 allow.

---

## 2. RuleModule 시그니처

`.hb-rules.mjs` 는 **`RuleModule` 의 배열을 default export** 한다.

```js
// <any-dir>/.hb-rules.mjs
export default [
  {
    // (선택) 이 규칙을 적용할지 빠르게 거른다. 생략하면 항상 적용.
    applies(ctx) {
      return ctx.filePath.endsWith('.test.ts');
    },
    // (필수) 검사. Verdict 또는 Promise<Verdict> 반환.
    validate(ctx) {
      if (!ctx.content.includes('/** @jest-environment')) {
        return { ok: false, reason: '테스트 파일 상단에 @jest-environment JSDoc 필요' };
      }
      return { ok: true };
    },
  },
];
```

### ctx (디스패처 → 규칙)

| 필드 | 타입 | 의미 |
|---|---|---|
| `tool` | `'Write' \| 'Edit'` | 발화한 도구 |
| `filePath` | `string` | 대상 파일 경로(정규화: `/` 구분자) |
| `content` | `string` | 도구 적용 **후** 최종 파일 내용 |
| `previousContent` | `string \| null` | 적용 **전** 내용(신규 파일이면 `null`) |

### Verdict (규칙 → 디스패처)

| 형태 | 의미 |
|---|---|
| `{ ok: true }` | 통과 |
| `{ ok: false, reason: string }` | **위반** — `reason` 이 사용자에게 deny 사유로 반환됨 |

---

## 3. 불변 규칙

- **deny-wins** — walk-up 으로 모인 모든 모듈·모든 규칙 중 **하나라도** `ok:false` 면 차단.
  모든 위반 `reason` 을 합쳐 반환한다.
- **fail-open** — 디스패처 자체 오류, 모듈 import 실패, 규칙 `validate()` 내부 예외는
  **그 층만 건너뛰고 allow**. 확정된 위반만 막는다. (강제가 에이전트를 망가뜨리지 않도록.)
- **walk-up 경계** — `dirname(filePath)` 부터 `CLAUDE_PROJECT_DIR` 까지. 세션이 워크스페이스
  루트에서 스폰될 때 그 루트가 경계다.
- **규칙 0개 원칙** — 플러그인은 규칙을 넣지 않는다. 규칙 없는 레포에선 walk-up 결과가 0 →
  즉시 allow(무해). 규칙은 각 레포가 opt-in.

---

## 4. 작성 시 주의

- `.hb-rules.mjs` 는 ESM(`export default`). Node 로 import 되므로 `node --check` 로 구문 확인 권장.
- 블록주석에 `*/` 리터럴을 넣지 말 것(엔진 파일과 동일 이유: SyntaxError → fail-open 위장).
- `validate()` 는 순수 검사에 집중한다. 파일 쓰기·네트워크 등 부작용 금지.
- 디스패처 matcher 는 `Write|Edit` 라 셸 우회(`echo > x`)는 걸리지 않는다(알려진 갭).
