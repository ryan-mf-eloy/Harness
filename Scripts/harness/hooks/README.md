# Scripts/harness/hooks/

Enforcement hooks. Each one is deterministic — it runs regardless of what
the model decides, unlike `principles/PRINCIPLES.md`, which is only ever
advisory context. They're split across two settings scopes depending on
whether the check depends on this repo's own files:

| Script | Event | Matcher | Wired in | Purpose |
|---|---|---|---|---|
| `block_destructive_bash.py` | `PreToolUse` | `Bash` | `~/.claude/settings.json` (global — no dependency on any specific project's files) | Deny known-destructive command patterns (force-push to main, `reset --hard`, `rm -rf` on root/home, `--no-verify`) — redundant with `permissions.deny` on purpose, defense in depth |
| `check_tests_and_revalidation.py` | `Stop` | — | `~/.claude/settings.json` (global) | Block ending the turn if files changed but no test command was observed, unless an explicit `<no-tests-required: ...>` marker is present |
| `reinforce_principles.py` | `SessionStart` | — | `~/.claude/settings.json` (global) | Once per session/resume, points at the mechanism (principles auto-loaded + per-edit checklist) — does not repeat `principles/PRINCIPLES.md` content, since that's already loaded separately and repeating it would just waste tokens |
| `reinforce_principles.py` (same script, branches on `hook_event_name`) | `PreToolUse` | `Edit\|Write\|MultiEdit` | `~/.claude/settings.json` (global) | Injects a short reuse/diff-size/testing/blast-radius checklist as `additionalContext` before **every** code-modifying action — this is the actual answer to "principles must always be considered during changes": reinforcement frequency scales up with implementation size instead of decaying over a long session. Escalates its message once a session has touched 5+ distinct files, nudging toward `pre-change-impact-check` |
| `../guard_rag_immutable.py` | `PreToolUse` | `Write\|Edit\|MultiEdit\|Bash` | this repo's own `.claude/settings.json` (project-scoped — only meaningful when the working directory is this repo) | Deny edits under `RAG/` (see `RAG/README.md`) |
| `../index_upsert.py` | `PostToolUse` | `Write\|Edit\|MultiEdit` | this repo's own `.claude/settings.json` (project-scoped) | Incrementally reindex a changed file if it's under `Vault/` or `RAG/` |

## Why principles need active reinforcement, not just passive loading

`principles/PRINCIPLES.md` reloads automatically from disk after every
`/compact` (confirmed against the official "what survives compaction"
table — it's startup content via `~/.claude/CLAUDE.md`, not part of the
summarized message history). But surviving in context is not the same as
being *considered*: on turn 400 of a long implementation, text that hasn't
been touched since turn 1 competes for attention with everything read
since. `reinforce_principles.py`'s `PreToolUse` branch exists specifically
to counter that — it re-injects a short reminder at the exact moment of
every code change, so the reminder is always fresh relative to the action,
regardless of how long the session has run. This is still advisory (it
can't force SOLID compliance the way `block_destructive_bash.py` forces a
denied Bash command) — it raises the odds the model actually weighs the
principles at the right moment, it doesn't guarantee it.

The global hooks reference this repo by **absolute path** (they run no
matter which project you're in, so `${CLAUDE_PROJECT_DIR}` would resolve to
the wrong place outside this repo). The project-scoped hooks use
`${CLAUDE_PROJECT_DIR}` correctly, since they only ever fire while a session
actually has this repo as its working directory.

All of these fail open on malformed/unreadable input (exit 0, no block)
rather than risk blocking unrelated work on a parsing bug — a hook that
fails closed on its own error is worse than the guardrail it's trying to
enforce.

When onboarding a new project, copy `templates/settings.permissions-baseline.json`
into that project's own `.claude/settings.json` as a starting point — it
does not carry the hooks above, since those are either global already
(no copy needed) or specific to this repo's own `RAG/`/`Vault/` paths (not
meaningful in another project).

## Cross-provider: Cursor and Codex CLI

The reinforcement mechanism (not the destructive-command/RAG guards) is
also wired into Cursor, since the "principles must be considered during
changes" requirement isn't Claude-Code-specific:

- **Cursor**: `~/.cursor/hooks.json` (real file, not part of this repo,
  same pattern as `~/.claude/settings.json`) wires `sessionStart` and
  `postToolUse` to `reinforce_principles_cursor.py`, sharing its actual
  message text with the Claude Code script via `_reinforcement_common.py`.
  One confirmed, honest gap: Cursor's `afterFileEdit` event is the
  semantically precise one for "a file was edited," but per Cursor's own
  docs it does **not** support returning `additional_context` —
  observational only. `postToolUse` is the only event confirmed to support
  it, but it fires for every tool call, not just edits, and Cursor's exact
  `tool_name`/`tool_input` shape for its built-in edit tool isn't fully
  documented publicly as of this writing. The script defensively detects
  edit-shaped calls (a `file_path`/`path` key, or "edit"/"write" in the
  tool name) and stays silent otherwise, rather than guessing wrong and
  spamming every shell command. If it turns out to never fire in practice,
  log one real `postToolUse` payload from an actual edit and adjust the
  detection in `reinforce_principles_cursor.py`.
- **Codex CLI**: no equivalent wired, and there isn't a good way to build
  one. Codex's enforcement model is fundamentally different — an
  OS-level sandbox (macOS Seatbelt / Linux bwrap+seccomp) plus an approval
  policy, not an arbitrary-script hook system like Claude Code's or
  Cursor's. That sandbox already does real enforcement (blocks writes
  outside the workspace, blocks network by default) but has no mechanism
  to inject a text reminder into the model's context mid-session. For
  Codex, `principles/PRINCIPLES.md` (via the `~/.codex/AGENTS.md` symlink)
  is the only lever available, with the same passive-loading caveats as
  any AGENTS.md content, and Codex's own docs confirm it re-reads
  `AGENTS.md`/`AGENTS.override.md` once per launched session — there's no
  per-edit reinforcement equivalent to offer here, and claiming otherwise
  would overstate what's actually possible.

## Known limitation of the regex-based Bash guards

`block_destructive_bash.py` and `guard_rag_immutable.py`'s Bash branch both
pattern-match the raw command string. This was confirmed, live, during
implementation: a `python3 -c "..."` command whose inline script merely
*mentioned* the words "rm", "mv", "truncate", "shred" as documentation prose
(not as an actual invocation) was incorrectly blocked, because the regex
has no way to distinguish a real command from a string literal describing
one. The inverse also holds — a command that writes a file through a
mechanism the regex doesn't enumerate (`sed -i`, a Python script, a `cat`
heredoc without `>`) is not caught by either hook at all. No regex-based
command guard can close both gaps at once without actually parsing shell
syntax and program semantics, which is out of scope here.

Treat these hooks as a strong deterrent against the common, literal forms
of the risky commands they name — not an airtight sandbox. The filesystem
permission lock (`chmod -R a-w RAG/`) and the `permissions.deny` rules in
settings are independent layers precisely because no single layer is
complete on its own.

A second, related bug was found and fixed the same way: `guard_rag_immutable.py`
originally checked "does 'RAG/' appear anywhere in the command" and "does a
destructive pattern appear anywhere in the command" as two independent,
whole-string checks — so `echo "...RAG/..." && find . 2>/dev/null` tripped
it even though the redirect and the RAG/ mention were unrelated parts of
the same line. Fixed by requiring proximity: a redirect only counts if its
own target references `RAG/`, and `rm`/`mv`/`truncate`/`shred` only count
if `RAG/` appears in the same shell sub-command (split on `;`/`&&`/`||`/`|`),
not just somewhere in a longer multi-part command. Still not real shell
parsing — the same prose-vs-invocation gap above still applies — but this
closes the specific "unrelated redirect elsewhere in the line" false
positive that block_destructive_bash.py's `rm -rf` fix (see git history)
didn't cover, since that was a different pattern.
