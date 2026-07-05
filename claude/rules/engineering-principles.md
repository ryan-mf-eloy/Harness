---
description: Standing code-level engineering principles applied to every implementation task, in every project
---

# Engineering Principles

- **Requirements first.** Do not start editing until the request's
  acceptance criteria are explicit. If ambiguous, ask rather than assume.
- **Reuse over new.** Before writing any new function, class, or utility,
  search the codebase for an existing equivalent (grep/glob). Only write new
  code when nothing equivalent already exists.
- **DRY** — don't repeat the same logic in two places; extract instead.
- **SOLID** — single responsibility, open for extension/closed for
  modification, substitutable subtypes, small focused interfaces, depend on
  abstractions not concretions. Watch for: a class doing two unrelated
  jobs, a change that requires touching many unrelated call sites.
- **Law of Demeter** — a method should only talk to its immediate
  collaborators, not reach through them into their internals
  (`a.b().c().d()` chains are a smell).
- **Clean Code** — names that reveal intent, functions that do one thing,
  no magic numbers, no dead code left behind.
- **Object Calisthenics** — prefer small, focused methods and classes;
  avoid deep nesting; avoid primitive obsession where a small value type
  would be clearer.
- **Surgical diffs.** Prefer the smallest change that satisfies the
  acceptance criteria. No drive-by refactors bundled into an unrelated
  change. No renaming/moving files unless that's the explicit ask. See
  `surgical-changes.md` for the diff-hygiene checklist.
- **Testing is non-negotiable.** Unit + integration + end-to-end (as
  applicable) + a sanity check on cyclomatic complexity for anything new or
  changed — every time, no exception for "small" changes. This is enforced
  mechanically by the `Stop` hook wired globally in `~/.claude/settings.json`
  (see `Scripts/harness/hooks/README.md`); this rule
  explains the *why* so it happens proactively, not only when blocked.
- **Re-validation gate.** Before declaring anything done, re-read the
  original request/acceptance criteria and explicitly check each one off —
  do this even when confident.
- **Escalate, don't guess.** If a change crosses module boundaries, touches
  auth/payments/data-migration, or changes a public interface, invoke the
  `pre-change-impact-check` skill before writing code.
