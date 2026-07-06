---
type: decision
tags: [harness, portability, install, symlinks, hooks]
status: active
created: 2026-07-05
---

# Path-portable install: replacing copy-paste setup with an idempotent script

## Context

This harness is meant to be cloned to one filesystem location at a time,
but relocatable over time — moved, recloned on another machine, or
reorganized into a different folder — with everything continuing to work
regardless of where that one active clone currently lives. Two parts of
the repo violated this, confirmed directly (not assumed) by a full-repo
grep and a read of every relevant file:

1. `claude/skills/onboard-project/SKILL.md` hardcoded this session's
   specific absolute path to `ONBOARDING.md`, with an explanatory comment
   correctly identifying *why* a dynamic mechanism was needed
   (`${CLAUDE_PROJECT_DIR}` resolves to whatever project a session is
   currently in, not the Harness, when this skill is invoked from inside a
   different project) — but landing on a fix (a literal path) that broke
   the moment the repo moved, the exact failure mode the comment itself
   was trying to avoid.
2. `README.md`'s "One-time setup" section was a bash snippet of `ln -s`
   commands meant to be copy-pasted once, with `$PWD` resolved at
   paste-time and baked into each symlink. Re-running the identical
   commands after the repo moved fails outright — `ln -s` refuses to
   create a symlink where one already exists, and this failure mode
   already happened once this same session, where `~/.cursor/agents`
   turned out to be a real, pre-existing empty directory (not a stale
   symlink), which needed a manual `rmdir` before the `ln -s` could
   succeed at all.
3. Global hook configuration for Claude Code, Cursor, and Codex CLI
   (`~/.claude/settings.json`, `~/.cursor/hooks.json`,
   `~/.codex/hooks.json`) was hand-edited during this same session to wire
   up this repo's hook scripts by absolute path — with no mechanism to
   refresh those paths later, and every hand-edit risking silently
   clobbering unrelated content already in those files (all three carry
   content this harness does not own — `~/.claude/settings.json` in
   particular has `permissions`, `enabledPlugins`, and other keys entirely
   unrelated to this harness).

All Python scripts under `Scripts/` other than this one already solve the
"where am I" problem correctly and portably, via
`Path(__file__).resolve().parents[N]` — confirmed by reading
`Scripts/harness/_index_common.py` (`parents[2]`) and
`Scripts/harness/hooks/_reinforcement_common.py` (`parents[3]`, with its
own comment explaining the depth difference). The gap was scoped
specifically to markdown prose (the onboarding skill) and external
config/setup (the README snippet and the three global JSON files) — never
to any Python script's own root computation, which needed no changes.

## Decision

1. Add `Scripts/harness/install.py`, a single idempotent Python script
   (Python chosen per `Scripts/shared/README.md`'s own stated convention —
   "Python for anything with real logic," and JSON structural merging
   without clobbering unrelated keys is exactly that) that:
   - Computes its own root the same way every other harness script does
     (`Path(__file__).resolve().parents[2]`).
   - Creates or refreshes the 7 global symlinks this harness depends on,
     using a symlink table extracted verbatim from the old README setup
     block (no parallel, potentially-drifting list). A target that's
     already a correctly-pointed symlink is left untouched; a
     stale-pointed symlink is replaced; a target that exists as a real
     file or directory (not a symlink) is reported and skipped, never
     silently deleted — the exact `~/.cursor/agents` case above is the
     reason this branch exists as a distinct, non-automatic outcome.
   - Merges this harness's own hook entries into the three global JSON
     config files, matching each known entry by its script's exact
     basename at the end of the `command` string, and updating only the
     `command` field of an existing, stale entry in place — every other
     key in every file, and every other entry in every hook array, is
     left exactly as it was.
   - Is safe to run any number of times: a file is only ever written if
     something in it actually needs to change; already-correct state
     produces zero writes.
   - Supports `--dry-run`/`-n` to preview every change with zero writes.
2. `README.md`'s "One-time setup" section is replaced with the single
   `python3 Scripts/harness/install.py` invocation.
3. `Scripts/harness/hooks/README.md` is corrected to describe the three
   global config files as maintained by `install.py`, not hand-edited —
   re-running it after a move is the prescribed fix, not manual editing.
4. `claude/skills/onboard-project/SKILL.md`'s hardcoded path is replaced
   with a shell one-liner that resolves the Harness's current root at
   runtime via the `~/.claude/agents` symlink
   (`dirname "$(dirname "$(readlink -f ~/.claude/agents)")"`) — a
   mechanism that is correct by construction precisely because
   `install.py` is now what keeps that symlink's target current. The
   skill's original explanation of *why* a dynamic resolution is needed
   (the `${CLAUDE_PROJECT_DIR}` limitation) is preserved; only *how* it
   resolves changes.

## Alternatives considered

- **Keep the README bash snippet, just add `-f` to every `ln -s` (force
  overwrite).** Rejected — `ln -sf` blindly overwrites whatever is at the
  target, including a real file or directory that isn't a stale symlink at
  all (again, the actual live `~/.cursor/agents` case: it's an empty real
  directory, not a broken symlink, and force-overwriting it would silently
  destroy whatever expectation created that directory in the first place,
  even though today it happens to be empty). A script that distinguishes
  "stale symlink" from "real file/dir I don't understand" and only acts on
  the former is strictly safer for the same amount of effort.
- **Bash instead of Python for `install.py`.** Rejected per
  `Scripts/shared/README.md`'s own stated default: JSON merging that must
  preserve unrelated keys and array entries exactly, while matching
  already-present hook entries by exact basename, is real logic with real
  data structures — not thin CLI orchestration. `jq` could technically do
  this, but the matching-then-conditional-mutate logic needed here is
  substantially more legible as Python dict/list manipulation than as
  `jq` filter expressions, and this repo's own convention already draws
  that exact line.
- **Have the onboarding skill shell out to `install.py --print-root` (a
  new flag) instead of the `readlink`/`dirname` one-liner.** Considered,
  not chosen for this pass — it would require `install.py` to already have
  been run successfully (same dependency the chosen approach also has) but
  adds an extra process invocation for something two `dirname` calls on an
  already-guaranteed symlink solve directly. Not ruled out as a future
  simplification if the shell one-liner turns out fragile in practice, but
  judged sufficient without adding a new CLI surface for a single caller.
- **Fold `index_rebuild.py` into `install.py` as a final step.** Considered
  and left out — `README.md`'s updated setup section keeps them as two
  separate invocations. Index rebuilding is a different concern (search-
  index population) from symlink/hook-config reconciliation, and folding
  the former in would be scope creep on a script meant to stay narrowly
  about path portability.

## Consequences

- The harness can now be moved, recloned, or reorganized an arbitrary
  number of times, with `python3 Scripts/harness/install.py` as the single
  command that brings every symlink and every global hook config file back
  in sync with the new location — no more hand-editing three JSON files or
  re-running a bash snippet that fails the second time.
- `claude/skills/onboard-project/SKILL.md` now has a real, if narrow,
  runtime dependency on `install.py` having been run at least once on the
  current clone (so `~/.claude/agents` actually points at the current
  root) — a dependency that did not exist with the old hardcoded string
  (which was self-contained, just wrong the moment the repo moved). This
  is accepted as a reasonable trade: `install.py` is this harness's own
  one-time-per-clone setup step, so any session capable of invoking the
  onboarding skill has almost certainly already run it.
- The one case `install.py` cannot resolve automatically — a symlink
  target that's actually a real file or directory — surfaces as an
  explicit, itemized report line telling the user exactly what to check
  and how to resolve it by hand, rather than either silently overwriting
  it (the rejected `ln -sf` alternative) or crashing uninformatively.
- Three global JSON config files gain a genuine, tooling-enforced
  invariant they didn't have before: re-running `install.py` after any
  edit made by hand elsewhere will detect and correct any path that no
  longer matches the current clone location, on every run, indefinitely.
