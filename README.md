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
claude/               agents/ skills/ — Claude-Code-specific packaging, each entry mirrored via its own symlink into ~/.claude/agents/ and ~/.claude/skills/ (which stay real directories — see install.py)
.cursor/agents/       Cursor-specific subagent translations, each mirrored into ~/.cursor/agents/
.codex/agents/        Codex-CLI-specific subagent translations (TOML), each mirrored into ~/.codex/agents/
.agents/skills        symlink to ~/.claude/skills — shared discovery path Cursor + Codex CLI both scan
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
python3 Scripts/harness/install.py
```

This ensures `~/.claude/agents`, `~/.claude/skills`, `~/.cursor/agents`,
and `~/.codex/agents` are real directories (never a symlink straight into
this repo — that lets any *other* tool install its own skills/agents
there too, alongside the harness's own, without landing inside this
repo's git tree), each populated with one symlink per harness-owned
entry; sets up `~/.agents/skills` (aliased to `~/.claude/skills`),
`~/.claude/CLAUDE.md`, and `~/.codex/AGENTS.md`; and merges this
harness's global hook entries into `~/.claude/settings.json`,
`~/.cursor/hooks.json`, and `~/.codex/hooks.json` — without touching any
unrelated content already in those files. Idempotent: safe to run again
after moving, recloning, or reorganizing this repo (it will refresh
anything now pointing at a stale location) and safe to run repeatedly
with no effect once everything is already correct. Run
`python3 Scripts/harness/install.py --dry-run` first if you want to
preview what it would change before it changes anything.

Also run once, to build the search index:
```bash
python3 Scripts/harness/index_rebuild.py
```

Cursor has no confirmed file-based *global* rules slot (only per-project
`AGENTS.md`/`.cursor/rules/` and an in-app "User Rules" setting) — if you
want Cursor to see these principles in every project, paste
`principles/PRINCIPLES.md` into Cursor's Settings → Rules once, by hand.

See `AGENTS.md` for the full operating contract, and its
"Provider-agnostic by construction" section for exactly how each tool
reaches these principles.
