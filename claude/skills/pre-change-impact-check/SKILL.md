---
name: Pre-Change Impact Check
description: Structured codebase-exploration and blast-radius checklist to run before any non-trivial implementation task — traces call sites, identifies affected tests, and flags cross-module or breaking-change risk. Use before starting large features, refactors, public-interface changes, or anything touching auth/data/payments.
when_to_use: Before writing code for any task that is not a one-line fix — especially when the change touches a shared module, a public API/interface, database schema, auth, or anything with more than a couple of call sites.
argument-hint: "[optional: short description of the planned change]"
allowed-tools: Read, Grep, Glob, Bash(git log*), Bash(git blame*), Bash(git diff*)
---

Run this checklist before implementing $ARGUMENTS. Do not skip steps because
the change "looks small" — that judgment is exactly what this checklist
verifies.

1. **Restate the acceptance criteria** in your own words. If any are
   unclear, stop and ask before proceeding.
2. **Search for existing equivalents** (Grep/Glob) — per the reuse-over-new
   principle, confirm nothing already does this before writing anything new.
3. **Trace call sites.** Grep for every import/usage of anything you're
   about to change.
4. **Identify existing test coverage** for the affected area — note which
   tests will need updates versus which are net-new.
5. **Classify risk:**
   - *Low* — isolated, well-tested, reversible.
   - *Medium* — touches more than one module, or has partial test coverage.
   - *High* — crosses module boundaries with no test coverage, touches
     auth/payments/migrations, or changes a public interface.
   For medium/high, surface this explicitly to the user before proceeding
   and name the specific risk — don't bury it in the implementation.
6. Only after steps 1–5, produce a short implementation plan and proceed.
