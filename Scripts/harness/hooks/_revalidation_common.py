"""Shared detection logic for the test-revalidation Stop hooks
(check_tests_and_revalidation.py, check_tests_and_revalidation_codex.py).

Kept in one place for the same reason _reinforcement_common.py exists: the
two tool-specific wrappers must never disagree on what counts as "files
changed" or "a test was run" -- only their stdin/stdout framing differs,
since that's dictated by each tool's own hook schema.
"""
from __future__ import annotations

import re
from pathlib import Path

TEST_COMMAND_RE = re.compile(
    r"\b(npm (run )?test|pytest|go test|cargo test|jest|vitest|rspec|phpunit)\b",
    re.IGNORECASE,
)
NO_TESTS_MARKER_RE = re.compile(r"<no-tests-required:.*?>", re.IGNORECASE)

# Claude Code's transcript JSONL renders tool calls as "tool_name":"Edit" etc.
# Codex's transcript format at transcript_path is NOT independently confirmed
# to use the same literal string shape -- this list is deliberately broad
# (includes apply_patch) so the same detector has a chance of matching
# Codex's transcript too, but this breadth is a hedge, not a confirmed fact.
EDIT_TOOL_NAME_MARKERS = (
    '"tool_name":"Edit"',
    '"tool_name":"Write"',
    '"tool_name":"MultiEdit"',
    '"tool_name":"apply_patch"',
)

NO_TESTS_BLOCK_REASON = (
    "Files were modified this turn but no test command was observed. "
    "Per the engineering-principles rule, run the appropriate test "
    "suite before finishing, or state explicitly why tests don't "
    "apply (e.g. `<no-tests-required: docs-only change>`). For a "
    "non-trivial change, this mechanical check is a floor, not the "
    "real review -- the pre-delivery-review skill covers what this "
    "hook can't (multi-source cross-check, not just 'was a test "
    "command typed')."
)


def read_transcript_tail(transcript_path: str, max_lines: int = 400) -> str:
    path = Path(transcript_path)
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-max_lines:])


def files_changed_without_tests(tail: str) -> tuple[bool, str]:
    """Returns (should_block, reason_or_empty)."""
    if not tail:
        return False, ""  # can't inspect the transcript -- fail open
    files_changed = any(marker in tail for marker in EDIT_TOOL_NAME_MARKERS)
    if not files_changed:
        return False, ""  # pure investigation/planning turn -- nothing to gate
    if NO_TESTS_MARKER_RE.search(tail):
        return False, ""  # explicit, auditable escape hatch used
    if TEST_COMMAND_RE.search(tail):
        return False, ""  # a test command was observed somewhere in this turn
    return True, NO_TESTS_BLOCK_REASON
