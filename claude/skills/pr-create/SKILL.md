---
name: PR Create
description: Drafts and opens a GitHub pull request using the standard changelog/description template — summarizes the diff, fills Summary/Why/What-Changed/Testing/Risk sections, and runs gh pr create. Use only when explicitly asked to open, create, or draft a PR.
when_to_use: User explicitly asks to create, open, or draft a pull request for the current branch's changes.
disable-model-invocation: true
allowed-tools: Bash(git status*), Bash(git diff*), Bash(git log*), Bash(git push*), Bash(gh pr create*), Bash(gh pr view*), Read
---

1. **Preconditions** — confirm you're on a feature branch (not
   main/master), and that the engineering-principles testing gate has
   actually been satisfied for this change (re-run tests if uncertain,
   don't assume clean just because nothing blocked you earlier in a long
   session).
2. **Gather context** — `git status`, `git diff` against the merge-base,
   `git log` since divergence.
3. **Fill the template** from `templates/PR_TEMPLATE.md` (in the Harness
   repo root): Summary, Why/Context, What Changed, Testing Performed, Risk &
   Rollback, Related Task/Issue.
   - Related Task/Issue: pull from the branch name if it encodes a ticket
     key, otherwise ask.
   - Testing Performed must list concrete, verifiable commands/results —
     not "tested manually" with no detail.
4. **Push and create** — push the branch with `-u` if not already tracking
   upstream, then `gh pr create --title "..." --body "$(cat <<'EOF' ... EOF)"`
   (heredoc form, to avoid quoting issues).
5. Return the PR URL. Never merge, never force-push.
