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
CLAUDE.md             thin Claude Code pointer: @AGENTS.md
.cursorrules, .cursor/rules/agents.mdc   thin Cursor pointer: see AGENTS.md
ONBOARDING.md         full procedure for onboarding a new project onto the harness
principles/           PRINCIPLES.md — the actual rules content, provider-agnostic
claude/               agents/ skills/ — Claude-Code-specific packaging, symlinked into ~/.claude/
.cursor/agents/       Cursor-specific subagent translations, symlinked into ~/.cursor/agents/
.codex/agents/        Codex-CLI-specific subagent translations (TOML), symlinked into ~/.codex/agents/
.agents/skills        symlink to claude/skills — shared discovery path Cursor + Codex CLI both scan
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
mkdir -p ~/.agents
ln -s "$PWD/claude/agents"          ~/.claude/agents
ln -s "$PWD/claude/skills"          ~/.claude/skills
ln -s "$PWD/claude/skills"          ~/.agents/skills       # global reach for Cursor + Codex CLI skill discovery
ln -s "$PWD/principles/PRINCIPLES.md" ~/.claude/CLAUDE.md   # global reach for Claude Code
ln -s "$PWD/principles/PRINCIPLES.md" ~/.codex/AGENTS.md    # global reach for Codex CLI
python3 Scripts/harness/index_rebuild.py
```

Cursor has no confirmed file-based *global* rules slot (only per-project
`AGENTS.md`/`.cursor/rules/` and an in-app "User Rules" setting) — if you
want Cursor to see these principles in every project, paste
`principles/PRINCIPLES.md` into Cursor's Settings → Rules once, by hand.

See `AGENTS.md` for the full operating contract, and its
"Provider-agnostic by construction" section for exactly how each tool
reaches these principles.
