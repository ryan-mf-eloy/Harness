---
type: reference
tags: [vault]
status: active
created: 2026-07-05
---

# 10-Projects

STRUCTURE placeholder — one subfolder per active project, created when that
project is onboarded (see `Codebase/REGISTRY.md` and `templates/`):

```
10-Projects/<project-slug>/
├── decisions/       # ADR-style notes, using the Decision template
├── investigations/  # debugging/research logs, using the Investigation template
└── meetings/        # using the Meeting template
```

These are your own hand-written notes about the project. Claude Code's own
auto-memory for that project lives separately, in
`../40-Memory/<project-slug>/` — don't merge the two folders. See
`00-System/Frontmatter Taxonomy.md` for the frontmatter every note here should
carry.
