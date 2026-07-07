---
type: decision
tags: [harness, hooks, security]
status: active
created: 2026-07-06
---

# Add infra-mutation and remote-automation guard hooks, ported from a consuming project

## Context

While consolidating the Paketa project (a separate, pre-existing
agent-tooling workspace) onto this harness's conventions, its own
agent-tooling scaffolding turned out to have two deterministic hooks more
mature than anything this harness had:

1. A hook blocking cloud/IaC/Kubernetes/PaaS mutation commands and
   infra-mutating MCP tool calls (Cloudflare/Supabase/Vercel), regardless
   of what the model decides. This harness's only answer to infra-CLI
   safety before this change was `claude/skills/infra-cli-check/SKILL.md`
   — purely advisory guidance a model is instructed to follow, not a
   deterministic block — and `block_destructive_bash.py`, which is scoped
   to git/filesystem patterns only and has no infra/cloud coverage at all.
2. A hook blocking creation/editing of GitHub Actions workflow files unless
   explicitly approved, forcing local validation to be exhausted first.
   This harness had no equivalent of any kind, advisory or enforced.

Both of the source scripts emit the old JSON `hookSpecificOutput.permissionDecision`
envelope. `2026-07-05-cross-tool-hook-portability.md` already established
that this envelope is not understood by Cursor's flat `preToolUse` response
schema — which is exactly why `block_destructive_bash.py` uses exit-code-2
instead. Porting the two scripts as-is would have left Cursor sessions with
no protection from either guard, silently.

## Decision

1. Add two new global hooks, `Scripts/harness/hooks/guard_infra_mutation.py`
   and `Scripts/harness/hooks/guard_remote_automation.py`, carrying the
   source projects' detection logic (mutation-verb matching for cloud
   CLIs/IaC tools/Kubernetes/PaaS deploy platforms; workflow-file-path
   matching for the remote-automation gate) but converted to the
   exit-code-2-with-stderr-reason deny mechanism `block_destructive_bash.py`
   already uses — this conversion, not a literal port, is the actual
   design change here.
2. Keep both as separate files rather than folding either into
   `block_destructive_bash.py` — that script is scoped to git/filesystem
   patterns by design, and this repo's hook roster is otherwise
   one-concern-per-script throughout (`guard_rag_immutable.py`,
   `check_tests_and_revalidation*.py`, `reinforce_principles*.py`).
3. Keep `infra-cli-check` unmodified — it verifies the correct
   profile/account is active and collects human approval with a
   blast-radius statement for a classified mutation, neither of which a
   hook can do. The two layers are complementary, same "defense in depth"
   reasoning already documented for `block_destructive_bash.py` vs.
   `permissions.deny`.
4. Drop the source `guard_remote_automation.py`'s `ask`-vs-`deny` split
   (Claude got a softer "ask," Codex got "deny") — exit-code-2 has no
   "ask" tier, so every match is now a hard deny on all three tools. More
   conservative than the original Claude behavior, but consistent and
   actually portable everywhere.
5. Wire `guard_infra_mutation.py`'s direct MCP-tool-name matcher only into
   Claude Code's `~/.claude/settings.json` (via `MCP_INFRA_MUTATION_MATCHER`
   in `install.py`) — Cursor's and Codex's matcher engines are not
   confirmed to match arbitrary MCP tool-name regexes the same way Claude
   Code's does. Both still get full Bash/Shell coverage for the same
   patterns invoked via a shell command. Stated as a known asymmetry in
   `hooks/README.md` rather than guessed around.
6. Generalize both scripts' text to English and strip the specific
   originating-project citation (an internal PR-learning reference) from
   the remote-automation reason string, replacing it with a generic
   "exhaust local validation first" explanation. The mechanism travels;
   the specific evidence citation for why it was adopted does not — that
   stays in the originating project's own memory.

## Alternatives considered

- **Fold both into `block_destructive_bash.py`.** Rejected — that script's
  own docstring and this repo's hook-roster convention scope it to
  git/filesystem patterns specifically; adding two unrelated concerns would
  make it a kitchen-sink script and break the one-concern-per-script
  pattern every other hook in this repo already follows.
- **Keep the JSON `permissionDecision` envelope, since Claude Code and
  Codex both understand it.** Rejected — already proven non-functional on
  Cursor's flat response schema by the existing cross-tool-hook-portability
  ADR; silently leaving one of three tools unprotected is worse than a
  slightly more conservative deny-only mechanism that works everywhere.
- **Preserve the softer `ask` decision for Claude Code specifically, only
  hard-denying on Codex.** Rejected — exit-code-2 doesn't carry a
  decision-type payload, so there is no way to express "ask" through it;
  branching the deny mechanism per tool would reintroduce the exact
  per-tool JSON-shape complexity this repo's hooks deliberately moved away
  from.

## Consequences

- Every project on this machine now gets deterministic infra-mutation and
  remote-automation blocking automatically, once `Scripts/harness/install.py`
  has been re-run — not just Paketa, the project these were ported from.
- Two new global hook scripts to maintain going forward, each inheriting
  the same regex/string-matching limitations already documented for
  `block_destructive_bash.py` (no real shell/patch parsing; a deliberately
  obfuscated command can still escape, and a string literal merely
  mentioning a mutating verb as prose can still false-positive).
- Cursor and Codex CLI sessions have no equivalent of Claude Code's direct
  MCP-tool-name matcher for `guard_infra_mutation.py` — an infra-mutating
  MCP tool call issued directly (not via a shell command) on those two
  tools would not be caught by this hook. Accepted as a stated gap rather
  than an invented, unconfirmed mechanism; revisit if either tool's
  first-party docs later confirm MCP-tool-name matcher support.
- The remote-automation gate is a genuinely new capability class for this
  harness (no prior equivalent, advisory or enforced), not merely a merge
  of overlapping coverage.
