---
name: Branch & Worktree
description: Creates correctly-named branches and isolated git worktrees following consistent naming and lifecycle conventions. Use before starting a new task that needs its own branch, or when running risky/parallel work that shouldn't touch the main working tree.
when_to_use: Starting a new unit of work that should live on its own branch, or when the user wants to work on something in isolation (parallel task, risky experiment) without disturbing the current working tree.
argument-hint: "<short-task-description> [ticket-key]"
allowed-tools: Bash(git branch*), Bash(git worktree*), Bash(git checkout -b*), Bash(git fetch*)
---

1. **Naming convention** — `<type>/<ticket-key-if-any>-<slug>`, where type is
   one of `feature`, `fix`, `chore`, `refactor`, `spike`.
   > Confirm the target project's actual existing branch-naming convention
   > (`git log --all --oneline` / `git branch -a`) before assuming this
   > scheme applies — don't impose it on a repo with an established
   > different convention.
2. **Always branch from up-to-date main/master** — `git fetch` first. Never
   commit directly to main/master (also blocked mechanically by the
   `PreToolUse` hook wired globally in `~/.claude/settings.json`).
3. **Worktree use cases:**
   - Parallel exploration of two approaches.
   - Isolating a risky/experimental change so the main working tree stays
     clean.
   - Subagent-driven work using `isolation: worktree` on the subagent's
     frontmatter.
   For an interactive session, use `EnterWorktree`/`ExitWorktree` (or
   `claude --worktree <name>`) rather than raw `git worktree` commands where
   available — it also handles cleanup on exit.
4. **Cleanup** — remove a worktree once its branch is merged
   (`ExitWorktree` with `action: remove`, or `git worktree remove` for
   manually created ones). Don't let stale worktrees accumulate.
5. This skill does not push or open PRs — hand off to the `pr-create` skill
   for that.
