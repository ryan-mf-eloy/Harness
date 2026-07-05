---
name: Pre-Delivery Review
description: Multi-source review before declaring a non-trivial task finished — checks the actual deliverable against every relevant available source (diff, tests actually run, memory/vault notes, connected MCP systems, logs), separates verified from assumed, and documents genuinely novel solutions so the next search finds them. The substantive counterpart to pre-change-impact-check, which opens a task; this closes it.
when_to_use: Before considering a non-trivial implementation, investigation, or multi-step task finished — especially after touching more than one file, after a debugging session, or before reporting a conclusion that a decision will be based on.
argument-hint: "[optional: what you're about to declare done]"
allowed-tools: Read, Grep, Glob, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(python3 */Scripts/harness/query.py*)
---

Run this before saying a non-trivial task is done. Do not skip it because
the diff looks clean — a clean diff is not the same as a verified result.

1. **Re-state the original acceptance criteria** and check each one off
   explicitly against what was actually done, not what was intended.
2. **Check the diff itself** (`git diff`, `git status`) — does it match
   what you're about to claim you changed? No unexplained extra files, no
   scope creep left in.
3. **Check tests for real** — not "I wrote a test" but "I ran it and saw
   it pass." If you didn't run something, say so explicitly rather than
   implying you did.
4. **Cross-check available sources relevant to this task** — whichever of
   these actually apply, don't invent access that isn't there:
   - `Vault/40-Memory/<project-slug>/` and `Vault/10-Projects/<project-slug>/`
     for a prior decision or investigation this might conflict with
   - the FTS index (`Scripts/harness/query.py`) for related precedent
   - any connected MCP system the task's claim depends on (a task
     tracker, a log aggregator, a database) — verify against the live
     system instead of assuming it matches what you read earlier in the
     conversation
   - logs, if the task involved debugging — confirm the fix against the
     actual error signature, not just "the code looks right now"
5. **Take a second, different-angle look.** Could this be read another
   way? Does the evidence actually support the conclusion, or does it just
   seem to because it confirms what you expected to find?
6. **State verified vs. assumed, explicitly and separately.** Don't let a
   confident tone imply more certainty than the evidence supports — say
   plainly what you checked and what you didn't get to.
7. **If this was genuinely novel** (no precedent was found in step 2 of
   `pre-change-impact-check`), write it up in `Vault/20-Knowledge/` — see
   that folder's `README.md` for the format. This is the step that closes
   the precedent-before-invention loop: the next agent's search should
   find this instead of re-solving it from nothing.
8. **Hygiene pass.** Does this make any existing Vault/memory note stale
   or wrong? Update that note instead of leaving a new, contradicting one
   beside it — see the `consolidate-memory` skill if memory has
   accumulated enough that a broader cleanup is due, not just this one
   note.
