# Codebase

Real project repositories are **not** cloned or nested inside this folder.
They stay wherever the user explicitly says to put them — **never inferred,
never searched for**. No agent should look inside any other folder on this
machine (`~/dev`, or anywhere else) to find or suggest a location; the path
always comes from the user, stated directly. This folder holds only
`REGISTRY.md`, an index pointing at wherever those explicitly-given paths
are.

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

Give the agent the project's slug, its absolute path, and a short project
overview (or ask for the `/onboard-project` skill directly) — never a
folder to go look in. The full procedure lives in `ONBOARDING.md` at this
repo's root: it writes/refreshes `AGENTS.md` (principles stamped in, and
pre-filled from the overview wherever the overview gives real signal),
`CLAUDE.md`, `.cursorrules`, and `.claude/settings.json`
(`autoMemoryDirectory` pointed at `Vault/40-Memory/<slug>/`). Two things
still need a human, by design:

1. Add a row to `REGISTRY.md` (status/notes need a judgment call).
2. Confirm or refine whatever `AGENTS.md` sections the overview didn't give
   enough signal to pre-fill, and add any project-specific specialists to
   that project's own `.claude/agents/` — the harness-level roster in
   `~/.claude/agents/` is generic on purpose (see `claude/agents/`).
