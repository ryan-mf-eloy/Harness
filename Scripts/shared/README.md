# Scripts/shared/ — graduated cross-project routines

An ad hoc routine "graduates" into a script here once the same 3+-step
sequence has been repeated across two or more sessions or projects — that's
a judgment call, not something to automate precisely, but the FTS index
helps make the call cheaply: before writing a new script, query it first
(`python3 Scripts/harness/query.py "<what you're about to automate>" --source project-docs`
won't find these — query the plain filenames/READMEs directly with `grep -r`
across `Scripts/shared/*/README.md`, or extend `index_rebuild.py`'s glob to
include this folder if it's worth indexing formally).

## Convention

```
Scripts/shared/<verb-noun-slug>/
├── README.md      # what it does, when to reach for it, how to invoke it
└── <script>.{sh,py}
```

Each `README.md` follows this fixed minimal shape:

```markdown
# <verb-noun-slug>

**What:** one sentence.
**When:** the trigger condition for reaching for this instead of doing it by hand.
**Invoke:** exact command.
**Depends on:** any CLI tools/credentials it assumes are already set up.
```

## Default language

**Bash for thin CLI orchestration, Python for anything with real logic**
(parsing, data structures, SQLite) — this is the harness-level default for
cross-project utilities only. A specific project under `Codebase/<slug>/`
should use whatever language/stack that project already uses for its own
scripts; don't force this default onto project-specific tooling.
