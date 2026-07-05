---
name: Task Manager Culture
description: PLACEHOLDER — taxonomy of labels and statuses for the project's task manager (Jira/Linear/GitHub Issues/other). Not yet configured; contains fill-in instructions for a future project-scoped setup pass. Use when creating/labeling/transitioning tasks once a tracker is chosen and connected.
when_to_use: Any time a task needs a label or status set, after the target project's tracker has been chosen and its MCP connected — until then, this skill should surface itself as unconfigured rather than guessing.
user-invocable: false
---

## STATUS: UNCONFIGURED — project-specific setup required

This entire file is a placeholder. Do not invent a taxonomy to fill it —
follow the steps below when a real project needs this configured.

### Step 1 — Identify the tracker

Confirm which tool is actually in use: Jira, Linear, GitHub Issues, or
other. Check for an already-connected MCP server before assuming — don't
guess based on what's common.

### Step 2 — Pull the real taxonomy from the tool, don't invent one

- **Jira** — query the project's actual configured issue types, workflow
  statuses, and labels via the Jira/Atlassian MCP or admin UI. Real Jira
  projects customize this per project; don't assume a generic
  To-Do/In-Progress/Done workflow.
- **Linear** — query the team's actual configured workflow states and label
  set via the Linear MCP. Linear teams also customize per team.
- **GitHub Issues** — pull the repo's actual configured labels via
  `gh label list`.

### Step 3 — Populate this table (replace entirely with real values)

| Category | Value | Meaning | When to apply |
|---|---|---|---|
| _(TODO)_ | | | |

### Step 4 — Update this file's frontmatter

Remove "PLACEHOLDER" from the description once populated, and set
`user-invocable` based on whether this should be directly triggerable.

### Step 5 — Cross-link

Update the `task-create` and `task-comment` skills' notes (they currently
point back here) to reference the now-real taxonomy instead of "pending
setup."
