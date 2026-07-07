---
name: Task Kickoff
description: End-to-end intake ritual for a new task before any code is touched — reads every available source in full (prompt, tracker item, linked epics/subtasks, attachments, video/image/audio, comment threads), runs discovery via `pre-change-impact-check`, resolves every ambiguity via `grill-with-docs` plus direct clarifying questions, assembles a standardized implementation plan with explicit scope and risk, and gates on explicit approval before any implementation begins. Use when assigned a new non-trivial task/ticket and about to start real work on it.
when_to_use: A new task, ticket, or feature request is assigned and work is about to begin — especially when it references a tracker item, has attachments/links, or carries enough ambiguity that assuming instead of asking would be risky.
argument-hint: "<task reference: prompt text, ticket key, or URL>"
allowed-tools: Read, Grep, Glob, WebFetch, Bash(git log*), Bash(git blame*), Bash(python3 */Scripts/harness/query.py*), Bash(gh issue view*), Bash(gh pr view*)
user-invocable: true
---

Read-and-plan only — this skill never edits or writes code. It ends at an
approved plan; implementation is a separate step.

Skip: a one-line fix, or a task with zero ambiguity, no tracker item, and
no attachments — go straight to `pre-change-impact-check` (existing broken
behavior instead of new work: `debug-fix-proposal`).

1. **Check memory first.** Query `Scripts/harness/query.py` and this
   project's `Vault/40-Memory/<project-slug>/` (or equivalent) for whether
   this exact task was already scoped, attempted, or handed off before —
   per "Precedent before invention." Resume from a prior plan or handover
   note instead of re-triaging from scratch if one exists.

2. **Identify the source completely.** A bare prompt needs nothing more. A
   tracker reference (Jira/Linear/GitHub Issues/other) needs the tracker
   identified first — don't guess which one from habit, check what's
   actually connected (an MCP, a CLI, an admin UI).

3. **Read 100% of available content**, not just the ticket description:
   - Parent epic (the *why*), linked/related subtasks (scope boundaries),
     and every comment in the thread, not only the latest one.
   - Every attachment and external link: documents, images, video, audio,
     Figma/FigJam links, recorded meetings (Granola or equivalent).
   - Linked tickets recursively, one hop out — if a linked ticket itself
     links further, note that it exists rather than chasing it indefinitely.
   - Whatever can't actually be fetched or analyzed (no transcript for a
     video, an inaccessible link), state the gap explicitly — see
     `principles/PRINCIPLES.md`'s "Full task context before starting." A
     requirement stated only in a screenshot is still a requirement.

4. **Discovery.** Run `pre-change-impact-check` directly via the Skill
   tool for precedent search, existing-code search, call-site tracing,
   test-coverage identification, and risk classification — do not
   re-derive that procedure here.

5. **Understanding — interview until zero ambiguity remains.**
   - List every open question surfaced by steps 1–4.
   - For each, try `grill-with-docs` against existing documentation first
     — don't spend the user's time on something the docs already answer,
     and surface any contradiction/staleness found along the way.
   - Whatever's still unresolved, ask directly (`AskUserQuestion` or
     inline) — do not proceed to planning with an open question the
     source material didn't actually answer.
   - If the task has no explicit, testable acceptance criteria yet, draft
     them now (same structure as the `task-create` skill) and confirm them
     with the user — this is what `pre-delivery-review` will eventually
     check the finished work against, so it needs to exist before coding
     starts, not be reconstructed afterward.

6. **Plan assembly.** Following `principles/PRINCIPLES.md` in full (layer
   discipline, DDD calibration, dependency direction, surgical-diff scope,
   mandatory test coverage), produce a plan that states:
   - **Scope** — what's in, what's explicitly out (mirrors the acceptance
     criteria from step 5).
   - **Files/modules to touch**, grounded in step 4's discovery.
   - **Risk tier** (Low/Medium/High, from step 4) and what it implies for
     how much of this checklist was worth running.
   - **Test plan** — unit/integration/e2e as applicable, plus the
     cyclomatic-complexity sanity check.
   - **ADR needed?** — flag it now if this introduces a new external
     dependency, changes a data model, or picks between two or more viable
     approaches (per "Record decisions" in Architecture culture); don't
     write the ADR yet, just flag that one is owed.
   - A branch, via the `branch-worktree` skill, if one doesn't exist yet.

7. **Review and approval — a hard gate, not a formality.** Present the
   plan through `ExitPlanMode` (or the project's equivalent plan-approval
   mechanism) and wait for explicit approval before writing or editing a
   single line of code. A plan that "looks obviously right" still goes
   through this gate — that judgment is exactly what the gate checks.

Once approved, implementation proceeds normally; `pre-delivery-review`
closes the loop this skill opens.
