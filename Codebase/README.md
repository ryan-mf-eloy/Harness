# Codebase

Real project repositories are **not** cloned or nested inside this folder.
They stay wherever they naturally live on disk (another folder, `~/dev/`,
wherever). This folder holds only `REGISTRY.md`, an index pointing at them.

## Why not nest them here

Claude Code discovers `CLAUDE.md`, `.claude/agents/`, `.claude/skills/`, and
`.mcp.json` by walking **up** the directory tree from the current working
directory. If a project repo were nested inside `Harness/Codebase/<slug>/`,
opening a session inside it would walk up through `Harness/Codebase/` and
`Harness/` itself, silently pulling this repo's own instructions and
tool-config into what should be an isolated project session — precisely the
cross-scope confusion this harness exists to prevent. Keeping project repos
physically separate, and reaching them only through `~/.claude/` (personal
scope, loads in every session regardless of directory) or through each
project's own `.mcp.json`/`.claude/agents/` is the mechanism that actually
guarantees isolation.

## Onboarding a new project

1. Add a row to `REGISTRY.md`.
2. Copy `templates/AGENTS.md.template` and `templates/CLAUDE.md.template`
   into the project's root, filling in the placeholders.
3. In that project's `.claude/settings.json`, set `autoMemoryDirectory` to
   `Vault/40-Memory/<slug>/` (absolute path) and `mkdir -p` that folder first.
4. Add any project-specific specialists to that project's own
   `.claude/agents/` — the harness-level roster in `~/.claude/agents/` is
   generic on purpose (see `claude/agents/`).
