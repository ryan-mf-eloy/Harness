---
name: Flow & Impact Mapping
description: Deep flow, business-rule, and criticality/impact mapping methodology for building a trustworthy implementation plan — traces every linear step and every branch/condition to completion, cross-checks every rule and decision against documentation via `grill-with-docs`, tiers criticality and impact per flow rather than once for the whole change, and runs cheap empirical preliminaries (an existing test, a read-only query) before the plan is considered final. Use as the core planning step inside `task-kickoff`, or standalone, for any change with real business logic, branching, or cross-flow impact.
when_to_use: Building the actual implementation plan for a change that is more than a trivial linear edit — branches/conditions, business rules or validations, or effects on more than one flow/consumer.
argument-hint: "<flow or change being planned>"
allowed-tools: Read, Grep, Glob, Bash(git log*), Bash(git blame*), Bash(python3 */Scripts/harness/query.py*)
user-invocable: true
---

Skip: a one-line fix or a purely mechanical change with no branching and no
business logic — `pre-change-impact-check` alone already covers that case.

This is the deep-dive companion to `pre-change-impact-check`: that skill
covers call sites, test coverage, and one risk tier for the change as a
whole; this one covers the business logic and control flow *inside* the
change, tiered per flow, not just once. Run `pre-change-impact-check`
first if it hasn't already run for this change — don't re-derive call-site
tracing or precedent search here.

1. **Explore.** Orient in the actual code path end to end at least once
   before reasoning about it abstractly — read the real flow, don't infer
   it from the ticket description alone.

2. **Map the flow linearly, then every branch.** Walk entry point to exit
   point(s) in order. For every conditional, switch/case, early return,
   exception path, retry, or async race: state the condition, what
   triggers it, what happens on each side, and whether a test currently
   covers it. Anything with 3+ branches gets a written decision-tree
   sketch (a short list or a Mermaid block) — a paragraph hides branches a
   tree makes obvious.

3. **Map the business rules.** For every validation/rule the flow
   enforces, state the actual business reason, not just what the code
   checks — "why does this rule exist" is a different question from "how
   is it coded today," and conflating them is how a refactor accidentally
   changes behavior. Distinguish a rule genuinely required by the domain
   from an implementation detail that happens to look like one.

4. **Question the plan itself — why, how, where.** Before treating the
   emerging approach as settled: *Why* this approach — is there a simpler
   or more conventional one? *How* — is the mechanism consistent with this
   project's own patterns (reuse over new, layer discipline, DDD
   calibration)? *Where* — is this the right module/layer/bounded context,
   or is logic being forced into the wrong place? Does it need refinement?
   Is information still missing? Answer these explicitly — "it looks
   fine" is not an answer.

5. **Map criticality per flow, not once for the whole change.** A single
   change can touch flows of very different weight — tier each one
   separately (financial/data-integrity impact, auth-sensitivity,
   user-facing vs. internal-only, reversibility) rather than assigning one
   risk level to everything touched.

6. **Map impact.** What breaks if a given flow is wrong: downstream
   consumers, other flows depending on current behavior, adjacent bounded
   contexts, anything requiring a data backfill/migration. This is the
   business-level companion to `pre-change-impact-check`'s call-site
   trace, not a replacement for it.

7. **Validate meticulously with `grill-with-docs`.** Run it per rule, per
   decision, per flow identified above — not once for the whole task.
   Where several rules are independent of each other, batch these checks
   in parallel rather than one at a time — nothing about rule A's
   validation depends on rule B's result. Surface every contradiction,
   staleness signal, or gap found; a rule with no documentation backing it
   is itself a finding, not something to quietly assume away.

8. **Run preliminaries before finalizing the plan.** Wherever a cheap,
   real check is possible, run it instead of reasoning abstractly: the
   existing test suite for a current baseline pass/fail, a read-only query
   confirming a data assumption, a quick reproduction of current behavior.
   Anything touching a live external system goes through `infra-cli-check`
   first. A plan built on an unverified assumption is a guess with extra
   steps.

9. **Close every open question before handing off.** Every branch,
   condition, and business rule from steps 2–3 must be resolved — either
   confirmed by evidence (steps 7–8) or explicitly answered by the
   user/tracker — before the plan is considered final. An unresolved
   conditional is exactly the kind of thing that surfaces as a bug after
   merge, not before.

Output: a flow map (linear steps + branch tree), a business-rules table
(rule → source → validated via `grill-with-docs`: yes/no), a criticality
map (flow/point → tier → why), an impact map, and the list of open
questions with how each was resolved. This is what `task-kickoff`'s plan-
assembly step and the `risk-analyst` subagent both produce when this skill
runs.
