---
type: reference
tags: [vault, memory]
status: active
created: 2026-07-05
---

# 40-Memory

This is where Claude Code's native auto-memory gets redirected to, per
project. It is **written by Claude, not by you** — do not hand-edit these
files as your primary way of adding context; use `10-Projects/<slug>/`
for that instead.

## How the redirect works

In a project's own `.claude/settings.json` (or `.claude/settings.local.json`):

```json
{ "autoMemoryDirectory": "/absolute/path/to/Harness/Vault/40-Memory/<project-slug>" }
```

Claude Code will then write `MEMORY.md` (and any topic files it creates,
e.g. `debugging.md`) directly into `40-Memory/<project-slug>/` instead of the
default hidden location (`~/.claude/projects/<repo-hash>/memory/`). It's the
exact same mechanism and the exact same file Claude reads at the start of
every session — just pointed somewhere you can see it, tag it, link it from
your own notes, and have it indexed by the FTS index alongside everything
else.

Before first use in a new project: `mkdir -p 40-Memory/<project-slug>/` and
accept the workspace-trust dialog once in that project (the setting is only
honored in a trusted workspace).
