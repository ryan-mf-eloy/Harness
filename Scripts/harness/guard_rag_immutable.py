#!/usr/bin/env python3
"""PreToolUse hook: deny Write/Edit/MultiEdit and destructive Bash under RAG/.

Wired in this repo's own .claude/settings.json against the PreToolUse event with
matcher "Write|Edit|MultiEdit|Bash". Reads the hook JSON payload from stdin
(the only input format the hook mechanism guarantees), never relies on
shell-templated placeholders beyond CLAUDE_PROJECT_DIR.

To make a legitimate change, follow the manual override procedure in
RAG/README.md instead of editing around this guard.
"""
import json
import re
import sys

RAG_MARKER = "RAG" + "/"
# Split into rough shell sub-commands so a destructive pattern in one part
# (e.g. a redirect suppressing stderr on an unrelated command) can't be
# co-mingled with an unrelated "RAG/" mention elsewhere in the same command
# line -- e.g. `echo "...RAG/..." && find . 2>/dev/null` used to trip this
# guard even though nothing writes to RAG/. Not real shell parsing (doesn't
# understand $(...) or block structure), so it can over-split -- that only
# makes the check MORE conservative, never less, which is the safe
# direction to err in.
COMMAND_SEPARATOR_RE = re.compile(r"&&|\|\||[;|\n]")
DESTRUCTIVE_COMMAND_RE = re.compile(r"\b(rm|mv|truncate|shred)\b")
# A redirect only counts if ITS TARGET references RAG/, not just any `>`
# appearing somewhere in a command that separately mentions RAG/ (e.g.
# `2>/dev/null` used to match this on its own).
REDIRECT_TO_RAG_RE = re.compile(r">>?\s*\S*" + re.escape(RAG_MARKER))


def command_threatens_rag(command: str) -> bool:
    if REDIRECT_TO_RAG_RE.search(command):
        return True
    for segment in COMMAND_SEPARATOR_RE.split(command):
        if RAG_MARKER in segment and DESTRUCTIVE_COMMAND_RE.search(segment):
            return True
    return False


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail open on malformed input rather than block unrelated tool calls

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if tool_name in ("Write", "Edit", "MultiEdit"):
        file_path = tool_input.get("file_path", "")
        if RAG_MARKER in file_path:
            deny(
                "RAG/ is near-immutable source-of-truth. Direct edits are "
                "blocked. Follow the manual override procedure in "
                "RAG/README.md if this change is genuinely warranted."
            )
            return 0

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if command_threatens_rag(command):
            deny(
                "Destructive command targeting RAG/ blocked. Follow the "
                "manual override procedure in RAG/README.md if this change "
                "is genuinely warranted."
            )
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
