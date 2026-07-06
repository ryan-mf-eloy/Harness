#!/usr/bin/env python3
"""Codex CLI variant of check_tests_and_revalidation.py -- see that file for
the full rationale. Detection logic is shared via _revalidation_common.py;
only the stdin/stdout framing differs where Codex's schema is confirmed to
diverge.

Confirmed (https://developers.openai.com/codex/hooks): Codex's Stop event
payload includes transcript_path (string | null) as a common field, same
field name as Claude Code -- this hook's entire mechanism depends on that,
and it is present, not a gap. Also confirmed: Stop's block/continue response
uses the same {"decision": "block", "reason": "..."} shape as Claude Code
("legacy format", per the docs), which is why this wrapper's output line is
identical to the Claude Code script's.

NOT independently confirmed: the exact byte-level format of what Codex
writes to the file at transcript_path (its own transcript/session-log
serialization was not fetched in this design pass). The shared detector in
_revalidation_common.py's EDIT_TOOL_NAME_MARKERS includes an "apply_patch"
variant as a hedge against Codex's transcript format differing from Claude
Code's JSONL shape, but this is a defensive guess, not a verified match --
if this hook is observed to never fire in practice on Codex despite real
edits happening, capture one real transcript_path file's actual content and
adjust the markers/detection in _revalidation_common.py accordingly, same
troubleshooting path the Cursor reinforcement wrapper's docstring already
prescribes for its own analogous gap.
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
