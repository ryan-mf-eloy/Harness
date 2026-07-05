#!/usr/bin/env python3
"""Onboard a new (or existing) project onto the Harness conventions.

Usage:
  onboard.py <project-slug> <absolute-path-to-project-root>

What it does:
  1. Writes <project>/AGENTS.md from templates/AGENTS.md.template, with the
     HARNESS:PRINCIPLES block stamped in verbatim from
     principles/PRINCIPLES.md — Cursor and Codex CLI only read a project's
     own AGENTS.md, they don't follow cross-directory imports, so the
     content has to physically live there.
  2. Writes <project>/CLAUDE.md from templates/CLAUDE.md.template (a thin
     @AGENTS.md pointer, for Claude Code).
  3. Writes <project>/.cursorrules (thin pointer, for Cursor).
  4. Ensures <project>/.claude/settings.json sets autoMemoryDirectory into
     this repo's Vault/40-Memory/<slug>/, creating that folder first.
  5. Prints a reminder to add a row to Codebase/REGISTRY.md (not automated,
     since the registry's other columns — status, notes — need a human
     judgment call, not a guessed default).

Re-running this script on an already-onboarded project refreshes the
stamped principles block and leaves everything else untouched (it does not
overwrite AGENTS.md/CLAUDE.md wholesale — only the HARNESS:PRINCIPLES block
inside an existing AGENTS.md, if one already exists).
"""
from __future__ import annotations

import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[3]
PRINCIPLES = HARNESS_ROOT / "principles" / "PRINCIPLES.md"
AGENTS_TEMPLATE = HARNESS_ROOT / "templates" / "AGENTS.md.template"
CLAUDE_TEMPLATE = HARNESS_ROOT / "templates" / "CLAUDE.md.template"

BEGIN_MARKER = "<!-- HARNESS:PRINCIPLES:BEGIN"
END_MARKER = "<!-- HARNESS:PRINCIPLES:END -->"


def stamp_principles(agents_md_text: str) -> str:
    principles_text = PRINCIPLES.read_text(encoding="utf-8").strip()
    begin_idx = agents_md_text.find(BEGIN_MARKER)
    end_idx = agents_md_text.find(END_MARKER)
    if begin_idx == -1 or end_idx == -1:
        raise ValueError(
            "AGENTS.md has no HARNESS:PRINCIPLES:BEGIN/END markers to stamp into. "
            "Add them (see templates/AGENTS.md.template) before running this script."
        )
    begin_line_end = agents_md_text.find("\n", begin_idx) + 1
    # find the closing '-->' of the BEGIN comment block, then keep everything
    # from there up to END_MARKER replaced by the stamped content
    comment_close = agents_md_text.find("-->", begin_idx) + len("-->")
    before = agents_md_text[:comment_close]
    after = agents_md_text[end_idx:]
    return f"{before}\n\n{principles_text}\n\n{after}"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1

    slug, project_root = sys.argv[1], Path(sys.argv[2]).resolve()
    if not project_root.exists():
        print(f"ERROR: {project_root} does not exist.", file=sys.stderr)
        return 1

    agents_path = project_root / "AGENTS.md"
    if agents_path.exists():
        text = agents_path.read_text(encoding="utf-8")
        print(f"AGENTS.md already exists at {agents_path} — refreshing stamped principles block only.")
    else:
        text = AGENTS_TEMPLATE.read_text(encoding="utf-8")
        text = text.replace("<Project Name>", slug)

    agents_path.write_text(stamp_principles(text), encoding="utf-8")
    print(f"wrote {agents_path}")

    claude_path = project_root / "CLAUDE.md"
    if not claude_path.exists():
        claude_path.write_text(CLAUDE_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"wrote {claude_path}")

    cursorrules_path = project_root / ".cursorrules"
    if not cursorrules_path.exists():
        cursorrules_path.write_text("See AGENTS.md.\n", encoding="utf-8")
        print(f"wrote {cursorrules_path}")

    memory_dir = HARNESS_ROOT / "Vault" / "40-Memory" / slug
    memory_dir.mkdir(parents=True, exist_ok=True)
    print(f"ensured {memory_dir}")

    claude_dir = project_root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"
    if not settings_path.exists():
        settings_path.write_text(
            '{\n  "autoMemoryDirectory": "' + str(memory_dir) + '"\n}\n',
            encoding="utf-8",
        )
        print(f"wrote {settings_path}")
    else:
        print(f"{settings_path} already exists — not overwriting; "
              f"add \"autoMemoryDirectory\": \"{memory_dir}\" to it by hand if missing.")

    print()
    print(f"Next: add a row for '{slug}' to {HARNESS_ROOT / 'Codebase' / 'REGISTRY.md'} by hand "
          f"(status and notes need a human judgment call).")
    print("Also accept the workspace-trust dialog once in this project "
          "(required for autoMemoryDirectory to take effect).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
