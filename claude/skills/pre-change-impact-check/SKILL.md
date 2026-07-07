---
name: Pre-Change Impact Check
description: Structured codebase-exploration and blast-radius checklist to run before any non-trivial implementation task — traces call sites, identifies affected tests, and flags cross-module or breaking-change risk. Use before starting large features, refactors, public-interface changes, or anything touching auth/data/payments.
when_to_use: Before writing code for any task that is not a one-line fix — especially when the change touches a shared module, a public API/interface, database schema, auth, or anything with more than a couple of call sites.
argument-hint: "[optional: short description of the planned change]"
allowed-tools: Read, Grep, Glob, Bash(git log*), Bash(git blame*), Bash(git diff*), Bash(python3 */Scripts/harness/query.py*)
user-invocable: false
---

Run this checklist before implementing $ARGUMENTS. Do not skip steps because
the change "looks small" — that judgment is exactly what this checklist
verifies.

Skip: an existing test is failing or behavior is already broken with no new
feature being planned — that's `debug-fix-proposal`'s job, not this one.

1. **Restate the acceptance criteria** in your own words. If the request
   originates from or references a task-tracker item (an epic, ticket,
   issue, or subtask), first explore its full available context — parent
   epic, linked/related subtasks, external links, attachments, embedded
   media — per `principles/PRINCIPLES.md`'s "Full task context before
   starting" bullet, rather than restating from a partial view. If
   anything is still unclear or couldn't be fetched/analyzed, stop and ask
   before proceeding.
2. **Search for precedent first** — assume this kind of task has probably
   been done before. Query the harness FTS index
   (`python3 <path-to-harness>/Scripts/harness/query.py "<topic>" --source vault`)
   and check `Vault/20-Knowledge/` and this project's own docs for an
   already-documented way of doing it. If one exists, follow it instead of
   re-deriving from scratch — note where it came from.
3. **Search for existing equivalents in code** (Grep/Glob) — per the
   reuse-over-new principle, confirm nothing already does this before
   writing anything new.
4. **Trace call sites.** Grep for every import/usage of anything you're
   about to change.
5. **Identify existing test coverage** for the affected area — note which
   tests will need updates versus which are net-new.
6. **Classify risk:**
   - *Low* — isolated, well-tested, reversible.
   - *Medium* — touches more than one module, or has partial test coverage.
   - *High* — crosses module boundaries with no test coverage, touches
     auth/payments/migrations, changes a public interface, crosses a
     bounded context / introduces a cross-layer violation (see "Layer
     discipline" in `principles/PRINCIPLES.md`), or performs a mutating
     action against live infrastructure via CLI (see the `infra-cli-check`
     skill).
   For medium/high, surface this explicitly to the user before proceeding
   and name the specific risk — don't bury it in the implementation. Risk
   tier also sets how much research step 2 and 3 deserve: don't spend a
   high-risk-sized investigation on a low-risk change.
7. Only after steps 1–6, produce a short implementation plan and proceed.
   If step 2 found no precedent and this turns out to be genuinely novel,
   remember to document it afterward (see the `pre-delivery-review` skill)
   so the next search finds it.
