---
name: Onboard Project
description: Wires a new or existing project onto the Harness conventions — creates or refreshes its AGENTS.md (with engineering principles stamped in and pre-filled from a project overview where possible), CLAUDE.md, .cursorrules, and .claude/settings.json (autoMemoryDirectory pointed at the Harness vault). Use when the user wants to start a new project, has just cloned a repo they want the harness to manage, or asks how to set a project up with the harness conventions.
when_to_use: User says things like "let's start a new project", "iniciar um projeto", "onboard this repo onto the harness", or asks what to do to begin using the harness for a project.
argument-hint: "<project-slug> <absolute-path> [project overview]"
allowed-tools: Bash(git init*), Bash(ls*), Read, Write, Edit
---

See `ONBOARDING.md` at the harness repo root
(`/Users/larissamiyoshi/Library/CloudStorage/Dropbox/drive_sync/Personal/OpenSource/Harness/ONBOARDING.md`,
hardcoded here deliberately — this skill may run from inside a completely
different project directory, so it cannot rely on `${CLAUDE_PROJECT_DIR}`,
which would resolve to that *other* project, not the Harness) for the full
onboarding procedure. Follow every step there directly using Read/Write/
Edit and Bash — do not duplicate its steps here, and do not shell out to
any script; there isn't one anymore.

If `$ARGUMENTS` is missing the slug, path, or project overview, ask for
whichever is missing before proceeding — `ONBOARDING.md`'s Step 1 covers
exactly what's needed and why.
