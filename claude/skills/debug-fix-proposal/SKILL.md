---
name: Debug & Fix Proposal
description: Structured root-cause investigation and minimal-fix proposal procedure for a bug, failing test, or unexpected behavior — reproduces the issue, isolates root cause, proposes the smallest fix, and states confidence level before applying anything.
when_to_use: A test is failing, an error is reported, or behavior doesn't match the spec/acceptance criteria, and the cause is not yet understood.
allowed-tools: Read, Grep, Glob, Bash
user-invocable: false
---

Skip: a planned new feature or change with no existing broken behavior —
that's `pre-change-impact-check`'s job, not this one.

1. **Reproduce** — get a minimal, deterministic repro (failing test, exact
   command, exact input) before touching source.
2. **Isolate** — bisect via logs/`git blame`/binary search on inputs, not by
   guessing. State the hypothesis explicitly before testing it.
3. **State the root cause** in one or two falsifiable sentences — not
   "seems related to X."
4. **Propose the smallest fix** that addresses the root cause, not the
   symptom. Explicitly reject "swallow the exception" / "add a retry"
   band-aids unless that genuinely is the correct fix.
5. **State confidence** (high/medium/low) and what would raise it (e.g.
   "would want a repro on production-shaped data to be fully confident").
6. **Apply only after** the testing gate can be satisfied for the fix —
   write or update the failing test as the first artifact of the fix, watch
   it go red then green.

For a bug worth delegating to its own context (verbose logs, long
investigation), use the `debugger` subagent instead of running this inline —
it follows this same procedure with its own tool scoping and persistent
memory of past root causes.
