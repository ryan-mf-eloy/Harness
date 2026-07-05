# Artifacts

Organized storage for anything an agent generates as output: images,
reports, exported data, one-off diagrams.

## Layout

```
Artifacts/<project-slug>/YYYY-MM/YYYY-MM-DD_<short-slug>.<ext>
Artifacts/_unscoped/YYYY-MM/                # harness-level or exploratory generations
```

`<project-slug>` matches the same identifier used in `Codebase/REGISTRY.md`,
`Secrets/manifest.yaml`, and `Vault/40-Memory/`. The `YYYY-MM/` folder keeps
any single directory from accumulating thousands of files, which matters for
Finder/Obsidian responsiveness and for Dropbox sync overhead on folders with
huge file counts.

## Retention policy

An artifact with no incoming link from any Vault note is a candidate for
deletion after 90 days. The Obsidian backlink graph is the actual source of
truth for "is this still needed" — if it's referenced from a note, it
survives regardless of age; if not, it's disposable. There is no automated
pruning script yet; treat this as a manual periodic check until/unless one
is worth writing.
