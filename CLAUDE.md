@AGENTS.md

## Claude Code

This repo's `claude/agents/` and `claude/skills/` are symlinked into
`~/.claude/{agents,skills}`, and `~/.claude/CLAUDE.md` is symlinked to
`principles/PRINCIPLES.md` — treat edits made under any of these paths as
editing the same versioned file. See `README.md` for the one-time symlink
setup commands.

When working on the harness's own scripts (indexer, hooks, guards), run
`python3 Scripts/harness/index_rebuild.py --check` before considering a
change to those scripts complete.
