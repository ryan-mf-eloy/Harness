@AGENTS.md

## Claude Code

This repo's `claude/agents/`, `claude/skills/`, and `claude/rules/` are
symlinked into `~/.claude/{agents,skills,rules}` — treat edits made under
either path as editing the same versioned file. See
`Scripts/harness/README.md` for the one-time symlink setup command.

When working on the harness's own scripts (indexer, hooks, guards), run
`python3 Scripts/harness/index_rebuild.py --check` before considering a
change to those scripts complete.
