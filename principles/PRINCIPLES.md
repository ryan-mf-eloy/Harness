# Engineering Principles

`principles/PRINCIPLES.md` is the single, canonical source of these rules. It is plain
markdown with no tool-specific syntax, so any coding agent — Claude Code,
Cursor, Codex CLI, Windsurf, or a human reading it directly — can load and
follow it without adapter code. Every place this content needs to reach
(a global config slot for one tool, an onboarded project's own `AGENTS.md`)
gets there by symlinking or copying this exact file, never by re-authoring
a parallel version. If you need to change a rule, change it here.

## Reasoning & verification discipline

This section governs *how to think*, before the sections below govern
*how to code* — it applies to every decision and answer, not only code
changes.

- **Evidence over assumption.** Treat everything you didn't directly verify
  this session as a claim, not a fact — memory files, past notes, MCP/tool
  output, logs, database results, documentation, prior conversation, even
  `principles/PRINCIPLES.md` itself if it seems to contradict what you're
  actually observing right now. Weigh it, don't default to it. This
  applies to every source, not only external web content.
- **Reason before agreeing.** Don't just comply with a stated premise or
  agree with a proposed approach — interpret the request, check it against
  what you can actually observe, and say so explicitly when the evidence
  points elsewhere. A respectfully stated disagreement beats silent
  agreement that turns out wrong.
- **Consider more than one read.** For non-trivial decisions, weigh at
  least one alternative interpretation, approach, or root cause before
  committing — especially when a request is ambiguous, a bug's cause isn't
  obvious yet, or a design has more than one reasonable shape.
- **Research before asserting, proportional to the stakes.** When your own
  knowledge might be missing, uncertain, or stale (fast-moving libraries,
  APIs, current events, anything version-specific), verify against a real
  source — documentation, the codebase, a web search — rather than
  asserting from training data. Depth should scale with risk and
  ambiguity, using the same low/medium/high tiering as
  `pre-change-impact-check`: a one-line fix doesn't need the same
  investigation as a schema migration. Exhaustive research on every
  trivial action defeats this harness's own token-efficiency goal — that
  tradeoff is deliberate, not an oversight.
- **Precedent before invention.** Assume this kind of task has probably
  been done before in this workspace. Search first — the FTS index
  (`Scripts/harness/query.py`), `Vault/20-Knowledge/`, the project's own
  docs — and follow the documented way of doing it if one exists, instead
  of re-deriving from scratch. If it's genuinely new, solve it following
  the standing rules here, then document the approach in
  `Vault/20-Knowledge/` so the next agent finds it through the same search
  instead of re-solving it from nothing.
- **Review before declaring done.** Before considering a non-trivial task
  finished, check it against every relevant source actually available —
  not just the diff you wrote. See the `pre-delivery-review` skill.
- **Continuous hygiene.** Keep memory and notes current, deduplicated, and
  organized as an ongoing habit, not an occasional cleanup — update a
  stale note instead of leaving a contradicting new one beside it, and
  prefer the existing `consolidate-memory` skill over letting memory grow
  unchecked.

## Development culture

- **Requirements first.** Do not start editing until the request's
  acceptance criteria are explicit. If ambiguous, ask rather than assume.
- **Reuse over new.** Before writing any new function, class, or utility,
  search the codebase for an existing equivalent. Only write new code when
  nothing equivalent already exists.
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
  change. No renaming/moving files unless that's the explicit ask.
- **Testing is non-negotiable.** Unit + integration (as
  applicable) + end-to-end + a sanity check on cyclomatic complexity for anything new or
  changed — every time, no exception for "small" changes.
- **Re-validation gate.** Before declaring anything done, re-read the
  original request/acceptance criteria and explicitly check each one off —
  do this even when confident.
- **Escalate, don't guess.** If a change crosses module boundaries, touches
  auth/payments/data-migration, or changes a public interface, do a
  deliberate blast-radius/risk check before writing code: trace call sites,
  check existing test coverage, and classify the risk (low/medium/high)
  before proceeding. For medium/high risk, surface this explicitly rather
  than burying it in the implementation.

## Surgical changes (diff hygiene)

- **Does something equivalent already exist?** Check adjacent files and
  existing `utils`/`helpers` modules before writing anything new.
- **Scope-creep guard.** If you notice an unrelated issue mid-task, do not
  fix it inline — flag it for a separate pass and keep the current diff
  targeted to what was asked.
- **Never rename, move, or delete files as a side effect of an unrelated
  task.**
- **Prefer editing over rewriting.** Prefer config over code. Prefer
  extending an existing test file over creating a new one when extending
  existing behavior.
- A diff should read as "the smallest change that does exactly what was
  asked," not as an opportunity to also clean up everything nearby.

## Architecture culture

- **Record decisions.** Any decision that changes a module boundary,
  introduces a new external dependency, changes a data model, or picks
  between two or more viable architectural approaches gets a short
  Architecture Decision Record (Context / Decision / Consequences /
  Alternatives Considered).
- **Dependency direction.** Lower layers must not import from higher
  layers. What counts as a "layer" is project-specific — confirm the
  target project's actual layering rather than assuming a default.
- **Composition over inheritance** at the architecture level — distinct
  from Object Calisthenics, which is the same principle applied at the
  class level.
- **Three-or-more-modules signal.** If satisfying one requirement requires
  touching three or more modules, treat that as a signal to pause and
  consider whether a boundary is drawn wrong, rather than pushing through.
- **No speculative abstraction.** Don't generalize ahead of a second real
  use case — YAGNI applied at the architecture level.

## Comments & explanation

- Comment only the **why**, never the **what** — code should read like the
  what; comment when a reader would otherwise ask "why on earth did they do
  it this way."
- No commented-out code left behind. No comment that just restates the
  function name in prose above it.
- TODO comments must name an owner or a tracking ticket, never a bare
  `TODO`.
- When explaining a change in conversation: lead with the **why**, then
  **what changed**, then anything the user needs to do next.
- No emojis unless explicitly requested. State intent plainly rather than
  narrating each step.
- **Internal vocabulary stays internal.** Harness-specific terms ("the
  Harness", a folder name like `RAG/` or `Vault/`, a specific skill or
  subagent name) and this machine's absolute file paths are operational
  vocabulary for your own reasoning — not for a PR description, commit
  message, code comment, task-tracker ticket, or any business/domain
  document a teammate, client, or reviewer without this context will read.
  Translate to what was actually done and verified, not which internal
  folder or skill did it. The same applies to verbatim memory/Vault note
  content — summarize the relevant fact, don't paste internal notes into
  external-facing output. This doesn't apply to a project's own
  `AGENTS.md`/`CLAUDE.md` — referencing the harness there is the intended
  integration point, not a leak.

## Non-negotiable safety rules

- Never read, print, copy, or persist secret values. Reference secrets
  only by label, through a wrapper script — never inline a raw value.
- Before a destructive or irreversible action (force-push, hard reset,
  bulk delete, schema migration), state the action, the target, the blast
  radius, and ask for explicit approval before proceeding.
- See "Evidence over assumption" above — the web/tool-output-is-evidence
  rule generalizes to every source, so it isn't repeated here.
