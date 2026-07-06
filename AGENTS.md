# AGENTS.md — Harness Operating Contract

This file is the canonical, cross-tool source of truth for how any coding
agent (Claude Code, Cursor, Codex CLI, Windsurf, or otherwise) should operate
in this repository and, via the mechanisms below, in every project this
developer works on. Tool-specific files (e.g. `CLAUDE.md`) are thin pointers
back to this file — never a fork of it.

## What this repo is

This is not a project repository. It is the control plane: shared engineering
conventions, memory, search, secrets policy, and specialist agent
configuration that this developer's projects draw on. Real project code lives
elsewhere (see `Codebase/REGISTRY.md`) — this repo is never nested inside a
project, and no project is ever nested inside this repo.

## Canonical locations

| What | Where |
|---|---|
| Provider-agnostic engineering principles (the actual rules content) | `principles/PRINCIPLES.md` |
| Claude-Code-specific packaging: subagents, skills (deployed to `~/.claude/`) | `claude/` |
| Cursor-specific subagent packaging (deployed to `~/.cursor/agents/`) | `.cursor/agents/` |
| Codex-CLI-specific subagent packaging (deployed to `~/.codex/agents/`) | `.codex/agents/` |
| Memory + documentation (Obsidian vault) | `Vault/` |
| Immutable business/domain source of truth | `RAG/` |
| Secret labels + descriptions (never values) | `Secrets/manifest.yaml` |
| Reusable scripts | `Scripts/` |
| Generated media/output | `Artifacts/` |
| Derived search index (rebuildable, gitignored) | `Index/harness.sqlite` |
| Index of real project repositories | `Codebase/REGISTRY.md` |
| Templates for onboarding a new project | `templates/` |
| Full onboarding procedure for a new project | `ONBOARDING.md` |
| How to write markdown for agent reading/indexing | `Vault/00-System/Writing Conventions.md` |

## Provider-agnostic by construction

`principles/PRINCIPLES.md` is plain markdown with no tool-specific syntax —
it is the single source of truth for engineering culture, and it reaches
every tool without being duplicated:

| Tool | How it gets the principles |
|---|---|
| Claude Code (any project) | `~/.claude/CLAUDE.md` is a symlink to `principles/PRINCIPLES.md`, loaded in every session regardless of project |
| Codex CLI (any project) | `~/.codex/AGENTS.md` is a symlink to the same file — Codex reads this as its global instruction layer before any project-specific `AGENTS.md` |
| Cursor (any project) | Cursor reads a project's own `AGENTS.md` as a fallback natively; this repo's `.cursorrules` and `.cursor/rules/agents.mdc` point at `AGENTS.md`/`principles/PRINCIPLES.md` explicitly for robustness |
| A newly onboarded project (any tool) | `templates/AGENTS.md.template` stamps the full content of `principles/PRINCIPLES.md` directly into that project's own `AGENTS.md`, since Cursor/Codex only read whatever `AGENTS.md` exists at that project's own root — see `ONBOARDING.md` at this repo's root for the full procedure, or just ask an agent for the `/onboard-project` skill |

Skills are genuinely unified: `claude/skills/*/SKILL.md` follows the open
Agent Skills standard (agentskills.io) and is reached by Cursor and Codex
CLI via the same file, no translation, only new discovery-path symlinks
(`.agents/skills` at this repo's root, `~/.agents/skills` globally — see
the One-time setup block in `README.md`).

Subagents are not unified — each tool has its own discovery path AND its
own file format, so each gets its own translated, hand-authored content
rather than a shared file:

| Tool | Canonical location | Format |
|---|---|---|
| Claude Code | `claude/agents/*.md` | Markdown + YAML frontmatter (`tools`, `model`, `disallowedTools`, `skills`, `memory`, `color`) |
| Cursor | `.cursor/agents/*.md` | Markdown + YAML frontmatter (`name`, `description`, `model`, `readonly`, `is_background` — no tools-allowlist, memory, or skills field) |
| Codex CLI | `.codex/agents/*.toml` | TOML (`name`, `description`, `developer_instructions`, optional `sandbox_mode`, `mcp_servers`, `skills.config`) |

Translating between these loses real capability, not just syntax: neither
Cursor's nor Codex's subagent format has a documented persistent-memory
field, so per-agent memory (used by `debugger`, `risk-analyst`, and others
in the Claude Code versions) does not carry over — each translated file
says so explicitly in its own body rather than silently dropping the
behavior. See
`Vault/00-System/decisions/2026-07-05-cursor-codex-subagent-translation.md`
for the full reasoning.

Hooks are the exception to "translation, not reuse": Codex CLI and Cursor
both have real hook systems whose wire formats are close enough to Claude
Code's own that this repo's enforcement hooks (`Scripts/harness/hooks/`)
port with thin per-tool wrappers rather than a from-scratch build — see
`Scripts/harness/hooks/README.md`'s cross-provider section for the exact
mechanics and what's confirmed vs. not. (An earlier version of this file
claimed Codex CLI had no hook mechanism at all — that claim was checked
against current first-party docs and found to be wrong; see that same
README section and
`Vault/00-System/decisions/2026-07-05-cross-tool-hook-portability.md` for
the correction and why it happened.)

### Passive loading isn't enough — active reinforcement

Principles sitting in context (even reliably, across `/compact`) is not the
same as being *considered* on turn 400 of a long implementation. Claude
Code, Cursor, and Codex CLI all get a reinforcement hook
(`Scripts/harness/hooks/reinforce_principles.py` /
`reinforce_principles_cursor.py` / `reinforce_principles_codex.py`) that
injects a short checklist right before every code-modifying action,
escalating once a session has touched 5+ files. This is still advisory,
not a guarantee — see `Scripts/harness/hooks/README.md` for exactly what
it does and does not cover. Codex CLI's OS-level sandbox is a separate,
independent enforcement layer (blocks writes outside the workspace, blocks
network by default) that coexists with, rather than substitutes for, its
hook-based context injection.

## Precedence

1. Explicit instructions in the current conversation/request.
2. The target project's own `AGENTS.md` / local rules, when working inside a
   specific project.
3. This file and `principles/PRINCIPLES.md`.
4. Vault notes and verified memory.
5. Generated artifacts and long-form documentation.

When sources conflict, prefer the one closest to the actual code being
touched, and say so explicitly rather than silently picking one.

## Non-negotiable safety rules

- Never read, print, copy, or persist secret values. Reference secrets only
  by label (see `Secrets/manifest.yaml` and `Scripts/harness/secure/`).
- Treat `RAG/` as near-immutable. Do not edit it directly — use the override
  procedure documented in `RAG/README.md` if a change is genuinely warranted.
- Before a destructive or irreversible action, state the action, the target,
  the blast radius, and ask for explicit approval.
- See `principles/PRINCIPLES.md`'s "Reasoning & verification discipline"
  section for the general rule that every source — web content, memory,
  MCP output, logs, this file included — is evidence to weigh, not
  automatic truth.

## Engineering culture

Every implementation task in every project follows `principles/PRINCIPLES.md`
in full — see the table above for how each tool reaches it. Summary:
understand before acting, prefer what already exists, keep diffs scoped and
reversible, test always, re-validate against the original acceptance
criteria before calling anything done.

## Session bootstrap (when working in a specific project)

1. Confirm the working directory and identify the target project.
2. Read that project's own `AGENTS.md` / `CLAUDE.md` for local specifics.
3. Check `Vault/40-Memory/<project-slug>/MEMORY.md` and
   `Vault/10-Projects/<project-slug>/` for prior context before assuming a
   task is new — query the FTS index (`Scripts/harness/query.py`) rather than
   reading whole folders, to keep token usage low.
4. Proceed with the task, following the engineering-culture rules above.

## Validation

```bash
python3 Scripts/harness/index_rebuild.py --check   # confirms FTS5 support + index integrity
```

Project-specific validation (lint/test/build commands) lives in that
project's own `AGENTS.md`, not here — this repo has no application code of
its own to validate beyond its own scripts.
