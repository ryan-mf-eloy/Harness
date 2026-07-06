---
type: decision
tags: [harness, hooks, cursor, codex, cross-tool]
status: active
created: 2026-07-05
---

# Cross-tool hook portability for Cursor and Codex CLI

## Context

This harness's enforcement hooks (`Scripts/harness/hooks/`,
`Scripts/harness/guard_rag_immutable.py`) were originally Claude-Code-only,
with a partial Cursor port already done for the reinforcement mechanism
(`reinforce_principles_cursor.py`). `Scripts/harness/hooks/README.md` and
`AGENTS.md` both stated, as settled fact, that Codex CLI had no hook
mechanism at all — reasoning that its enforcement model was purely an
OS-level sandbox (macOS Seatbelt / Linux bwrap+seccomp) with no way to
inject context mid-session.

That claim was checked directly against Codex's current first-party docs
(`https://developers.openai.com/codex/hooks`) during this same work and
found to be false. Codex CLI added a real, general-purpose hook system
around v0.117.0, with a wire format close enough to Claude Code's own
(`{"hooks": {"PreToolUse": [...]}}`, PascalCase event names, shared field
names like `tool_name`/`tool_input`/`transcript_path`) that this was
evidently not a from-scratch design on OpenAI's part.

This required extending the same cross-tool reach already being pursued
for skills/agents (a parallel, separately-recorded decision) to this
repo's hook scripts specifically.

## Decision

1. `block_destructive_bash.py` and `guard_rag_immutable.py` (pure
   allow/deny hooks, no context injection) switch their deny mechanism from
   emitting `hookSpecificOutput`/`permissionDecision` JSON to **exit code 2
   with the reason on stderr**, with zero per-tool branching in the script
   body. This is the only deny convention confirmed identical, first-party
   documented, across Claude Code, Cursor, and Codex CLI — Cursor's flat
   `preToolUse` response schema does not understand the nested JSON
   envelope at all, making exit-2 the actual lowest common denominator, not
   an arbitrary simplification.
2. Both scripts also recognize each tool's own tool-name values where they
   diverge from Claude Code's: `apply_patch` (Codex, for all file edits)
   and `Shell` (Cursor, for shell commands), alongside Claude Code's
   `Edit`/`Write`/`MultiEdit`/`Bash`.
3. New root-level `.cursor/hooks.json` and `.codex/hooks.json` wire
   `guard_rag_immutable.py` into this repo's own project scope (mirroring
   the existing `.claude/settings.json` project-scoped split) —
   `block_destructive_bash.py` stays global-only, wired into each tool's
   own global config (`~/.cursor/hooks.json`, newly-created
   `~/.codex/hooks.json`), matching its existing global-only wiring in
   `~/.claude/settings.json`.
4. `reinforce_principles_codex.py` (new file) joins the existing Claude
   Code and Cursor wrappers, importing shared message text from
   `_reinforcement_common.py` — not forked, per that module's existing
   purpose.
5. `check_tests_and_revalidation.py` gets a Codex counterpart
   (`check_tests_and_revalidation_codex.py`), since Codex's `Stop` event
   payload was confirmed (not assumed) to include `transcript_path` — this
   was an open question going into this work and resolved as present, not
   a gap. Shared detection logic was extracted into a new
   `_revalidation_common.py` module (kept separate from
   `_reinforcement_common.py`, which is scoped to the principles-
   reinforcement message family specifically) so the two Stop-hook
   wrappers can't disagree on what counts as "a file changed" or "a test
   ran."
6. `Scripts/harness/hooks/README.md` and `AGENTS.md` are corrected, not
   softened — both explicitly named the prior claim as wrong and explain
   what's actually true, rather than quietly rewriting history.

## Alternatives considered

- **Keep `hookSpecificOutput` JSON for Claude Code/Codex, add exit-2 only
  as a Cursor-specific fallback.** Rejected: requires the script to either
  know which tool invoked it or emit both mechanisms unconditionally —
  real branching complexity for a benefit (Claude Code's UI rendering of
  `permissionDecisionReason` vs. a bare stderr line) judged minor against
  the stated goal of minimal-to-zero per-tool branching.
- **Reuse `reinforce_principles.py` verbatim for Codex, given the wire
  format is nearly identical.** Rejected: the *output* framing is
  identical (`hookSpecificOutput.additionalContext` confirmed for both
  events on both tools), but the confirmed fact that Codex's `apply_patch`
  tool_name is the ONLY value ever reported for file edits (never
  `Edit`/`Write`/`MultiEdit`) means any future edit to the Claude Code
  script that starts branching on `tool_name` would silently break on
  Codex with no warning. A separate thin file, explicit about this
  divergence in its own docstring, was judged safer than a shared file
  carrying an implicit, undocumented assumption.
- **Silently drop `check_tests_and_revalidation.py`'s Codex port on the
  assumption Stop has no transcript equivalent.** Rejected outright once
  the docs fetch confirmed `transcript_path` is present — this was the
  literal failure mode (guessing a gap without checking) that produced the
  original wrong "Codex has no hooks" claim in the first place, and
  repeating it in the opposite direction (assuming absence without
  checking) would be the same mistake.
- **Extend `_reinforcement_common.py` with the Stop-hook detection logic
  instead of a new module.** Rejected — the reinforcement and
  revalidation hook families are conceptually distinct (context injection
  vs. turn-blocking), and growing one shared module to cover both would
  broaden its scope past what its own docstring states, the same
  boundary-drawn-wrong signal this harness's own principles warn against
  elsewhere.

## Consequences

- Three tools' worth of enforcement now share two Python files
  (`block_destructive_bash.py`, `guard_rag_immutable.py`) with zero
  per-tool code branches — future destructive-pattern additions only need
  editing in one place, no risk of the Cursor/Codex copies drifting from
  Claude Code's.
- Claude Code loses the `permissionDecisionReason` JSON-rendered deny
  message in its own UI in favor of a plain stderr line — a real, if
  minor, UX regression on the one tool that previously had the nicer
  presentation, accepted deliberately for cross-tool uniformity.
- Two residual, explicitly-documented (not silently smoothed-over)
  uncertainties remain for future verification: (1) whether Codex's
  `hooks.json` `command` field performs `${CLAUDE_PROJECT_DIR}`-style
  variable substitution the way Claude Code/Cursor do — unverified, this
  repo's own project-scoped `.codex/hooks.json` may need a literal
  absolute path instead if it doesn't; (2) the exact key name inside
  Codex's `apply_patch` `tool_input` for the file path, and the exact
  byte-level format Codex writes to `transcript_path` — both hedged
  defensively in code rather than assumed, with an explicit fix-forward
  path documented (capture one real payload, adjust the candidate-key
  list) if either hedge turns out wrong in practice.
