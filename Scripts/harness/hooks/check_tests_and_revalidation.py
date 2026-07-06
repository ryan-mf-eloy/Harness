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

Detection logic lives in _revalidation_common.py, shared with the Codex CLI
variant (check_tests_and_revalidation_codex.py) so the two can never
disagree on what counts as "files changed" or "a test was run."
"""
import json
import sys

from _revalidation_common import files_changed_without_tests, read_transcript_tail


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    transcript_path = payload.get("transcript_path", "")
    tail = read_transcript_tail(transcript_path)

    should_block, reason = files_changed_without_tests(tail)
    if should_block:
        print(json.dumps({"decision": "block", "reason": reason}))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
