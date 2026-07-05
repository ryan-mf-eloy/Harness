---
name: Onboard Project
description: Wires a new or existing project onto the Harness conventions — creates or refreshes its AGENTS.md (with engineering principles stamped in), CLAUDE.md, .cursorrules, and .claude/settings.json (autoMemoryDirectory pointed at the Harness vault). Use when the user wants to start a new project, has just cloned a repo they want the harness to manage, or asks how to set a project up with the harness conventions.
when_to_use: User says things like "let's start a new project", "iniciar um projeto", "onboard this repo onto the harness", or asks what to do to begin using the harness for a project.
argument-hint: "<project-slug> <absolute-path>"
allowed-tools: Bash(git init*), Bash(python3*), Bash(ls*), Read, Write
---

The Harness repo lives at a fixed absolute path on this machine:
`/Users/larissamiyoshi/Library/CloudStorage/Dropbox/drive_sync/Personal/OpenSource/Harness`
(hardcoded here deliberately — this skill may run from inside a completely
different project directory, so it cannot rely on `${CLAUDE_PROJECT_DIR}`,
which would resolve to that *other* project, not the Harness).

## Steps

1. **Get the slug and the path.** If either is missing from `$ARGUMENTS`,
   ask for them — don't guess a slug or invent a path. The path must be
   **outside** the Harness repo itself (never `Codebase/<slug>/` — see
   `Codebase/README.md` for why: config discovery walks up the directory
   tree, and nesting a project inside the Harness would leak the Harness's
   own `AGENTS.md`/`CLAUDE.md`/`.cursorrules` into that project's sessions).

2. **Check whether the path already exists.**
   - If it exists and is already a git repo (or has real files in it): treat
     it as an existing project to onboard, proceed to step 3 directly.
   - If it doesn't exist yet: this is a brand-new project. Confirm with the
     user before creating anything (`mkdir -p <path> && git init <path>`).
     Do **not** scaffold a specific tech stack (no `npm create`, `cargo
     new`, framework boilerplate, etc.) — that's the user's own decision;
     ask what stack they want if they haven't said, and let them drive that
     part or ask for it as a separate, explicit task.

3. **Run the onboarding script:**
   ```bash
   python3 "/Users/larissamiyoshi/Library/CloudStorage/Dropbox/drive_sync/Personal/OpenSource/Harness/Scripts/shared/onboard-project/onboard.py" <slug> <path>
   ```
   This writes/refreshes `AGENTS.md` (principles stamped in verbatim),
   `CLAUDE.md`, `.cursorrules`, and `.claude/settings.json` with
   `autoMemoryDirectory` pointed at
   `Harness/Vault/40-Memory/<slug>/` (created if missing).

4. **Report the manual steps that are left** — these genuinely need a human
   judgment call, don't attempt to fill them in yourself:
   - Fill in the `AGENTS.md` placeholders (System Overview, Where to
     Modify, Validation commands, Safety Rules) with real project
     knowledge — do not invent these.
   - Add a row for `<slug>` to
     `/Users/larissamiyoshi/Library/CloudStorage/Dropbox/drive_sync/Personal/OpenSource/Harness/Codebase/REGISTRY.md`
     (status + notes need human judgment, not a guessed default).
   - Accept the workspace-trust dialog once, the first time a session
     opens inside the new project directory — required for
     `autoMemoryDirectory` to actually take effect.

5. Do not add MCP servers, task-manager labels, or domain-specific
   subagents speculatively — those stay unconfigured (see
   `claude/skills/task-manager-culture/SKILL.md` and the commented
   `mcpServers` placeholders in `claude/agents/data-analyst.md` /
   `log-analyst.md` / `task-triage.md`) until the project actually needs
   them and the real tool/platform is known.
