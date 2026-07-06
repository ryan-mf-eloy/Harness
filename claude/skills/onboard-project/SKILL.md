---
name: Onboard Project
description: Wires a new or existing project onto the Harness conventions — creates or refreshes its AGENTS.md (with engineering principles stamped in and pre-filled from a project overview where possible), CLAUDE.md, .cursorrules, and .claude/settings.json (autoMemoryDirectory pointed at the Harness vault). Use when the user wants to start a new project, has just cloned a repo they want the harness to manage, or asks how to set a project up with the harness conventions.
when_to_use: User says things like "let's start a new project", "iniciar um projeto", "onboard this repo onto the harness", or asks what to do to begin using the harness for a project.
argument-hint: "<project-slug> <absolute-path> [project overview]"
allowed-tools: Bash(git init*), Bash(ls*), Bash(readlink*), Bash(dirname*), Read, Write, Edit
---

Find `ONBOARDING.md` at the harness repo root — this skill may run from
inside a completely different project directory, so it cannot rely on
`${CLAUDE_PROJECT_DIR}` (which would resolve to that *other* project, not
the Harness). Instead, resolve the Harness's current root at runtime via
the `~/.claude/agents` symlink, which `Scripts/harness/install.py`
guarantees always points at `<harness-root>/claude/agents`:

```bash
HARNESS_ROOT="$(dirname "$(dirname "$(readlink -f ~/.claude/agents)")")"
```

Two `dirname` calls peel the resolved symlink target back from
`<harness-root>/claude/agents` to `<harness-root>` itself. Read
`"$HARNESS_ROOT/ONBOARDING.md"` and follow every step there directly using
Read/Write/Edit and Bash — do not duplicate its steps here, and do not
shell out to any script; there isn't one for onboarding a project (as
opposed to `install.py`, which sets up this harness's own global config
and is unrelated to onboarding other projects).

This makes the resolution above depend on `install.py` having been run at
least once on the current clone (so `~/.claude/agents` actually points at
it) — a reasonable dependency, since any session capable of invoking this
skill has almost certainly already run it.

If `$ARGUMENTS` is missing the slug, path, or project overview, ask for
whichever is missing before proceeding — `ONBOARDING.md`'s Step 1 covers
exactly what's needed and why.
