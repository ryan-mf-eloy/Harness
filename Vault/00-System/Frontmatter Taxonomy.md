---
type: reference
tags: [vault, taxonomy]
status: active
created: 2026-07-05
---

# Frontmatter Taxonomy

Every note in this vault should carry this frontmatter block:

```yaml
---
type: meeting | learning | error | investigation | decision | reference | memory
project: <project-slug>   # omit for harness-wide notes not tied to one project
tags: []
status: active | superseded | archived
created: YYYY-MM-DD
---
```

## Field meanings

- **type** — what kind of note this is. Drives which template it started
  from (see `00-System/Templates/`) and helps FTS queries filter results.
- **project** — must match the slug used in `Codebase/REGISTRY.md`,
  `Secrets/manifest.yaml`, and `Artifacts/<slug>/`. One identifier, reused
  everywhere, so a search or a script can join across all of them.
- **tags** — freeform topical tags (e.g. `[sqlite, hooks, macos]`), not a
  substitute for `type` or `project`.
- **status** — `active` unless the note has been superseded by a newer
  decision/investigation (mark the old one `superseded` and link forward) or
  is no longer relevant (`archived`, and move it to `90-Archive/`).
- **created** — the date the note was first written, not last edited.
  Obsidian/filesystem metadata already tracks modification time.

## `40-Memory/` is the one exception

Files under `40-Memory/<slug>/` are written by Claude Code's own auto-memory
mechanism, not by hand, and will not carry this frontmatter unless you add it
yourself. That's fine — leave `MEMORY.md` and its topic files as Claude
writes them. Retrofitting frontmatter there is optional and never required.
