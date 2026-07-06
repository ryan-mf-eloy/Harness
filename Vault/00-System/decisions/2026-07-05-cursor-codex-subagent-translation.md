---
type: decision
tags: [harness, cursor, codex, skills, subagents, provider-agnostic]
status: active
created: 2026-07-05
---

# Bring skills and subagents to Cursor and Codex CLI via each tool's real discovery convention

## Context

`claude/agents/*.md` and `claude/skills/*/SKILL.md` were Claude-Code-only in
practice, even though this harness is meant to be provider-agnostic by
construction. Verified directly against each tool's current first-party
docs this session (not assumed from training-data memory, which was stale
on this specific point):

- Skills have a genuinely open, unified standard: agentskills.io (the
  "Agent Skills" spec, originated by Anthropic/Claude Code, now adopted by
  30+ tools). The same `SKILL.md` file works identically across tools —
  Cursor scans `.cursor/skills/` and `.agents/skills/` (project + user
  level), Codex CLI scans `.agents/skills/` at every directory from cwd up
  to repo root plus `$HOME/.agents/skills`. No translation is needed, only
  discovery-path reach.
- Subagents have no such standard. Claude Code, Cursor, and Codex CLI each
  define their own file location (`claude/agents/`, `.cursor/agents/`,
  `.codex/agents/`) AND their own file format (Markdown+YAML with a
  tools-allowlist/model/memory/color scheme; Markdown+YAML with a
  5-field readonly/background scheme; TOML with `developer_instructions`
  and `sandbox_mode`, respectively) — these are not interchangeable
  without content-level translation.
- `.agents/agents/` is not read by any confirmed tool — considered and
  rejected as a fabricated convention with no real backing.

## Decision

Two different mechanisms for two different facts:

1. **Skills**: extend reach only, via the harness's existing
   symlink-for-global-reach pattern (already used for
   `principles/PRINCIPLES.md` and `claude/agents`/`claude/skills`) — add
   `.agents/skills` (project-local, this repo) and `~/.agents/skills`
   (global) as new symlinks to the existing `claude/skills`. No new
   content, no format change.
2. **Subagents**: translate the existing 7 `claude/agents/*.md` files into
   genuinely new, hand-authored `.cursor/agents/*.md` and
   `.codex/agents/*.toml` files — one new canonical file per tool per
   subagent — reached via new symlinks mirroring the same
   `~/.claude/agents` pattern (`~/.cursor/agents`, `~/.codex/agents`).
   `claude/agents/*.md` and `claude/skills/*/SKILL.md` themselves are left
   completely unmodified; this is pure addition.

## Alternatives considered

- **Duplicate `claude/agents/*.md` content three times with light edits.**
  Rejected — this misrepresents the situation as "the same file with minor
  syntax differences" when the underlying capabilities are genuinely
  different (Cursor's binary `readonly` flag versus Claude's per-tool
  allowlist; Codex's `sandbox_mode` versus either). A light edit would
  either silently drop real behavior (memory, fine-grained tool scoping)
  or falsely imply it's still present.
- **Skip subagent translation entirely, unify skills only.** Rejected per
  explicit request — skills genuinely have an open standard behind them;
  subagents don't, but the user asked to translate now rather than defer,
  accepting the capability-gap cost documented in Consequences below.
- **Invent a shared `.agents/agents/` convention as a new de facto
  standard.** Rejected — not read by any confirmed tool today; inventing
  an unconfirmed path contradicts this harness's own standing principle of
  not guessing at unverified integration surfaces.
- **Guess at Codex's `skills.config` TOML sub-schema to give the 4
  skill-referencing subagents a first-class Codex skills wiring.**
  Rejected for now — the sub-schema was not confirmed from the docs
  fetched this session (only that it's "an array" for "skill
  definitions"). Skill references are carried in `developer_instructions`
  prose instead, the same safe choice made for Cursor. Revisit if Codex's
  `skills.config` schema gets confirmed later.

## Consequences

- Real capability is lost in translation, not just syntax, and this is
  stated plainly in each translated file rather than hidden:
  - Cursor subagents collapse Claude's fine-grained `tools:`/
    `disallowedTools:` allowlist into a single binary `readonly` flag.
  - Neither Cursor's nor Codex's subagent format has a documented
    persistent-memory field — the `memory: project`/`memory: user`
    behavior on 4 of the 7 Claude Code subagents (`data-analyst`,
    `debugger`, `log-analyst`, `risk-analyst`) does not carry over to
    either translation.
  - Codex subagents gain `sandbox_mode` (a real OS-level enforcement
    Claude Code's `tools:` allowlist doesn't have) but lose the
    fine-grained tool-by-tool scoping Claude Code has.
- Three sources of truth now exist per subagent instead of one. A future
  edit to a subagent's behavior (e.g. changing what `debugger` does) must
  be applied to `claude/agents/debugger.md`, `.cursor/agents/debugger.md`,
  and `.codex/agents/debugger.toml` separately — there is no single-file
  source generating all three. This is an accepted, deliberate cost of
  "translate now" versus deferring.
- `AGENTS.md`'s "Provider-agnostic by construction" section required a
  correction alongside this change: its prior claim that "there is no
  equivalent mechanism yet in Codex CLI" for `claude/`'s packaging became
  false the moment `.codex/agents/*.toml` exists.
