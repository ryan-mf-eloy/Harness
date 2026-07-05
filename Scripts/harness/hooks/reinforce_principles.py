#!/usr/bin/env python3
"""Actively re-surfaces the harness principles near the moment they matter,
instead of relying on them sitting passively in context. Claude Code
variant -- see reinforce_principles_cursor.py for the Cursor equivalent;
both share their actual message text via _reinforcement_common.py.

Why this exists: principles/PRINCIPLES.md is loaded once as "startup content"
(via ~/.claude/CLAUDE.md) and does survive /compact -- but surviving in
context is not the same as being *considered* on turn 400 of a long
implementation. Text that hasn't been touched in 300 turns competes for
attention with everything read since. This hook re-injects a short,
high-signal reminder at exactly the two moments that matter most:

  - SessionStart: once per session/resume, a pointer to the mechanism
    itself (not a repeat of the principles text -- that would just
    duplicate what ~/.claude/CLAUDE.md already loads).
  - PreToolUse on Edit/Write/MultiEdit: every single code-modifying action,
    a compact checklist. This is the actual answer to "principles must
    always be remembered during code changes" -- it fires precisely when
    a change happens, and reinforcement frequency scales UP with
    implementation size instead of decaying, which is the opposite of what
    plain context does over a long session.

Both branches use hookSpecificOutput.additionalContext, confirmed working
for both events live during implementation of this harness.
"""
from __future__ import annotations

import json
import sys

from _reinforcement_common import SESSION_START_REMINDER, checklist_message


def emit(event_name: str, context: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }))


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
        file_path = tool_input.get("file_path", "")
        session_id = payload.get("session_id", "unknown")
        emit("PreToolUse", checklist_message(file_path, session_id))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
