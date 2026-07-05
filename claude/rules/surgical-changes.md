---
description: Diff hygiene and pre-existence checks before adding new code
---

# Surgical Changes

- **Does something equivalent already exist?** Grep for similar function
  names, check adjacent files in the same directory, check for an existing
  `utils`/`helpers` module before writing anything new.
- **Scope-creep guard.** If you notice an unrelated issue mid-task, do not
  fix it inline — flag it for a separate pass and keep the current diff
  targeted to what was asked.
- **Never rename, move, or delete files as a side effect of an unrelated
  task.**
- **Prefer editing over rewriting.** Prefer config over code. Prefer
  extending an existing test file over creating a new one when extending
  existing behavior.
- **A diff should read as "the smallest change that does exactly what was
  asked,"** not as an opportunity to also clean up everything nearby.
