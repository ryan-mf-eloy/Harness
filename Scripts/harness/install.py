#!/usr/bin/env python3
"""Idempotent installer for this harness — safe to run once per clone,
after a move/reclone, or any number of times with no drift.

Replaces the old README.md "One-time setup" copy-paste bash block, which
worked once but could not be safely re-run: its `ln -s` calls fail with
"File exists" the moment the repo moves to a new location and the
symlinks still point at the old one. This script fixes that by never
assuming an empty slate — every operation below checks current state
first and only acts on the actual gap between "what exists now" and
"what should exist, given this clone's current location."

Two independent jobs, both idempotent on their own:

1. Create/refresh the global symlinks Claude Code, Cursor, and Codex CLI
   discovery paths depend on (see SYMLINKS below — sourced verbatim from
   README.md's setup block, not re-derived).
2. Merge this harness's global hook entries into the three tools' global
   config files (~/.claude/settings.json, ~/.cursor/hooks.json,
   ~/.codex/hooks.json), updating only the harness-owned entries and
   never touching unrelated content in those files.

Run with --dry-run to preview every change without writing anything.

This script deliberately does NOT touch this repo's own project-scoped
.claude/settings.json / .cursor/hooks.json / .codex/hooks.json — those
already use ${CLAUDE_PROJECT_DIR}/${CURSOR_PROJECT_DIR} correctly (see
Scripts/harness/hooks/README.md) and need no path-fixing at all.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Scripts/harness/install.py is 2 levels below the Harness root — same
# depth as Scripts/harness/_index_common.py (which uses parents[2]), NOT
# the same depth as Scripts/harness/hooks/_reinforcement_common.py (3
# levels down, parents[3]).
ROOT = Path(__file__).resolve().parents[2]

HOOKS_DIR = ROOT / "Scripts" / "harness" / "hooks"

# ---------------------------------------------------------------------------
# 1. Symlinks — sourced verbatim from README.md's "One-time setup" block.
#    (target_path, source_path). If README.md's list ever changes, update
#    it there first and mirror the change here — this list must never
#    drift from that one.
# ---------------------------------------------------------------------------

HOME = Path.home()

SYMLINKS: list[tuple[Path, Path]] = [
    (HOME / ".claude" / "agents", ROOT / "claude" / "agents"),
    (HOME / ".claude" / "skills", ROOT / "claude" / "skills"),
    (HOME / ".agents" / "skills", ROOT / "claude" / "skills"),
    (HOME / ".cursor" / "agents", ROOT / ".cursor" / "agents"),
    (HOME / ".codex" / "agents", ROOT / ".codex" / "agents"),
    (HOME / ".claude" / "CLAUDE.md", ROOT / "principles" / "PRINCIPLES.md"),
    (HOME / ".codex" / "AGENTS.md", ROOT / "principles" / "PRINCIPLES.md"),
]

# ---------------------------------------------------------------------------
# 2. Known hook scripts, split by scope — mirrors Scripts/harness/hooks/
#    README.md's table exactly. Only "global" entries are used by this
#    script; "project" entries are listed here only so this registry can be
#    visually cross-checked against that table by a human, never acted on.
# ---------------------------------------------------------------------------

GLOBAL_SCRIPTS = {
    "block_destructive_bash.py",
    "reinforce_principles.py",
    "reinforce_principles_cursor.py",
    "reinforce_principles_codex.py",
    "check_tests_and_revalidation.py",
    "check_tests_and_revalidation_codex.py",
}

PROJECT_SCOPED_SCRIPTS = {
    # Wired only into this repo's own .claude/settings.json / .cursor/hooks.json
    # / .codex/hooks.json via ${CLAUDE_PROJECT_DIR}/${CURSOR_PROJECT_DIR} —
    # never global. Listed here only for cross-checking against
    # Scripts/harness/hooks/README.md; install.py must never add these to
    # any of the three global files below.
    "guard_rag_immutable.py",
    "index_upsert.py",
}


def _hook_command(script_name: str) -> str:
    """The exact command string this harness wires up for a given script,
    given this run's current ROOT. Single source of truth for the command
    shape so the three merge functions below can never disagree on it."""
    return f'python3 "{HOOKS_DIR / script_name}"'


# ---------------------------------------------------------------------------
# Claude Code: ~/.claude/settings.json
# ---------------------------------------------------------------------------

CLAUDE_SETTINGS_HOOKS: dict[str, list[dict[str, Any]]] = {
    "SessionStart": [
        {"matcher": None, "script": "reinforce_principles.py"},
    ],
    "PreToolUse": [
        {"matcher": "Bash", "script": "block_destructive_bash.py"},
        {"matcher": "Edit|Write|MultiEdit", "script": "reinforce_principles.py"},
    ],
    "Stop": [
        {"matcher": None, "script": "check_tests_and_revalidation.py"},
    ],
}


def merge_claude_settings(path: Path, dry_run: bool) -> list[str]:
    """Merge harness hook entries into ~/.claude/settings.json without
    touching any other key (permissions, enabledPlugins, etc.)."""
    report: list[str] = []
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.append(
                f"SKIPPED {path}: not valid JSON ({exc}) — resolve by hand, "
                "install.py will not overwrite a file it can't safely parse."
            )
            return report

    hooks = data.setdefault("hooks", {})
    changed = False

    for event, entries in CLAUDE_SETTINGS_HOOKS.items():
        event_list = hooks.setdefault(event, [])
        for entry_spec in entries:
            matcher = entry_spec["matcher"]
            script = entry_spec["script"]
            command = _hook_command(script)

            target_block = None
            for block in event_list:
                if block.get("matcher") == matcher:
                    target_block = block
                    break

            if target_block is None:
                new_block: dict[str, Any] = {"hooks": [{"type": "command", "command": command}]}
                if matcher is not None:
                    new_block = {"matcher": matcher, "hooks": new_block["hooks"]}
                event_list.append(new_block)
                changed = True
                report.append(f"CREATED {event}/{matcher or '(no matcher)'} -> {script}")
                continue

            inner_hooks = target_block.setdefault("hooks", [])
            existing_entry = None
            for h in inner_hooks:
                cmd = h.get("command", "")
                if cmd.rsplit("/", 1)[-1].rstrip('"') == script:
                    existing_entry = h
                    break

            if existing_entry is None:
                inner_hooks.append({"type": "command", "command": command})
                changed = True
                report.append(f"CREATED {event}/{matcher or '(no matcher)'} -> {script}")
            elif existing_entry.get("command") != command:
                existing_entry["command"] = command
                changed = True
                report.append(f"REFRESHED {event}/{matcher or '(no matcher)'} -> {script} (stale path corrected)")
            else:
                report.append(f"OK {event}/{matcher or '(no matcher)'} -> {script} (already correct)")

    if changed and not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    elif changed and dry_run:
        report.append(f"(dry-run: would write {path})")

    return report


# ---------------------------------------------------------------------------
# Cursor: ~/.cursor/hooks.json
# ---------------------------------------------------------------------------

CURSOR_HOOKS: dict[str, list[dict[str, Any]]] = {
    "preToolUse": [
        {"matcher": "Shell", "script": "block_destructive_bash.py"},
    ],
    "sessionStart": [
        {"matcher": None, "script": "reinforce_principles_cursor.py"},
    ],
    "postToolUse": [
        {"matcher": None, "script": "reinforce_principles_cursor.py", "extra": {"failClosed": False}},
    ],
}


def merge_cursor_hooks(path: Path, dry_run: bool) -> list[str]:
    """Merge harness hook entries into ~/.cursor/hooks.json. Cursor's shape
    is flatter than Claude Code's: hooks.<event> is directly a list of
    {matcher?, command, type, ...} entries, no nested "hooks" wrapper."""
    report: list[str] = []
    data: dict[str, Any] = {"version": 1}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.append(
                f"SKIPPED {path}: not valid JSON ({exc}) — resolve by hand."
            )
            return report

    data.setdefault("version", 1)
    hooks = data.setdefault("hooks", {})
    changed = False

    for event, entries in CURSOR_HOOKS.items():
        event_list = hooks.setdefault(event, [])
        for entry_spec in entries:
            matcher = entry_spec["matcher"]
            script = entry_spec["script"]
            command = _hook_command(script)
            extra = entry_spec.get("extra", {})

            existing_entry = None
            for h in event_list:
                cmd = h.get("command", "")
                same_matcher = h.get("matcher") == matcher
                same_script = cmd.rsplit("/", 1)[-1].rstrip('"') == script
                if same_matcher and same_script:
                    existing_entry = h
                    break

            if existing_entry is None:
                new_entry: dict[str, Any] = {"command": command, "type": "command", **extra}
                if matcher is not None:
                    new_entry = {"matcher": matcher, **new_entry}
                event_list.append(new_entry)
                changed = True
                report.append(f"CREATED {event}/{matcher or '(no matcher)'} -> {script}")
            elif existing_entry.get("command") != command:
                existing_entry["command"] = command
                changed = True
                report.append(f"REFRESHED {event}/{matcher or '(no matcher)'} -> {script} (stale path corrected)")
            else:
                report.append(f"OK {event}/{matcher or '(no matcher)'} -> {script} (already correct)")

    if changed and not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    elif changed and dry_run:
        report.append(f"(dry-run: would write {path})")

    return report


# ---------------------------------------------------------------------------
# Codex CLI: ~/.codex/hooks.json
# ---------------------------------------------------------------------------

CODEX_HOOKS: dict[str, list[dict[str, Any]]] = {
    "SessionStart": [
        {"matcher": None, "script": "reinforce_principles_codex.py"},
    ],
    "PreToolUse": [
        {"matcher": "Bash", "script": "block_destructive_bash.py"},
        {"matcher": "apply_patch|Edit|Write", "script": "reinforce_principles_codex.py"},
    ],
    "Stop": [
        {"matcher": None, "script": "check_tests_and_revalidation_codex.py"},
    ],
}


def merge_codex_hooks(path: Path, dry_run: bool) -> list[str]:
    """Merge harness hook entries into ~/.codex/hooks.json. Codex's shape
    mirrors Claude Code's exactly (nested hooks.<Event>[].hooks[] list)."""
    report: list[str] = []
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.append(
                f"SKIPPED {path}: not valid JSON ({exc}) — resolve by hand."
            )
            return report

    hooks = data.setdefault("hooks", {})
    changed = False

    for event, entries in CODEX_HOOKS.items():
        event_list = hooks.setdefault(event, [])
        for entry_spec in entries:
            matcher = entry_spec["matcher"]
            script = entry_spec["script"]
            command = _hook_command(script)

            target_block = None
            for block in event_list:
                if block.get("matcher") == matcher:
                    target_block = block
                    break

            if target_block is None:
                new_block: dict[str, Any] = {"hooks": [{"type": "command", "command": command}]}
                if matcher is not None:
                    new_block = {"matcher": matcher, "hooks": new_block["hooks"]}
                event_list.append(new_block)
                changed = True
                report.append(f"CREATED {event}/{matcher or '(no matcher)'} -> {script}")
                continue

            inner_hooks = target_block.setdefault("hooks", [])
            existing_entry = None
            for h in inner_hooks:
                cmd = h.get("command", "")
                if cmd.rsplit("/", 1)[-1].rstrip('"') == script:
                    existing_entry = h
                    break

            if existing_entry is None:
                inner_hooks.append({"type": "command", "command": command})
                changed = True
                report.append(f"CREATED {event}/{matcher or '(no matcher)'} -> {script}")
            elif existing_entry.get("command") != command:
                existing_entry["command"] = command
                changed = True
                report.append(f"REFRESHED {event}/{matcher or '(no matcher)'} -> {script} (stale path corrected)")
            else:
                report.append(f"OK {event}/{matcher or '(no matcher)'} -> {script} (already correct)")

    if changed and not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    elif changed and dry_run:
        report.append(f"(dry-run: would write {path})")

    return report


# ---------------------------------------------------------------------------
# Symlink reconciliation
# ---------------------------------------------------------------------------

def reconcile_symlink(target: Path, source: Path, dry_run: bool) -> str:
    """Return one report line. Never touches a real (non-symlink) file or
    directory — reports it and moves on."""
    if target.is_symlink():
        current = target.resolve()
        if current == source.resolve():
            return f"OK      {target} (already -> {source})"
        if dry_run:
            return f"WOULD REFRESH {target}: -> {current} (stale) => {source}"
        target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
        return f"REFRESHED {target}: was -> {current} (stale), now -> {source}"

    if target.exists():
        kind = "directory" if target.is_dir() else "file"
        return (
            f"SKIPPED {target}: exists as a real {kind}, not a symlink — "
            f"not touching it automatically. Resolve by hand (confirm it's "
            f"safe to remove, e.g. `rmdir {target}` if empty, or move its "
            f"contents first), then re-run this script."
        )

    if dry_run:
        return f"WOULD CREATE {target} -> {source}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source)
    return f"CREATED {target} -> {source}"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Preview every change without writing or symlinking anything.",
    )
    args = parser.parse_args()

    print(f"Harness root: {ROOT}")
    print(f"{'(dry run) ' if args.dry_run else ''}Reconciling symlinks...\n")

    for target, source in SYMLINKS:
        print("  " + reconcile_symlink(target, source, args.dry_run))

    print(f"\n{'(dry run) ' if args.dry_run else ''}Merging global hook config...\n")

    print("  ~/.claude/settings.json:")
    for line in merge_claude_settings(HOME / ".claude" / "settings.json", args.dry_run):
        print(f"    {line}")

    print("\n  ~/.cursor/hooks.json:")
    for line in merge_cursor_hooks(HOME / ".cursor" / "hooks.json", args.dry_run):
        print(f"    {line}")

    print("\n  ~/.codex/hooks.json:")
    for line in merge_codex_hooks(HOME / ".codex" / "hooks.json", args.dry_run):
        print(f"    {line}")

    print(
        "\nDone."
        + (" (dry run — nothing was actually written)" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
