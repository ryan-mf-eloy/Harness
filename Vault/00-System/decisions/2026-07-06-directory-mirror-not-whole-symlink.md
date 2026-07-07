---
type: decision
tags: [harness, install, symlinks, skills, agents, portability]
status: active
created: 2026-07-06
---

# Directory mirrors with per-entry symlinks, not whole-directory symlinks

## Context

`install.py` (see
`Vault/00-System/decisions/2026-07-05-path-portable-install.md`) originally
made `~/.claude/agents`, `~/.claude/skills`, `~/.cursor/agents`, and
`~/.codex/agents` each a single whole-directory symlink straight into this
harness repo's own `claude/agents/`, `claude/skills/`, `.cursor/agents/`,
`.codex/agents/`.

This broke the very first time a third-party tool installed something new
into one of those directories. The community `caveman` skill's own
installer wrote its 6 skill directories plus a lock file into
`~/.claude/skills/`, following the symlink transparently — every one of
those files landed physically inside this harness's own git-tracked
`claude/skills/` folder, showing up as untracked files in `git status`.
Cleaned up by hand once (moved the 6 directories + lock file out, rebuilt
the symlink structure), but the same latent bug remained for
`~/.claude/agents` and `~/.codex/agents` (both still whole-directory
symlinks) until this fix.

A first attempt at the fix used a plain directory listing to decide which
entries under, e.g., `claude/skills/` were "the harness's own" versus
"foreign" — this failed a test that reproduced the exact incident: once a
foreign entry has already landed inside a harness-owned directory (via the
old bug, or by being placed there in a test), a directory listing can no
longer distinguish it from the harness's own real content — they're
physically the same kind of directory entry, indistinguishable by name or
location alone.

## Decision

1. `~/.claude/agents`, `~/.claude/skills`, `~/.cursor/agents`, and
   `~/.codex/agents` are never whole-directory symlinks into this repo.
   Each is a **real directory**, containing one individual symlink per
   harness-owned entry pointing back into the repo. Anything else another
   tool installs alongside sits there as an ordinary real file/directory —
   never inside this repo's git tree, no matter what gets installed next.
2. `~/.agents/skills` becomes a symlink to `~/.claude/skills` (itself now
   real) rather than to the harness directly — same reasoning: its source
   is already a real, non-harness location, so nothing written through it
   can land inside this repo either.
3. **The source of truth for "which entries are the harness's own" is git
   tracking (`git ls-files`), not a directory listing.** This is the part
   that actually closes the bug: even if a foreign entry is already
   sitting inside a harness-owned directory (exactly the state this repo
   was in after the `caveman` incident), git correctly reports it as
   untracked, so it's never mistaken for harness content — during
   migration it's identified as foreign and moved out, never claimed as
   the harness's own or silently dropped.
4. Migrating an existing whole-directory symlink to the new layout
   preserves whatever foreign entries are found inside its resolved
   target (identified via step 3), moving them into the new real
   directory rather than discarding them — verified with a sandboxed test
   that reproduces the exact incident (a foreign file mixed in among the
   harness's own agent files inside an old-style symlink target) before
   trusting this against the real, live `~/.claude/agents` and
   `~/.codex/agents`, which still had the bug at the time this was
   written.

## Alternatives considered

- **Keep directory listing as the "is this harness-owned" test, just
  exclude a fixed list of known third-party names (`caveman`, etc.).**
  Rejected — this only ever protects against the *specific* third-party
  tool that already caused a problem, not the general case. The whole
  point of this fix is that any future tool's install should be safe by
  construction, not enumerated after the fact.
- **Force-overwrite (`ln -sf`) whenever a target isn't already the exact
  expected symlink.** Rejected for the same reason the original
  `path-portable-install` ADR rejected it: it can't distinguish "stale
  symlink safe to replace" from "a real directory with real content in
  it," and would either destroy the exact kind of third-party content this
  fix is meant to protect, or crash unpredictably depending on what's
  there.
- **Leave `~/.claude/agents`/`~/.codex/agents` as whole-directory symlinks
  since nothing had been installed into them yet (unlike `~/.claude/skills`,
  which had already been hit).** Rejected — the bug is latent, not
  hypothetical; the only reason it hadn't manifested there yet is that no
  third-party agent-marketplace install had happened to target those paths
  during this session. Waiting for it to happen again before fixing it
  would repeat the exact mistake.

## Consequences

- Installing any third-party skill or subagent globally (via its own
  installer, a plugin marketplace, or by hand) is now safe regardless of
  which of these four directories it targets — it becomes an ordinary
  real file living alongside the harness's own symlinks, never inside this
  repo's git tree.
- `install.py`'s directory-mirror logic now shells out to `git` (via
  `subprocess`) to determine harness ownership, a new dependency the
  original design didn't have — accepted, since no other signal reliably
  survives the "foreign content already landed here" case this fix
  specifically exists to handle.
- A newly-added harness skill or subagent is only recognized as
  harness-owned once it's tracked by git (committed, or at least staged) —
  a file sitting in `claude/skills/`/`claude/agents/` that hasn't been
  `git add`-ed yet won't get a global symlink until it is. Accepted as a
  reasonable, minor trade-off: it's a natural side effect of using git as
  the source of truth, and in practice a new skill is added and committed
  in the same pass before anyone relies on its global symlink existing.
