#!/usr/bin/env python3
"""PreToolUse hook: deny Write/Edit/MultiEdit and destructive Bash under RAG/.

Wired in claude/settings.template.json against the PreToolUse event with
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
DESTRUCTIVE_BASH_RE = re.compile(r"\b(rm|mv|truncate|shred)\b|>>?|1>|2>")


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
        if RAG_MARKER in command and DESTRUCTIVE_BASH_RE.search(command):
            deny(
                "Destructive command targeting RAG/ blocked. Follow the "
                "manual override procedure in RAG/README.md if this change "
                "is genuinely warranted."
            )
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
