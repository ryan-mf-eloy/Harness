# Harness

A local, provider-agnostic control plane for daily development work: shared
engineering conventions, an Obsidian vault unified with Claude Code's native
auto-memory, a SQLite FTS5 index for cheap search, an immutable RAG
source-of-truth folder, a secrets-by-label convention, reusable scripts, and
a roster of specialist subagents — all designed to be deployed once
(`~/.claude/`) and reused across every project.

## Layout

```
AGENTS.md            canonical, cross-tool instructions (start here)
CLAUDE.md             thin Claude Code pointer to AGENTS.md
claude/               agents/ skills/ rules/ — symlinked into ~/.claude/
Vault/                Obsidian vault: memory + documentation
RAG/                  immutable business/domain source of truth
Secrets/              label manifest only, never values
Scripts/              harness/ (self-maintenance) + shared/ (cross-project utilities)
Artifacts/            generated media/output, namespaced by project + month
Index/                derived SQLite FTS5 index (gitignored, rebuildable)
Codebase/             registry of real project repos (not cloned in here)
templates/            AGENTS.md / CLAUDE.md / PR templates for onboarding a new project
```

## One-time setup

```bash
mkdir -p ~/.claude
ln -s "$PWD/claude/agents" ~/.claude/agents
ln -s "$PWD/claude/skills" ~/.claude/skills
ln -s "$PWD/claude/rules"  ~/.claude/rules
python3 Scripts/harness/index_rebuild.py
```

See `AGENTS.md` for the full operating contract.
