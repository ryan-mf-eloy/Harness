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
or correctness bug-hunting (`/code-review`'s job).
