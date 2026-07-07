---
name: Task Create
description: Drafts a well-formed task/ticket (title, description, acceptance criteria, size estimate) ready to paste into or create directly in the project's task manager. Use when asked to create a task, ticket, or issue for new work.
when_to_use: User asks to create a task/ticket/issue, or a piece of work needs to be tracked before or instead of being implemented immediately.
argument-hint: "<short description of the work>"
user-invocable: true
---

1. **Title** — imperative, under ~70 characters, no ticket-key prefix (the
   tracker assigns that).
2. **Description structure:**
   - *Context* — why this exists.
   - *Scope* — what's in, what's explicitly out.
   - *Acceptance Criteria* — a testable checklist. This should be the same
     checklist used to close the task later (mirrors the
     engineering-principles re-validation gate).
   - *Notes* — links, related tasks.
3. **Sizing** — rough t-shirt or points estimate if the target tracker uses
   one.
   > Project-specific: confirm the estimation scheme once a tracker is
   > chosen (story points vs. a different estimate style vs. none).
4. **Labels/Status** — do not invent these. Use the `task-manager-culture`
   skill to get the real taxonomy once it exists; until then, leave
   unlabeled and flag to the user that labeling is pending setup.
5. If an MCP connector for the chosen tracker is configured, create the task
   directly via that MCP after drafting; otherwise output the draft as
   markdown for manual paste.
6. Before creating: the ticket is read by teammates — check it against the
   "Internal vocabulary stays internal" principle (no internal-tooling
   jargon, no internal file paths).
