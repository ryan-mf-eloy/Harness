#!/usr/bin/env python3
"""PreToolUse hook: deny creating or editing a GitHub Actions workflow file
(`.github/workflows/*.yml`/`*.yaml`) regardless of what the model decides.

Why: remote/CI automation is heavier, harder to review, and harder to
revert than a local validation command. Reaching for it as a shortcut
around inadequate local validation is a known failure mode when left to
advisory judgment alone (see the remote-automation bullet in this repo's
principles/PRINCIPLES.md, under "Non-negotiable safety rules," which this
hook enforces deterministically) — text alone doesn't reliably stop it, a
gate does.

Cross-tool: fires on Write/Edit/MultiEdit/NotebookEdit (Claude Code),
apply_patch (Codex — the target path is embedded in the patch text, not a
clean file_path), and Bash/Shell (Claude Code/Codex/Cursor — only blocked
if the command shows actual write intent, so reading an existing workflow
file is unaffected).

Deny mechanism: exit code 2 with the reason on stderr — the one convention
confirmed identical across Claude Code, Cursor, and Codex CLI (see
Scripts/harness/hooks/README.md's cross-provider section). Every match is a
hard deny on all three tools; there is no softer "ask" tier once the deny
mechanism is a bare exit code, which is a deliberate trade for a mechanism
that actually works identically everywhere.

Heuristic, not a real shell/patch parser (see hooks/README.md's "Known
limitation" section for the general caveat this shares with the other
regex-based guards). Fails open on any parse error.
"""
from __future__ import annotations

import json
import re
import sys

WORKFLOW_PATH_RE = re.compile(r"\.github/workflows/[^\s\"'`)\\]+\.ya?ml\b", re.IGNORECASE)
SHELL_TOOL_NAMES = {"Bash", "Shell"}
EDIT_TOOL_NAMES = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}
WRITE_INTENT_RE = re.compile(r">|\btee\b|\btouch\b|\bcp\b|\bmv\b|<<|\bmkdir\b|\binstall\b", re.IGNORECASE)

REASON = (
    "Blocked by harness guardrail: creating or editing a GitHub Actions "
    "workflow file. Exhaust the project's own local validation commands "
    "(lint/typecheck/test/build) before reaching for remote CI automation as "
    "a shortcut — remote automation needs explicit user approval first, not "
    "just a plausible-looking pipeline."
)


def candidate_strings(tool_input: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            out.append(("path", value))
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
                out.append(("path", edit["file_path"]))
    command = tool_input.get("command")
    if isinstance(command, str):
        out.append(("command", command))
    return out


def is_blocked(tool_name: str, tool_input: dict) -> bool:
    for kind, value in candidate_strings(tool_input):
        normalized = value.replace("\\", "/")
        if not WORKFLOW_PATH_RE.search(normalized):
            continue
        if kind == "command" and tool_name in SHELL_TOOL_NAMES and not WRITE_INTENT_RE.search(value):
            continue
        return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in EDIT_TOOL_NAMES and tool_name not in SHELL_TOOL_NAMES:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    if not is_blocked(tool_name, tool_input):
        return 0

    print(REASON, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
