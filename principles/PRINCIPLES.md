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
- **Full task context before starting.** When a request originates from or
  references a task-tracker item (an epic, ticket, issue, or subtask),
  explore its entire available context before treating the acceptance
  criteria as explicit — the parent epic (for the *why*), linked/related
  subtasks (for scope boundaries), external links, and attachments
  (documents, images, video, audio) — using whatever tools are actually
  connected (the tracker's own MCP/API, WebFetch, Read). A requirement
  stated only in a screenshot or a linked doc is still a requirement;
  missing it isn't the same as it being genuinely absent. If something
  can't actually be fetched or analyzed (e.g., no transcript available for
  a video), say so explicitly rather than silently proceeding as if it had
  been reviewed — this is the same "state the gap, don't guess" discipline
  as "Evidence over assumption" above, applied specifically to task
  context. See the `pre-change-impact-check` skill for where this fits
  into the broader pre-implementation checklist.
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
- **Layer discipline.** Respect the application's own layers — typically
  presentation/API → application → domain → infrastructure, though exact
  names are project-specific (see "Dependency direction" in Architecture
  culture, which governs import direction; this bullet governs what
  *kind* of logic belongs where — a change can satisfy one and still
  violate the other). Business rules and validation belong in the
  **domain** layer, never in presentation/API or infrastructure.
  Anti-patterns to recognize on sight: a business rule (a
  discount-percentage bound, an eligibility check) written inline inside
  an HTTP route handler instead of called from a domain object; a domain
  entity that extends an ORM base class or imports a web-framework type,
  coupling business logic to a delivery/persistence mechanism that
  should depend on it, not the reverse.
- **DDD-informed modeling, calibrated to risk, not maximalist.** For a
  genuinely complex domain, model with real DDD concepts instead of a bag
  of loosely-related functions: **Entity** (identity persists across
  state changes), **Value Object** (defined by its attributes, no
  identity, immutable — e.g. Money, DateRange), **Aggregate**/**Aggregate
  Root** (entities/value objects that must change together to keep an
  invariant true, modified only through the root), **Repository**
  (persistence abstraction — domain code depends on the interface, never
  the query/ORM details), **Domain Service** (a domain operation that
  doesn't belong to one entity), **Domain Event** (something that
  already happened, for decoupling side effects — e.g. `OrderPlaced`
  triggering a confirmation email via an application-layer subscriber,
  not inline in the entity). A **Bounded Context** is the
  domain-modeling version of the existing "three-or-more-modules" signal
  — the same real-world concept (e.g. "Product") can be modeled
  differently in different contexts (catalog vs. billing) rather than
  forced into one shared shape; keep code vocabulary matching the domain
  expert's own terms (**Ubiquitous Language**) within each context.
  Calibrate to the same low/medium/high risk tier used elsewhere (see
  "Escalate, don't guess"): a script, a single CRUD endpoint, or a
  prototype is low risk, and the full pattern set there is exactly what
  "No speculative abstraction" and "Reuse over new" already forbid —
  plain functions are correct. Bounded contexts specifically pay for
  themselves when multiple teams/subsystems genuinely evolve
  independently; on a solo project or small team with one deployable,
  treat that machinery as available for when a second real use case
  shows up, not a default (same "No speculative abstraction" test).
  Reach for tactical DDD when the signal is medium/high *for
  domain-modeling reasons*: a business invariant spanning multiple
  entities, a concept already modeled inconsistently across modules, or
  a codebase large enough that ad hoc structure is causing bugs — and
  note "Surgical diffs" and the "three-or-more-modules signal" cut both
  ways: splitting a 40-line script into five DDD-flavored files is the
  same boundary-drawn-wrong signal as cramming five concerns into one
  module. This calibration is not license to skip structure a complex
  domain actually needs — an **anemic domain model** (entities as pure
  data-bags, all logic in a generic `*Service` class) is the anti-pattern
  this bullet prevents, not a safe default. Full unpacking, worked
  examples, and context-mapping patterns:
  `Vault/20-Knowledge/Playbooks/domain-driven-design-and-layering.md`.
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
  target project's actual layering rather than assuming a default —
  distinct from "Layer discipline" in Development culture, which governs
  what *kind* of logic belongs in a layer, not import direction.
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
- **Token economy in conversation.** Default to terse, high-signal replies
  — drop filler words, hedging, and pleasantries where dropping them costs
  nothing in clarity. The community `caveman` skill
  (github.com/JuliusBrussee/caveman, an open Agent-Skills-format skill
  reachable the same way as this harness's own — see `AGENTS.md`'s
  "Provider-agnostic by construction" section — via `.agents/skills`) is
  the concrete mechanism recommended here: install once, then toggle per
  session with `/caveman [lite|full|ultra]`, and "stop caveman"/"normal
  mode" to turn it back off. Never let this compress away the clarity a
  destructive-action confirmation, a security warning, or a multi-step
  sequence needs — drop the compression the moment it risks ambiguity,
  the same exception the skill itself already documents.

  This applies **only** to the live chat/conversational reply stream —
  nothing else, ever. Never compressed, no exceptions: documentation
  (READMEs, skill/subagent files, ADRs, Vault notes, PR descriptions,
  commit messages), memory (Claude Code's own auto-memory, `MEMORY.md`,
  anything under `Vault/40-Memory/`), this harness's own operational
  content (`principles/PRINCIPLES.md`, `AGENTS.md`, skills, subagents,
  hooks, templates), code/inline comments, comments posted to a
  ticket/PR/task tracker, emails, and any other action visible outside
  this conversation (a chat message to a third party, a calendar invite,
  a comment on an external system) — including never running the skill's
  own `caveman-compress` command against any of the above, even though
  compressing memory-style files is one of its advertised features. Same
  reasoning as "Internal vocabulary stays internal" below: these are read
  by people and systems without today's conversational context, so a
  fragment that's unambiguous mid-conversation can become a genuine
  misread later, or just read as unprofessional to someone outside this
  session, with no one left to ask what it meant.
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
- Before running any external infrastructure CLI (cloud provider, database
  platform, or infra-as-code tool), confirm the CLI is actually installed
  and confirm the active profile/account/project matches the environment
  named in the request — never assume the current default context is
  correct. Read-only operations may run autonomously once that check
  passes; anything mutating still needs the explicit approval the
  destructive-action bullet above already requires — this bullet adds the
  environment-verification step and the read-only carve-out, it doesn't
  redefine what counts as destructive. See the `infra-cli-check` skill for
  the operational checklist and provider-specific verification commands.
- See "Evidence over assumption" in "Reasoning & verification discipline"
  — the web/tool-output-is-evidence rule generalizes to every source, so
  it isn't repeated here.
