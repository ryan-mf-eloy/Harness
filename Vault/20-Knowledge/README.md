---
type: reference
tags: [vault]
status: active
created: 2026-07-05
---

# 20-Knowledge

Durable reference notes that aren't tied to one specific project: patterns,
glossary entries, "how X works" notes, cross-project lessons. If a note only
makes sense in the context of one project, it belongs in
`10-Projects/<slug>/` instead — put it here when a second, unrelated project
would also benefit from finding it.

## Playbooks/ — the precedent-before-invention loop

`principles/PRINCIPLES.md`'s "precedent before invention" rule and the
`pre-change-impact-check` / `pre-delivery-review` skills form a closed
loop: search here first before assuming a task is new, and write here
after solving something genuinely novel — so the *next* search finds it
instead of the task being re-solved from scratch.

Put a writeup in `20-Knowledge/Playbooks/<slug>.md` when a task had no
existing precedent and the way it got solved is likely to recur — not for
routine work that doesn't need a next-time shortcut. Frontmatter:

```yaml
---
type: reference
tags: [playbook]
project: <slug or omit if cross-project>
status: active
created: YYYY-MM-DD
---
```

Keep the body short and search-friendly rather than a full narrative:

```markdown
# <What this playbook is for>

## When to use this
<the situation that should trigger finding this note>

## Approach
<the actual steps/decision, concise>

## Why (if non-obvious)
<the reasoning that isn't visible just from the steps>
```

A stale playbook is worse than none — if you follow one and it no longer
matches reality, update it in the same turn (per the hygiene principle)
instead of leaving it for someone else to hit the same gap.
