---
type: decision
tags: [harness, onboarding, data-residency, paketa]
status: active
created: 2026-07-07
---

# Consuming projects keep their own business/domain memory, not centralized in this repo's Vault

## Context

Consolidating the Paketa project (a separate fintech-domain agent workspace)
onto this harness's conventions required a concrete answer to a question
this harness's own `AGENTS.md` doesn't fully resolve on its own: `AGENTS.md`
states per-project memory lives at `Vault/40-Memory/<project-slug>/` and
`Vault/10-Projects/<project-slug>/` inside this repo — implying a single
central Vault with project-slug subfolders. Paketa had its own mature
Obsidian vault (`paketa-vault/`) already holding real business/domain
knowledge: credit-engine internals, guarantee mechanics (QiTech, Dataprev),
credit simulators, and dated PR-review learnings (ENGM-32, ENGM-40,
ENGM-56).

Neither `Codebase/REGISTRY.md` nor `Vault/40-Memory/` had a real project in
them yet at the time of this decision (`Vault/40-Memory/{acme-widgets,
harness-self}` were empty placeholders) — so this was the first time the
central-vault convention met a project with substantial, pre-existing,
confidential domain content of its own, and the abstract convention had to
be tested against a concrete case rather than assumed.

## Decision

Paketa's own business/domain knowledge (`paketa-vault/20-Knowledge/`,
`paketa-vault/10-Agent-Memory/`, and its one genuinely domain-specific
playbook) stays physically inside the Paketa project, not migrated into
this repo's `Vault/`. Only Paketa's *generic* agent-tooling scaffolding
(a duplicate engineering-principles restatement, a duplicate onboarding
skill, duplicate guard-hook logic) was retired in favor of this harness's
shared versions — see `Codebase/REGISTRY.md`'s `paketa` row and the
sibling ADR on the two guard hooks ported from Paketa
(`2026-07-06-infra-and-remote-automation-guard-hooks.md`) for the
scaffolding side of this same consolidation.

Consequence for the onboarding convention: Paketa has no
`Vault/40-Memory/paketa/` folder in this repo and no `autoMemoryDirectory`
pointed here — its `AGENTS.md` stamps this harness's `principles/PRINCIPLES.md`
for shared engineering culture, but its own memory/knowledge stays governed
by its own `paketa-vault/` and validation tooling (`scripts/ai-tooling/`),
unchanged.

## Alternatives considered

- **Migrate Paketa's vault content into `Vault/10-Projects/paketa/` and
  `Vault/40-Memory/paketa/` in this repo, matching the stated convention
  literally.** Rejected — this repo (`Personal/OpenSource/Harness`) is a
  general-purpose, personal tooling repo, potentially reused as a template
  or reference across future, unrelated projects. Physically absorbing one
  specific employer's confidential fintech domain knowledge into it is a
  data-residency/boundary problem independent of whether the folder
  taxonomy matches — the same reasoning `principles/PRINCIPLES.md`'s
  "Internal vocabulary stays internal" bullet already applies to
  harness-internal vocabulary leaking into external-facing output, applied
  here to the reverse direction (external business data flowing into
  harness-internal storage).
- **Point Paketa's `autoMemoryDirectory` at `Vault/40-Memory/paketa/` here
  while leaving `paketa-vault/` in place, splitting memory across two
  vaults.** Rejected — this creates exactly the two-systems-doing-the-same-job
  duplication this consolidation was meant to eliminate, just moved to a new
  seam (which vault does a new note go in) instead of removed.

## Consequences

- The `Vault/40-Memory/<project-slug>/` / `Vault/10-Projects/<project-slug>/`
  convention in `AGENTS.md` is confirmed to mean "available for a project
  that wants it," not "mandatory for every onboarded project" — a project
  that already has its own equivalent, confidentiality-sensitive memory
  system is expected to keep it, onboarding only the generic layer.
  `AGENTS.md` and `ONBOARDING.md` do not yet say this explicitly; a future
  pass should add a line clarifying this is a real, considered option, not
  an oversight, the next time either file is touched.
- `Codebase/REGISTRY.md`'s status legend (`onboarded` implies
  `autoMemoryDirectory` wired) doesn't cleanly cover this case — Paketa's
  row is marked `onboarded (memory exception)` with a note explaining why,
  rather than stretching the existing `onboarded`/`not onboarded`/`needs
  refresh` values to fit.
