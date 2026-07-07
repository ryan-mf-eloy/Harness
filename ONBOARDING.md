# Onboarding a New Project

This is the full procedure for wiring a new or existing project onto this
harness's conventions. Any tool — Claude Code, Cursor, Codex CLI, or a human
reading this directly — can follow it start to finish using only Read/Write/
Edit and a shell; nothing here requires running a script. Claude Code users
can also trigger this via the `/onboard-project` skill, which is a thin
pointer back to this exact file — do not duplicate these steps there.

## Step 1 — Get the project overview, slug, and absolute path

Ask for, or confirm from what's already been said:

- **A short project overview** — what the system does, who it's for, and
  (if known yet) its tech stack/architecture in a sentence or two. This is
  the input Step 5 uses to pre-fill `AGENTS.md` — the more concrete this
  is, the more of that file can be drafted now instead of left as a
  placeholder.
- **A slug** — a short kebab-case identifier for the project. Don't guess
  one; ask if it wasn't stated.
- **An absolute path** to the project's root directory. This path must be
  **outside this harness repo** — never `Codebase/<slug>/` inside it. See
  `Codebase/README.md`: Claude Code discovers `CLAUDE.md`/`.claude/agents/`/
  `.claude/skills/`/`.mcp.json` by walking *up* the directory tree from the
  working directory, so nesting a project inside `Harness/Codebase/<slug>/`
  would leak this harness's own `AGENTS.md`/`CLAUDE.md`/`.cursorrules` into
  that project's own sessions.

## Step 2 — Determine new vs. existing project

Check whether the given path already exists:

- **If it exists** and has real files in it (or is already a git repo):
  this is an existing project. Continue to Step 3 directly.
- **If it doesn't exist yet**: this is a brand-new project. Confirm with
  the user before creating anything, then run:
  ```bash
  mkdir -p <path> && git init <path>
  ```
  Do **not** scaffold a specific tech stack here (no `npm create`, `cargo
  new`, framework boilerplate, etc.) — that is the user's own decision.
  If the overview from Step 1 didn't name a stack, ask; don't default to
  one. Scaffolding an actual stack, if wanted, is a separate explicit task
  after onboarding, not part of this procedure.

## Step 3 — Write or refresh `AGENTS.md`

**If `<path>/AGENTS.md` does not exist yet:**

1. Read `templates/AGENTS.md.template` from this harness repo.
2. Replace its `<Project Name>` placeholder with the slug from Step 1.
3. Continue to the principles-stamping step below before writing the file.

**If `<path>/AGENTS.md` already exists:**

1. Read the existing file. Only the stamped principles block (below) gets
   refreshed — every other section is left exactly as it is.

### Stamping the principles block (exact procedure, do this precisely)

The templated/existing `AGENTS.md` contains this pair of markers:

```
<!-- AGENT-PRINCIPLES:BEGIN
     ...explanatory comment text...
     -->
<!-- AGENT-PRINCIPLES:END -->
```

To stamp the current principles in:

1. Read `principles/PRINCIPLES.md` from this harness repo fresh (not from
   memory — it may have changed since this procedure was last run). Strip
   any leading/trailing blank lines from its content.
2. In the target `AGENTS.md` text, find the **closing `-->`** of the
   `AGENT-PRINCIPLES:BEGIN` comment block (the first `-->` that appears
   after the `<!-- AGENT-PRINCIPLES:BEGIN` marker — the marker's own
   explanatory comment spans multiple lines before that `-->`).
3. Find the `<!-- AGENT-PRINCIPLES:END -->` marker.
4. Replace everything between the end of that closing `-->` (step 2) and
   the start of the END marker (step 3) with: a blank line, the full
   `principles/PRINCIPLES.md` content from step 1, then another blank
   line. Leave the BEGIN comment itself and the END marker untouched —
   only the content *between* them changes.
5. If a target `AGENTS.md` has no `AGENT-PRINCIPLES:BEGIN`/`:END` markers
   at all (a hand-written file predating this convention), do not
   fabricate them silently — surface this to the user and ask whether to
   add the markers block from `templates/AGENTS.md.template` before
   stamping, since inserting an unrequested structural block into a file
   someone else wrote is exactly the kind of invention Step 5 below warns
   against.

Write the resulting text to `<path>/AGENTS.md`.

## Step 4 — Write `CLAUDE.md` and `.cursorrules` (new projects only)

These are **never overwritten** if they already exist — only written when
absent:

- If `<path>/CLAUDE.md` does not exist: read `templates/CLAUDE.md.template`
  from this harness repo and write it verbatim to `<path>/CLAUDE.md`.
- If `<path>/.cursorrules` does not exist: write the literal text
  `See AGENTS.md.\n` to `<path>/.cursorrules`.

## Step 5 — Pre-fill `AGENTS.md` from the project overview

This is where the overview from Step 1 gets used, calibrated as follows:
**draft whatever the overview actually supports; leave everything else as
an explicit placeholder or TODO — never invent a detail the overview
didn't state or clearly imply.** This mirrors
`templates/AGENTS.md.template`'s own instruction ("Do not invent specifics;
leave a section blank or marked TODO rather than guessing") — it is not a
license to guess a stack, path, or command that wasn't actually given.

Concretely, in the `AGENTS.md` written in Step 3:

- **System Overview** — always draft this from the overview text directly;
  a one-paragraph project description is exactly what was given in Step 1.
- **Where to Modify**, **Validation**, **Safety Rules** — draft a
  first-pass guess **only if** the overview names or clearly implies a
  concrete stack or structure (e.g. "a Next.js + Postgres app," "a Python
  CLI tool," "a monorepo with a `packages/` layout"). A stated stack gives
  real signal for likely directory conventions (e.g. `app/` or `src/` for
  Next.js, `migrations/` for a Postgres-backed app) and likely validation
  commands (e.g. `npm run lint && npm test` for a Node stack) — draft
  those as a labeled first pass, not a placeholder.
- Anything the overview gives **no real signal for** — a validation
  command for a stack that wasn't named, a specific auth/API path with no
  hint of the actual layout, an Infrastructure & Environments row with no
  named provider — stays the template's own placeholder/TODO text
  unchanged. Do not fabricate a plausible-sounding path or command to make
  a section look complete.
- If uncertain whether a given overview detail is "real signal" or a
  stretch, treat it as insufficient signal and leave the placeholder — the
  cost of an under-filled section (a human fills it in later, same as
  today) is far lower than the cost of a wrong, confidently-stated
  assumption baked into a new project's own operating contract.

## Step 6 — Ensure the memory directory and `.claude/settings.json`

1. Ensure `Vault/40-Memory/<slug>/` exists inside this harness repo,
   creating it if not (this is where that project's Claude Code
   auto-memory will be written).
2. Check `<path>/.claude/settings.json`:
   - **If it does not exist:** read
     `templates/settings.permissions-baseline.json` from this harness
     repo, and write a new `<path>/.claude/settings.json` containing:
     - `"autoMemoryDirectory"`: the absolute path to
       `Vault/40-Memory/<slug>/` from step 1.
     - `"permissions"`: the exact `permissions` object copied from
       `templates/settings.permissions-baseline.json`, unmodified.
   - **If it already exists:** do **not** modify it. Instead, tell the
     user to review it by hand against
     `templates/settings.permissions-baseline.json` and add
     `"autoMemoryDirectory": "<absolute path to Vault/40-Memory/<slug>/>"`
     to it if that key is missing.

## Step 7 — Report the manual steps that remain

After the steps above, tell the user what still needs their input — don't
attempt these yourself, they need a human judgment call:

- Any `AGENTS.md` section left as a placeholder/TODO in Step 5 because the
  overview gave no real signal for it — point out which sections those
  are, so the user knows what's still outstanding.
- Add a row for `<slug>` to `Codebase/REGISTRY.md` in this harness repo
  (status and notes need a human judgment call, not a guessed default).
- Accept the workspace-trust dialog once, the first time a session opens
  inside the new project directory — required for `autoMemoryDirectory`
  to actually take effect.

## Step 8 — Don't speculatively add more than this

Do not add MCP servers, task-manager labels, or domain-specific subagents
as part of onboarding — those stay unconfigured until the project actually
needs them and the real tool/platform is known. See the commented
`mcpServers` placeholders in `claude/agents/data-analyst.md` /
`log-analyst.md` / `task-triage.md`. Once a tracker is chosen, pull its
real label/status taxonomy from its own MCP or CLI rather than inventing
one — `task-create` and `task-comment` already say so.

## Re-running this procedure

Running this again on an already-onboarded project only refreshes the
stamped principles block in Step 3 (since `AGENTS.md` already exists) and
leaves `CLAUDE.md`/`.cursorrules`/`.claude/settings.json` untouched (Steps
4 and 6 only write when the target file is absent). Step 5's pre-fill is
also skipped in that case — an already-onboarded project's `AGENTS.md`
sections are presumed to reflect real project knowledge already, not the
template's placeholders, so re-running this procedure must never overwrite
them.
