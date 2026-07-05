#!/usr/bin/env python3
"""Cursor variant of reinforce_principles.py -- see that file for the full
rationale. Message text is shared via _reinforcement_common.py; only the
JSON input/output framing differs, because that's dictated by Cursor's own
hook schema (snake_case, no hookSpecificOutput wrapper, sessionStart/
postToolUse instead of SessionStart/PreToolUse).

Honest caveat (documented, not silently assumed): Cursor's `afterFileEdit`
event is the semantically precise one for "a file was just edited," but per
Cursor's own docs it does NOT support returning additional_context --
observational only. `postToolUse` is the only event confirmed to support
additional_context, but it fires for every tool call (e.g. running a shell
command), not only edits, and its exact tool_name/tool_input shape for
Cursor's built-in file-edit tool isn't fully documented publicly at the
time this was written. This script defensively inspects tool_name and
tool_input for common file-edit signals (a "file_path"/"path" key, or
"edit"/"write" in the tool name) and only emits a reminder when it
recognizes one -- so a call it doesn't recognize is silently skipped
rather than spamming a reminder on unrelated tool calls like a shell
command. If this never fires in practice, the fix is to log one real
payload from an actual edit and adjust the detection below -- see
Scripts/harness/hooks/README.md.
"""
from __future__ import annotations

import json
import sys

from _reinforcement_common import SESSION_START_REMINDER, checklist_message

FILE_PATH_KEYS = ("file_path", "path", "filePath")
EDIT_TOOL_NAME_HINTS = ("edit", "write", "file")


def detect_file_path(tool_name: str, tool_input: dict) -> str:
    for key in FILE_PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    if any(hint in tool_name.lower() for hint in EDIT_TOOL_NAME_HINTS):
        # recognized as an edit-shaped tool but no path field we know of --
        # still worth a reminder, just without per-file escalation tracking
        return ""
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    event = payload.get("hook_event_name", "")

    if event == "sessionStart":
        print(json.dumps({"additional_context": SESSION_START_REMINDER}))
        return 0

    if event == "postToolUse":
        tool_name = payload.get("tool_name", "") or ""
        tool_input = payload.get("tool_input", {}) or {}
        is_edit_shaped = any(tool_input.get(k) for k in FILE_PATH_KEYS) or any(
            hint in tool_name.lower() for hint in EDIT_TOOL_NAME_HINTS
        )
        if not is_edit_shaped:
            return 0  # not recognized as a file edit -- stay silent, don't spam

        file_path = detect_file_path(tool_name, tool_input)
        session_id = payload.get("conversation_id", "unknown")
        print(json.dumps({"additional_context": checklist_message(file_path, session_id)}))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
