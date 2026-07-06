# Scripts/harness/hooks/

Enforcement hooks. Each one is deterministic — it runs regardless of what
the model decides, unlike `principles/PRINCIPLES.md`, which is only ever
advisory context. They're split across two settings scopes depending on
whether the check depends on this repo's own files:

| Script | Event | Matcher | Wired in | Purpose |
|---|---|---|---|---|
| `block_destructive_bash.py` | `PreToolUse` | `Bash` (Claude Code/Codex CLI), `Shell` (Cursor) | `~/.claude/settings.json`, `~/.cursor/hooks.json`, `~/.codex/hooks.json` — all global, no dependency on any specific project's files | Deny known-destructive command patterns (force-push to main, `reset --hard`, `rm -rf` on root/home, `--no-verify`) — redundant with `permissions.deny` on purpose, defense in depth |
| `check_tests_and_revalidation.py` | `Stop` | — | `~/.claude/settings.json` (global) | Block ending the turn if files changed but no test command was observed, unless an explicit `<no-tests-required: ...>` marker is present |
| `check_tests_and_revalidation_codex.py` | `Stop` | — | `~/.codex/hooks.json` (global) | Same as above, for Codex CLI — shares detection logic with the Claude Code variant via `_revalidation_common.py` |
| `reinforce_principles.py` | `SessionStart` | — | `~/.claude/settings.json` (global) | Once per session/resume, points at the mechanism (principles auto-loaded + per-edit checklist) — does not repeat `principles/PRINCIPLES.md` content, since that's already loaded separately and repeating it would just waste tokens |
| `reinforce_principles.py` (same script, branches on `hook_event_name`) | `PreToolUse` | `Edit\|Write\|MultiEdit` | `~/.claude/settings.json` (global) | Injects a short reuse/diff-size/testing/blast-radius checklist as `additionalContext` before **every** code-modifying action — this is the actual answer to "principles must always be considered during changes": reinforcement frequency scales up with implementation size instead of decaying over a long session. Escalates its message once a session has touched 5+ distinct files, nudging toward `pre-change-impact-check` |
| `reinforce_principles_codex.py` | `SessionStart` + `PreToolUse` (`apply_patch\|Edit\|Write`) | — | `~/.codex/hooks.json` (global) | Same as `reinforce_principles.py`, for Codex CLI — shares message text via `_reinforcement_common.py` |
| `../guard_rag_immutable.py` | `PreToolUse` | `Write\|Edit\|MultiEdit\|Bash` (Claude Code), `Write\|Edit\|Delete` + `Shell` (Cursor), `apply_patch\|Edit\|Write` + `Bash` (Codex) | this repo's own `.claude/settings.json`, `.cursor/hooks.json`, `.codex/hooks.json` (project-scoped — only meaningful when the working directory is this repo) | Deny edits under `RAG/` (see `RAG/README.md`) |
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

`ONBOARDING.md` (this harness repo's root) has an agent seed a
newly-created project's `.claude/settings.json` with
`templates/settings.permissions-baseline.json`'s `permissions` block
directly, following that file's Step 6 — it does not carry the hooks
above, since those are either global already (no copy needed) or specific
to this repo's own `RAG/`/`Vault/` paths (not meaningful in another
project). If that project already had a `settings.json` before onboarding,
the merge is skipped (existing files are never overwritten) — the agent is
instructed to tell the user to review the baseline by hand in that case.

## Cross-provider: Cursor and Codex CLI

Cursor's and Codex CLI's hook wire formats are close enough to Claude
Code's own that most of this repo's hooks port with thin per-tool wrappers,
not from-scratch reimplementations — confirmed directly against each
tool's first-party docs (`https://cursor.com/docs/agent/hooks`,
`https://developers.openai.com/codex/hooks`).

**A previous version of this section stated Codex CLI had no hook
mechanism at all, on the theory that its enforcement was purely an
OS-level sandbox. That was wrong.** Codex CLI has a real, general-purpose
hook system (added around v0.117.0) whose event names (PascalCase:
`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, etc.), config shape
(`{"hooks": {"PreToolUse": [{"matcher": ..., "hooks": [{"type": "command",
"command": ...}]}]}}`), and several field names (`tool_name`,
`tool_input`, `transcript_path`, `hookSpecificOutput.additionalContext`)
are close enough to Claude Code's own that this was not a from-scratch
reinvention on OpenAI's part. See
`Vault/00-System/decisions/2026-07-05-cross-tool-hook-portability.md` for
the full correction and why the original claim happened.

### The exit-code-2 convention

`block_destructive_bash.py` and `guard_rag_immutable.py` are pure
allow/deny hooks (no context injection, no input rewriting), which makes
them genuinely portable: both now use **exit code 2 with the reason on
stderr** as their only deny mechanism, dropping the
`hookSpecificOutput`/`permissionDecision` JSON they used to emit. This is
the one deny convention confirmed identical, first-party documented,
across all three tools:

| Tool | Exit-2-as-deny confirmed via |
|---|---|
| Claude Code | Public docs; the alternative to the `hookSpecificOutput` JSON envelope |
| Codex CLI | `https://developers.openai.com/codex/hooks`, explicitly listed as an alternative to the JSON envelope |
| Cursor | `https://cursor.com/docs/agent/hooks`: "Exit code 2 - Block the action, equivalent to returning permission: deny" |

The `hookSpecificOutput` JSON path was **not** chosen, even though Claude
Code and Codex both understand it, because Cursor's `preToolUse` response
is a flat schema (`{"permission": "deny", ...}`) with no nested envelope
at all — sending the nested JSON to Cursor would silently fail to deny
(Cursor looks for the `permission` key, not `hookSpecificOutput`), which
is the one tool where a silent no-op on the deny path is least acceptable.
Exit-2 alone satisfies all three with zero per-tool branching in the
script body.

Both scripts also now recognize Codex's and Cursor's own tool-name values
where they differ from Claude Code's: Codex reports `tool_name:
"apply_patch"` for every file edit (never `Edit`/`Write`/`MultiEdit`, even
though the `hooks.json` `matcher` string can still be written as
`apply_patch|Edit|Write` — the matcher is lenient, the runtime value is
not), and Cursor reports `tool_name: "Shell"` for shell commands (not
`Bash`). Both scripts branch on the union of tool names rather than only
Claude Code's, with defensive fallbacks across candidate field names
(`file_path`/`path`, `command`/`cmd`) since the exact key isn't confirmed
identical on every tool.

### Wiring

| Script | This repo's own `.cursor/hooks.json` / `.codex/hooks.json` | Global `~/.cursor/hooks.json` / `~/.codex/hooks.json` |
|---|---|---|
| `guard_rag_immutable.py` | Yes — project-scoped, only meaningful for this repo's own `RAG/` | No |
| `block_destructive_bash.py` | No | Yes — global/no-project-dependency, mirrors its `~/.claude/settings.json` wiring |
| `reinforce_principles_codex.py` | No | Yes (Codex only; already covered for Cursor by `reinforce_principles_cursor.py`) |
| `check_tests_and_revalidation_codex.py` | No | Yes (Codex only; no Cursor variant exists — out of scope for this pass) |

This mirrors the existing Claude Code split exactly: this repo's own
project-scoped `.claude/settings.json` carries only the RAG guard and the
index-upsert hook, while the destructive-bash guard and the
reinforcement/Stop hooks are global in `~/.claude/settings.json` — same
reasoning carried into the new files rather than collapsed.

**Unresolved, stated rather than guessed around:** it is not confirmed
whether Codex CLI performs `${CLAUDE_PROJECT_DIR}`-style variable
substitution inside a `.codex/hooks.json` `command` string. This repo's
own project-scoped `.codex/hooks.json` uses `${CLAUDE_PROJECT_DIR}`
tentatively — verify empirically (a trivial hook that echoes `pwd`) before
treating that file as final; if it doesn't substitute, it needs a literal
absolute path instead, same as the global hooks below already require.

### Reinforcement mechanism

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
- **Codex CLI**: `reinforce_principles_codex.py` joins the Claude Code and
  Cursor wrappers, wired into `~/.codex/hooks.json`. Codex's `SessionStart`
  and `PreToolUse` events both confirmed to support
  `hookSpecificOutput.additionalContext` — the same output shape Claude
  Code uses — so this wrapper is a genuinely thin one, not a fork of the
  message text. The one uncertainty: the exact key inside `apply_patch`'s
  own `tool_input` that names the edited file is not independently
  confirmed to be `file_path` (Claude Code's own key name) — the script
  defensively checks a short list of candidate keys and degrades
  gracefully (still emits the reminder, without per-file escalation
  tracking) rather than guessing one key and silently emitting nothing if
  wrong.

### check_tests_and_revalidation.py — now has a Codex variant

Codex's `Stop` event payload **does** include `transcript_path` (confirmed,
`string | null`, a common field extended to `Stop` — this was an open
question during design, resolved as present, not a gap). Shared detection
logic (what counts as "a file changed," "a test command ran," the
escape-hatch marker regex) now lives in `_revalidation_common.py` so the
Claude Code and Codex wrappers can't disagree on what triggers a block —
only the stdin/stdout framing differs, and that framing turns out
identical for the block response itself (`{"decision": "block", "reason":
"..."}`, the same shape on both tools, per Codex's own docs calling this
the "legacy format").

One residual, explicitly unverified gap, stated rather than silently
assumed: the exact byte-level content Codex writes to the file at
`transcript_path` was not confirmed in this session (unlike the field's
existence, which was). The shared detector includes an `apply_patch`
tool-name-marker variant as a defensive hedge against Codex's transcript
format differing from Claude Code's JSONL shape, but this is a guess, not
a verified match. If this hook is ever observed to never fire on Codex
despite real file edits happening, capture one real `transcript_path`
file's actual content and adjust `_revalidation_common.py`'s
`EDIT_TOOL_NAME_MARKERS` accordingly — the same troubleshooting path
`reinforce_principles_cursor.py`'s own docstring already prescribes for
its analogous Cursor gap.

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
