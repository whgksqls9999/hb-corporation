// Dev-only test harness for the convention dispatcher.
// NOT part of the shipped plugin: lives at repo root, outside plugin/ (source),
// so marketplace install (source: "./plugin") never copies it.
//
// Run: node --test   (or: npm test)
//
// Spawns hooks/conventions-dispatch.mjs with a fake PreToolUse event on stdin
// and asserts allow (empty stdout) vs deny (JSON with permissionDecision:deny).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DISPATCHER = path.join(HERE, '..', 'plugin', 'hooks', 'conventions-dispatch.mjs');

// Spawn the dispatcher, pipe `event` as JSON on stdin, return {stdout, code}.
function run(event, projectDir) {
	const res = spawnSync(process.execPath, [DISPATCHER], {
		input: JSON.stringify(event),
		encoding: 'utf8',
		env: { ...process.env, CLAUDE_PROJECT_DIR: projectDir ?? '' },
	});
	return { stdout: res.stdout || '', code: res.status };
}

function isAllow(r) {
	return r.code === 0 && r.stdout.trim() === '';
}

function denyReason(r) {
	if (r.stdout.trim() === '') return null;
	const parsed = JSON.parse(r.stdout);
	const out = parsed.hookSpecificOutput;
	if (out && out.permissionDecision === 'deny') return out.permissionDecisionReason;
	return null;
}

// Fresh temp project dir per test; caller writes fixtures inside.
function mkProject() {
	return fs.mkdtempSync(path.join(os.tmpdir(), 'hbrules-'));
}

const DENY_RULE = `export default [
	{ validate: () => ({ ok: false, reason: 'BLOCKED_BY_TEST' }) },
];
`;

test('규칙 없는 트리 → allow', () => {
	const proj = mkProject();
	const r = run(
		{ tool_name: 'Write', tool_input: { file_path: path.join(proj, 'a.ts'), content: 'x' } },
		proj
	);
	assert.ok(isAllow(r), `expected allow, got: ${r.stdout}`);
});

test('deny 규칙 → 차단 + 사유 반환', () => {
	const proj = mkProject();
	fs.writeFileSync(path.join(proj, '.hb-rules.mjs'), DENY_RULE);
	const r = run(
		{ tool_name: 'Write', tool_input: { file_path: path.join(proj, 'a.ts'), content: 'x' } },
		proj
	);
	assert.equal(denyReason(r), 'BLOCKED_BY_TEST');
});

test('walk-up: 상위 디렉터리 규칙이 하위 파일에 적용', () => {
	const proj = mkProject();
	fs.writeFileSync(path.join(proj, '.hb-rules.mjs'), DENY_RULE);
	const sub = path.join(proj, 'src', 'deep');
	fs.mkdirSync(sub, { recursive: true });
	const r = run(
		{ tool_name: 'Write', tool_input: { file_path: path.join(sub, 'a.ts'), content: 'x' } },
		proj
	);
	assert.equal(denyReason(r), 'BLOCKED_BY_TEST');
});

test('applies() 로 대상 아니면 skip → allow', () => {
	const proj = mkProject();
	fs.writeFileSync(
		path.join(proj, '.hb-rules.mjs'),
		`export default [
			{ applies: (ctx) => ctx.filePath.endsWith('.test.ts'),
			  validate: () => ({ ok: false, reason: 'ONLY_TESTS' }) },
		];`
	);
	const r = run(
		{ tool_name: 'Write', tool_input: { file_path: path.join(proj, 'a.ts'), content: 'x' } },
		proj
	);
	assert.ok(isAllow(r), `expected allow, got: ${r.stdout}`);
});

test('fail-open: 깨진 .hb-rules.mjs → allow (강제 무력화 아님)', () => {
	const proj = mkProject();
	fs.writeFileSync(path.join(proj, '.hb-rules.mjs'), 'export default [ this is not valid js');
	const r = run(
		{ tool_name: 'Write', tool_input: { file_path: path.join(proj, 'a.ts'), content: 'x' } },
		proj
	);
	assert.ok(isAllow(r), `expected fail-open allow, got: ${r.stdout}`);
});

test('관할 밖 도구(Read 등) → allow', () => {
	const proj = mkProject();
	fs.writeFileSync(path.join(proj, '.hb-rules.mjs'), DENY_RULE);
	const r = run({ tool_name: 'Read', tool_input: { file_path: path.join(proj, 'a.ts') } }, proj);
	assert.ok(isAllow(r), `expected allow, got: ${r.stdout}`);
});

test('빈 stdin → allow', () => {
	const proj = mkProject();
	const res = spawnSync(process.execPath, [DISPATCHER], {
		input: '',
		encoding: 'utf8',
		env: { ...process.env, CLAUDE_PROJECT_DIR: proj },
	});
	assert.ok((res.status === 0) && (res.stdout || '').trim() === '');
});
