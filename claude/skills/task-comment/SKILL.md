---
name: Task Comment
description: Posts a status update, blocker note, or PR-link comment on an existing task/ticket in the project's task manager. Use when asked to update, comment on, or link work to an existing ticket.
when_to_use: User asks to comment on, update, or post progress to an existing task/ticket — including linking a newly opened PR back to its ticket.
argument-hint: "<ticket-key> <update-summary>"
user-invocable: true
---

1. **Comment types:**
   - *Progress update* — what's done / in-progress / blocked.
   - *PR-link* — auto-format: "PR opened: `<url>`".
   - *Blocker* — what's blocking, who/what is needed to unblock.
2. **Tone/format** — factual, no filler; the tracker adds its own
   timestamp. Use a bullet list when reporting multiple sub-items.
3. **Always link the PR back to the ticket** when `pr-create` completes for
   a branch whose name encodes a ticket key — this is the natural hand-off
   point between the two skills.
4. **Mechanism** — via the chosen tracker's MCP if connected, else output
   the comment text for manual paste.
   > Project-specific: exact MCP tool name/params depend on which tracker is
   > chosen — fill in once `task-manager-culture` is configured.
5. Same rule as ticket creation: check the comment against "Internal
   vocabulary stays internal" before posting — teammates read this too.
