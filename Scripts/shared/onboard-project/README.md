# onboard-project

**What:** stamps the Harness's `AGENTS.md`/`CLAUDE.md`/`.cursorrules`
templates into a real project, with the full `principles/PRINCIPLES.md`
content physically copied into that project's own `AGENTS.md` — Cursor and
Codex CLI only read a project's own file, they don't follow cross-directory
imports, so the content has to live there directly, not just be linked to.

**When:** onboarding a new project onto the Harness conventions, or
refreshing an already-onboarded project's stamped principles block after
`principles/PRINCIPLES.md` changes.

**Invoke:**
```bash
python3 Scripts/shared/onboard-project/onboard.py <project-slug> <absolute-path-to-project-root>
```

**Depends on:** nothing beyond Python stdlib. Does not touch
`Codebase/REGISTRY.md` (that needs a human judgment call for status/notes)
or the project's own workspace-trust acceptance (a one-time manual step in
that project).
