#!/usr/bin/env python3
"""Codex CLI variant of reinforce_principles.py -- see that file for the full
rationale. Message text is shared via _reinforcement_common.py; only the
JSON input/output framing differs at the points where Codex's own schema is
confirmed to diverge from Claude Code's.

Confirmed (via https://developers.openai.com/codex/hooks): hookSpecificOutput
.additionalContext is the SAME output shape Claude Code uses, for both
SessionStart and PreToolUse -- this is the reason this file is a thin
wrapper and not a from-scratch reimplementation. Event names are the same
PascalCase strings: SessionStart, PreToolUse. For file edits, Codex reports
tool_name: "apply_patch" -- NEVER "Edit", "Write", or "MultiEdit" -- even
when the hooks.json matcher itself is written as "apply_patch|Edit|Write"
(the matcher string is lenient; the runtime tool_name value is not).

NOT independently confirmed: the exact key inside apply_patch's own
tool_input that names the file being edited. Claude Code's Edit/Write/
MultiEdit use tool_input.file_path; this has not been confirmed to carry
over unchanged for apply_patch specifically. This script defensively checks
a short list of candidate keys and falls back to an empty file_path (still
emits the reminder, just without per-file escalation tracking) rather than
assuming a key name and silently emitting nothing if wrong.
"""
from __future__ import annotations

import json
import sys

from _reinforcement_common import SESSION_START_REMINDER, checklist_message

FILE_PATH_KEYS = ("file_path", "path", "target_file", "file")


def emit(event_name: str, context: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }))


def detect_file_path(tool_input: dict) -> str:
    for key in FILE_PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    event = payload.get("hook_event_name", "")

    if event == "SessionStart":
        emit("SessionStart", SESSION_START_REMINDER)
        return 0

    if event == "PreToolUse":
        tool_input = payload.get("tool_input", {}) or {}
        file_path = detect_file_path(tool_input)
        session_id = payload.get("session_id", "unknown")
        emit("PreToolUse", checklist_message(file_path, session_id))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
