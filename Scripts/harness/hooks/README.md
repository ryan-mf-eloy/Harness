# Scripts/harness/hooks/

Enforcement hooks. Each one is deterministic — it runs regardless of what
the model decides, unlike `principles/PRINCIPLES.md`, which is only ever
advisory context. They're split across two settings scopes depending on
whether the check depends on this repo's own files:

| Script | Event | Matcher | Wired in | Purpose |
|---|---|---|---|---|
| `block_destructive_bash.py` | `PreToolUse` | `Bash` | `~/.claude/settings.json` (global — no dependency on any specific project's files) | Deny known-destructive command patterns (force-push to main, `reset --hard`, `rm -rf` on root/home, `--no-verify`) — redundant with `permissions.deny` on purpose, defense in depth |
| `check_tests_and_revalidation.py` | `Stop` | — | `~/.claude/settings.json` (global) | Block ending the turn if files changed but no test command was observed, unless an explicit `<no-tests-required: ...>` marker is present |
| `../guard_rag_immutable.py` | `PreToolUse` | `Write\|Edit\|MultiEdit\|Bash` | this repo's own `.claude/settings.json` (project-scoped — only meaningful when the working directory is this repo) | Deny edits under `RAG/` (see `RAG/README.md`) |
| `../index_upsert.py` | `PostToolUse` | `Write\|Edit\|MultiEdit` | this repo's own `.claude/settings.json` (project-scoped) | Incrementally reindex a changed file if it's under `Vault/` or `RAG/` |

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
