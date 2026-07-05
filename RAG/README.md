---
type: reference
tags: [rag, policy]
status: active
created: 2026-07-05
---

# RAG — Source of Truth

Files under `RAG/business/<project-slug>/` are treated as near-immutable
ground truth for that project's business domain: pricing rules, compliance
constraints, contractual facts, canonical definitions — anything that, if an
agent silently "corrected," paraphrased, or drifted while summarizing it,
would introduce a dangerous factual error downstream.

## STRUCTURE placeholder

This folder is intentionally empty of real content — no project exists yet
to populate it with. When a real project is onboarded, a project-scoped
agent session (or you, by hand) should:

1. Create `RAG/business/<project-slug>/`.
2. Add one file per distinct fact area (e.g. `pricing-rules.md`,
   `compliance-constraints.md`), each with this frontmatter:
   ```yaml
   ---
   type: reference
   source: rag
   project: <project-slug>
   last_verified: YYYY-MM-DD
   owner: <who/what confirmed this fact>
   ---
   ```
3. Never invent facts here speculatively — only record what has actually
   been confirmed against a canonical source (a spec, a contract, a domain
   expert), and record that source.

## Immutability policy

Direct edits are blocked by a `PreToolUse` hook
(`Scripts/harness/guard_rag_immutable.py`, wired in
this repo's own `.claude/settings.json`) that denies `Write`/`Edit`/destructive
`Bash` under `RAG/**`, regardless of what the model decides. This is backed
by a second, independent layer: run `chmod -R a-w RAG/` at the filesystem
level once real content exists, so even a different tool or a stray script
can't silently mutate it.

## Making a legitimate change

There is no bundled "override skill" yet — that's intentionally left for
when a real project needs one, since the exact override ergonomics (who
approves, what gets logged) may want to match that project's own risk
tolerance. Until then, the manual override procedure is:

```bash
chmod -R u+w RAG/
# make the edit
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) — <path> — <who> — <why>" >> RAG/_meta/override-log.md
chmod -R a-w RAG/
```

## Indexing

`RAG/**/*.md` is indexed by the same SQLite FTS5 index as `Vault/`, tagged
`source: rag` (see `Scripts/harness/index_rebuild.py`), so a query can
restrict to authoritative facts specifically, or a result can visibly show
which source it came from.

## Honest scope of this guard

The `PreToolUse` hook blocks the normal editing path: Claude's own
Write/Edit/MultiEdit tools, and Bash commands matching common destructive
patterns (remove, move, truncate, shred, output redirection). It does not
attempt to catch every conceivable way to write a file from Bash (e.g. a
language runtime writing a file directly, or a command whose text happens
to be built up dynamically rather than typed literally) -- no hook can
fully sandbox an agent that has general Bash access. Treat this as a strong
deterrent against the common paths, not an absolute guarantee; the
filesystem permission lock is the backstop for anything the hook doesn't
catch.

