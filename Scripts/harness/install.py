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

1. Create/refresh the global directories and symlinks Claude Code, Cursor,
   and Codex CLI discovery paths depend on (see DIRECTORY_MIRRORS,
   ALIAS_SYMLINKS, FILE_SYMLINKS below — sourced verbatim from README.md's
   setup block, not re-derived).
2. Merge this harness's global hook entries into the three tools' global
   config files (~/.claude/settings.json, ~/.cursor/hooks.json,
   ~/.codex/hooks.json), updating only the harness-owned entries and
   never touching unrelated content in those files.

Run with --dry-run to preview every change without writing anything.

This script deliberately does NOT touch this repo's own project-scoped
.claude/settings.json / .cursor/hooks.json / .codex/hooks.json — those
already use ${CLAUDE_PROJECT_DIR}/${CURSOR_PROJECT_DIR} correctly (see
Scripts/harness/hooks/README.md) and need no path-fixing at all.

IMPORTANT, learned the hard way: ~/.claude/agents, ~/.claude/skills,
~/.cursor/agents, and ~/.codex/agents are never made whole-directory
symlinks straight into this harness repo. An earlier version of this
script did exactly that, and the very first time a third-party tool
installed something new into one of those directories (the community
`caveman` skill, installed via its own official installer), it wrote its
files transparently THROUGH the symlink, landing them inside this
harness's own git-tracked claude/skills/ folder. DIRECTORY_MIRRORS below
fixes this: each of those four stays (or becomes) a REAL directory, with
one symlink per harness-owned entry inside it — so anything else another
tool installs alongside sits there as ordinary, real, non-harness files,
never inside this repo. See
Vault/00-System/decisions/2026-07-06-directory-mirror-not-whole-symlink.md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
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
# 1. Directories, aliases, and file symlinks — sourced verbatim from
#    README.md's "One-time setup" block. If that list ever changes, update
#    it there first and mirror the change here — these must never drift
#    from that one.
# ---------------------------------------------------------------------------

HOME = Path.home()

# Directories where this harness contributes some entries but OTHER tools
# may also install their own entries alongside them (a skill marketplace,
# a plugin manager, a manual install). Each of these stays a REAL
# directory — never a symlink to the harness itself — with one symlink per
# harness-owned entry created inside it. This is the fix for the bug
# described in the module docstring above.
DIRECTORY_MIRRORS: list[tuple[Path, Path]] = [
    (HOME / ".claude" / "agents", ROOT / "claude" / "agents"),
    (HOME / ".claude" / "skills", ROOT / "claude" / "skills"),
    (HOME / ".cursor" / "agents", ROOT / ".cursor" / "agents"),
    (HOME / ".codex" / "agents", ROOT / ".codex" / "agents"),
]

# Symlinks whose SOURCE is one of the real (non-harness) directories above,
# not the harness directly — safe as a whole-directory symlink, since
# anything written through it lands in that already-real, already-shared
# directory, never inside this repo's own git tree.
ALIAS_SYMLINKS: list[tuple[Path, Path]] = [
    (HOME / ".agents" / "skills", HOME / ".claude" / "skills"),
]

# Pure file symlinks — no "shared directory" risk, since a file can't
# contain other unrelated content the way a directory can.
FILE_SYMLINKS: list[tuple[Path, Path]] = [
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
    "guard_infra_mutation.py",
    "guard_remote_automation.py",
    "reinforce_principles.py",
    "reinforce_principles_cursor.py",
    "reinforce_principles_codex.py",
    "check_tests_and_revalidation.py",
    "check_tests_and_revalidation_codex.py",
}

# Matcher string for infra-mutating MCP tool calls (Cloudflare/Supabase/Vercel)
# — must stay in sync with guard_infra_mutation.py's MCP_INFRA_MUTATION_RE.
# Only confirmed to work as a PreToolUse matcher on Claude Code; Cursor's and
# Codex's matcher engines are not confirmed to match arbitrary MCP tool-name
# regexes the same way, so this is wired only into CLAUDE_SETTINGS_HOOKS
# below — a stated, not guessed-around, asymmetry (see hooks/README.md).
MCP_INFRA_MUTATION_MATCHER = (
    r"mcp__.*__(d1_database_(create|delete)|kv_namespace_(create|delete|update)"
    r"|r2_bucket_(create|delete)|hyperdrive_config_(create|edit|delete)"
    r"|apply_migration|execute_sql|deploy_edge_function|create_branch"
    r"|delete_branch|merge_branch|reset_branch|rebase_branch|create_project"
    r"|pause_project|restore_project|deploy_to_vercel)"
)

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
        {"matcher": "Bash", "script": "guard_infra_mutation.py"},
        {"matcher": MCP_INFRA_MUTATION_MATCHER, "script": "guard_infra_mutation.py"},
        {"matcher": "Write|Edit|MultiEdit|NotebookEdit", "script": "guard_remote_automation.py"},
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
        {"matcher": "Shell", "script": "guard_infra_mutation.py"},
        {"matcher": "Shell", "script": "guard_remote_automation.py"},
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
        {"matcher": "Bash", "script": "guard_infra_mutation.py"},
        {"matcher": "apply_patch|Edit|Write|Bash", "script": "guard_remote_automation.py"},
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


def git_tracked_top_level_names(root: Path, source: Path) -> set[str]:
    """Names of top-level entries under `source` that are actually tracked
    in this harness's own git history (or currently staged) -- the real
    source of truth for "does the harness own this."

    A plain directory listing can't tell tracked harness content apart
    from something a third-party installer already wrote into the same
    path: confirmed to happen for real (the `caveman` skill's installer
    wrote its own directories straight into claude/skills/ through the
    old whole-directory symlink, and once there, `caveman` and
    `branch-worktree` look identical to a directory listing -- only git
    knows which one this repo actually committed).
    """
    try:
        relative = source.relative_to(root)
    except ValueError:
        return set()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", str(relative)],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    prefix = str(relative) + "/"
    names: set[str] = set()
    for line in result.stdout.splitlines():
        if line.startswith(prefix):
            names.add(line[len(prefix):].split("/", 1)[0])
    return names


def reconcile_directory_mirror(real_parent: Path, harness_source: Path, dry_run: bool) -> list[str]:
    """Ensure real_parent is a REAL directory (never a symlink itself),
    containing one symlink per entry in harness_source, without disturbing
    any other (non-harness) entries already inside real_parent.

    Migration case: if real_parent is currently a whole-directory symlink
    (the old, buggy design), any entries inside its resolved target that
    AREN'T one of harness_source's own entries are moved out into the new
    real directory before the symlink is replaced — this is exactly what
    protects a third-party tool's files (e.g. a skill installed alongside
    this harness's own) from being silently discarded during migration.
    """
    report: list[str] = []
    # Source of truth is git tracking, NOT a directory listing -- once a
    # third-party entry has already landed inside harness_source (the
    # caveman incident), a directory listing can no longer tell it apart
    # from the harness's own real content. Only git knows which is which.
    harness_names = git_tracked_top_level_names(ROOT, harness_source)

    if real_parent.is_symlink():
        old_target = real_parent.resolve()
        if dry_run:
            report.append(
                f"WOULD MIGRATE {real_parent}: currently a whole-directory "
                f"symlink -> {old_target} -- would convert to a real "
                f"directory with one symlink per harness entry, moving any "
                f"non-harness entries found inside {old_target} into it."
            )
            return report
        foreign_entries = []
        if old_target.exists():
            for entry in old_target.iterdir():
                if entry.name not in harness_names:
                    foreign_entries.append(entry)
        real_parent.unlink()
        real_parent.mkdir(parents=True, exist_ok=True)
        for entry in foreign_entries:
            entry.rename(real_parent / entry.name)
        if foreign_entries:
            names = ", ".join(e.name for e in foreign_entries)
            report.append(
                f"MIGRATED {real_parent}: was a whole-directory symlink -> "
                f"{old_target}; converted to a real directory, preserved "
                f"{len(foreign_entries)} non-harness entr"
                f"{'y' if len(foreign_entries) == 1 else 'ies'} moved out of "
                f"the harness repo and into it: {names}"
            )
        else:
            report.append(
                f"MIGRATED {real_parent}: was a whole-directory symlink -> "
                f"{old_target}; converted to a real directory (no "
                f"non-harness entries found to preserve)"
            )
    elif not real_parent.exists():
        if dry_run:
            report.append(f"WOULD CREATE {real_parent} (real directory)")
            return report
        real_parent.mkdir(parents=True, exist_ok=True)
        report.append(f"CREATED {real_parent} (real directory)")
    elif not real_parent.is_dir():
        report.append(
            f"SKIPPED {real_parent}: exists as a real file, not a "
            f"directory — not touching it automatically. Resolve by hand."
        )
        return report
    else:
        report.append(f"OK      {real_parent} (already a real directory)")

    for name in sorted(harness_names):
        entry = harness_source / name
        if entry.exists():
            report.append("  " + reconcile_symlink(real_parent / name, entry, dry_run))

    return report


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
    print(f"{'(dry run) ' if args.dry_run else ''}Reconciling directory mirrors...\n")

    # Order matters: directory mirrors first (so ~/.claude/skills is a real
    # directory before anything tries to alias it), then aliases, then
    # plain file symlinks.
    for real_parent, harness_source in DIRECTORY_MIRRORS:
        for line in reconcile_directory_mirror(real_parent, harness_source, args.dry_run):
            print("  " + line)

    print(f"\n{'(dry run) ' if args.dry_run else ''}Reconciling alias symlinks...\n")
    for target, source in ALIAS_SYMLINKS:
        print("  " + reconcile_symlink(target, source, args.dry_run))

    print(f"\n{'(dry run) ' if args.dry_run else ''}Reconciling file symlinks...\n")
    for target, source in FILE_SYMLINKS:
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
