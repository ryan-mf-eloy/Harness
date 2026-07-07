---
name: House Review Checklist
description: House-style review checklist (DRY/SOLID/Demeter/Object-Calisthenics conformance, surgical-diff scope, mandatory-test-coverage gate) — supplementary context for code review, not a replacement for correctness review.
when_to_use: Referenced during any code review pass (via /code-review or ad hoc) to check house-style conventions in addition to correctness.
user-invocable: false
---

This supplements `/code-review`'s correctness/reuse/simplification
dimensions — it does not replace them. For actual bug-hunting, defer
entirely to `/code-review`.

House-style checklist (cite line numbers on any "no"):

- Diff is scoped to the stated task — no drive-by changes.
- No new code was added where an equivalent already existed.
- SOLID / Law of Demeter / Object Calisthenics spot-check on any new or
  changed class.
- Layer discipline: business rules/validation live in the layer this
  project's own convention designates for them (see the project's
  `AGENTS.md` "Where to Modify" → "By layer" map, or
  `principles/PRINCIPLES.md`'s "Layer discipline" bullet if the project
  hasn't documented its own layer names yet) — flag a business rule or
  validation check found in a layer that owns a different concern (e.g.
  in a controller/route/UI layer instead of domain/service).
- Cyclomatic complexity of new/changed functions is reasonable — flag
  anything that reads as needing a split.
  > Project-specific: once a linter/complexity tool is chosen for the
  > target project, wire its exact threshold here. Generic guidance until
  > then: flag functions with more than ~4 independent branches/loops.
- Tests exist **and were actually run** for the changed behavior, not just
  written.
- The PR description follows `templates/PR_TEMPLATE.md`, and each Testing
  Performed claim is verifiable from the diff/CI, not just asserted.

Non-goals: this does not attempt security review (`/security-review`'s job)
or correctness bug-hunting (`/code-review`'s job). For the acting agent's
own self-check before declaring a task done (not a `/code-review` pass on
a diff), see `pre-delivery-review` instead — it covers verification
methodology this checklist doesn't (cross-source checks, assumed-vs-verified
framing).
