#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash): deny known-destructive command patterns
regardless of what the model decides. This is deliberately redundant with
the `permissions.deny` block in settings.template.json — both need to agree
to let a destructive command through, which is the point (defense in depth,
not a single point of failure if one list is ever edited carelessly).
"""
import json
import re
import sys

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"git\s+push\s+.*(--force|-f\b).*\b(origin\s+)?(main|master)\b"), "force-push to main/master"),
    (re.compile(r"git\s+push\s+.*\b(main|master)\b.*(--force|-f\b)"), "force-push to main/master"),
    (re.compile(r"git\s+reset\s+--hard"), "git reset --hard"),
    (re.compile(r"git\s+clean\s+-f"), "git clean -f"),
    (re.compile(r"git\s+branch\s+-D\b"), "force branch delete"),
    (re.compile(r"rm\s+-rf\s+(/|~|\.\s*$|\*\s*$)"), "rm -rf on a root/home/wildcard path"),
    (re.compile(r"--no-verify\b"), "--no-verify (skips hooks)"),
    (re.compile(r"--no-gpg-sign\b"), "--no-gpg-sign (skips commit signing)"),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return 0

    for pattern, label in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked by harness guardrail: matched destructive "
                        f"pattern '{label}'. If this is genuinely intended, "
                        f"it needs to be run manually by the user, not by an agent."
                    ),
                }
            }))
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
