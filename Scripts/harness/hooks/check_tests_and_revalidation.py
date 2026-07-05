#!/usr/bin/env python3
"""Stop hook: before letting a turn end, check whether files were modified
this session and, if so, whether a test command was ever observed running.

This is a heuristic, not a proof — it greps the transcript for test-looking
commands, which is inherently weaker evidence than the destructive-bash
pattern match in block_destructive_bash.py. Treat it as a nudge backed by a
real gate, not an ironclad guarantee, and prefer strengthening it (e.g. a
project-specific test command recorded in that project's own settings)
over trusting the generic heuristic alone.

Escape hatch: if the assistant's final message contains the literal marker
`<no-tests-required: ...>`, the gate passes without a test command found —
for turns that legitimately don't need one (docs-only changes, pure
investigation). Without an escape hatch this becomes the kind of hook people
just disable.
"""
import json
import re
import sys
from pathlib import Path

TEST_COMMAND_RE = re.compile(
    r"\b(npm (run )?test|pytest|go test|cargo test|jest|vitest|rspec|phpunit)\b",
    re.IGNORECASE,
)
NO_TESTS_MARKER_RE = re.compile(r"<no-tests-required:.*?>", re.IGNORECASE)


def read_transcript_tail(transcript_path: str, max_lines: int = 400) -> str:
    path = Path(transcript_path)
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-max_lines:])


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    transcript_path = payload.get("transcript_path", "")
    tail = read_transcript_tail(transcript_path)
    if not tail:
        return 0  # can't inspect the transcript — fail open rather than block blindly

    files_changed = '"tool_name":"Edit"' in tail or '"tool_name":"Write"' in tail or '"tool_name":"MultiEdit"' in tail
    if not files_changed:
        return 0  # pure investigation/planning turn — nothing to gate

    if NO_TESTS_MARKER_RE.search(tail):
        return 0  # explicit, auditable escape hatch used

    if TEST_COMMAND_RE.search(tail):
        return 0  # a test command was observed somewhere in this turn

    print(json.dumps({
        "decision": "block",
        "reason": (
            "Files were modified this turn but no test command was observed. "
            "Per the engineering-principles rule, run the appropriate test "
            "suite before finishing, or state explicitly why tests don't "
            "apply (e.g. `<no-tests-required: docs-only change>`)."
        ),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
