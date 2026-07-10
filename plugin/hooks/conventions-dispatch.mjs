#!/usr/bin/env node
//
// PreToolUse hook: fixed convention dispatcher (mechanism, not policy).
//
// Reads the tool event on stdin, reconstructs the resulting file content,
// then walks up the directory tree from the target file to CLAUDE_PROJECT_DIR
// collecting every <dir>/.hb-rules.mjs it finds. Each such module exports a
// default array of RuleModule; the dispatcher runs their validate() and
// denies (deny-wins) if any returns a violation.
//
// Design: mechanism/policy split. This file (shipped by the hb-corporation
// plugin) is pure plumbing. It ships ZERO rules — every rule lives in a
// project's own .hb-rules.mjs. Fail-open everywhere: any error in the
// dispatcher, in importing a rules module, or inside a rule -> that layer is
// skipped and the tool is allowed. Only a confirmed violation blocks.
//
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function allow() {
	process.exit(0);
}

function deny(reason) {
	process.stdout.write(
		JSON.stringify({
			hookSpecificOutput: {
				hookEventName: 'PreToolUse',
				permissionDecision: 'deny',
				permissionDecisionReason: reason,
			},
		})
	);
	process.exit(0);
}

function readStdin() {
	try {
		return fs.readFileSync(0, 'utf8');
	} catch {
		return '';
	}
}

async function main() {
	const raw = readStdin();
	if (!raw.trim()) allow();

	let evt;
	try {
		evt = JSON.parse(raw);
	} catch {
		allow();
		return;
	}

	const tool = evt.tool_name;
	const input = evt.tool_input || {};
	const rawPath = input.file_path;
	if (!rawPath) allow();

	const filePath = String(rawPath).replace(/\\/g, '/');

	let content;
	let previousContent;
	if (tool === 'Write') {
		content = input.content ?? '';
		try {
			previousContent = fs.readFileSync(rawPath, 'utf8');
		} catch {
			previousContent = null;
		}
	} else if (tool === 'Edit') {
		let current;
		try {
			current = fs.readFileSync(rawPath, 'utf8');
		} catch {
			allow();
			return;
		}
		const oldS = input.old_string;
		const newS = typeof input.new_string === 'string' ? input.new_string : '';
		if (!oldS || !current.includes(oldS)) {
			allow();
			return;
		}
		content = input.replace_all ? current.split(oldS).join(newS) : current.replace(oldS, newS);
		previousContent = current;
	} else {
		allow();
		return;
	}

	const modulePaths = collectRuleModules(filePath);
	if (modulePaths.length === 0) allow();

	const ctx = { tool, filePath, content, previousContent };
	const reasons = [];

	for (const modPath of modulePaths) {
		let mod;
		try {
			// Windows paths must go through pathToFileURL — import('D:/...') breaks.
			mod = await import(pathToFileURL(modPath).href);
		} catch {
			continue;
		}
		const rules = Array.isArray(mod.default) ? mod.default : [];
		for (const rule of rules) {
			try {
				if (typeof rule.applies === 'function' && !rule.applies(ctx)) continue;
				const verdict = await rule.validate(ctx);
				if (verdict && verdict.ok === false) reasons.push(verdict.reason);
			} catch {
				continue;
			}
		}
	}

	if (reasons.length > 0) deny(reasons.join('\n\n'));
	allow();
}

// Walk up from dirname(filePath) collecting <dir>/.hb-rules.mjs.
// Stops after including the CLAUDE_PROJECT_DIR level, or at the filesystem root.
function collectRuleModules(filePath) {
	const root = (process.env.CLAUDE_PROJECT_DIR || '').replace(/\\/g, '/');
	const found = [];
	let dir = path.dirname(filePath).replace(/\\/g, '/');
	while (true) {
		const candidate = dir + '/.hb-rules.mjs';
		try {
			if (fs.existsSync(candidate)) found.push(candidate);
		} catch {
			// ignore fs errors, keep walking
		}
		if (dir === root) break;
		const parent = path.dirname(dir).replace(/\\/g, '/');
		if (parent === dir) break;
		dir = parent;
	}
	return found;
}

main().catch(() => allow());
