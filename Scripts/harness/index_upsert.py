#!/usr/bin/env python3
"""Incremental single-file upsert, invoked as a PostToolUse hook.

Wired in this repo's own .claude/settings.json against PostToolUse with matcher
"Write|Edit|MultiEdit". Reads the hook JSON payload from stdin (the only
input format the hook mechanism guarantees) rather than relying on
shell-templated placeholders — deliberately more robust than assuming a
specific ${tool_input.file_path}-style substitution exists.

Silently no-ops (exit 0) for any file outside Vault/ or RAG/, or any
non-markdown file, so it's safe to wire against a broad matcher.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _index_common import (
    PRINCIPLES_DIR,
    RAG_DIR,
    ROOT,
    VAULT_DIR,
    connect,
    extract_title,
    parse_frontmatter,
)


def resolve_source(abs_path: Path) -> str | None:
    for directory, source in ((VAULT_DIR, "vault"), (RAG_DIR, "rag"), (PRINCIPLES_DIR, "principles")):
        try:
            abs_path.relative_to(directory)
            return source
        except ValueError:
            continue
    return None


def upsert_one(abs_path: Path, source: str) -> None:
    if not abs_path.exists():
        # file was deleted or moved — remove any stale row instead of upserting
        conn = connect()
        rel = abs_path.relative_to(ROOT).as_posix()
        conn.execute("DELETE FROM documents WHERE path = ?", (rel,))
        conn.commit()
        conn.close()
        return

    text = abs_path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = parse_frontmatter(text)
    title = extract_title(body, abs_path.stem)
    mtime = datetime.fromtimestamp(abs_path.stat().st_mtime, tz=timezone.utc).isoformat()
    rel = abs_path.relative_to(ROOT).as_posix()

    conn = connect()
    conn.execute(
        """INSERT INTO documents(path, source, project, title, tags, updated_at, content)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(path) DO UPDATE SET
             source=excluded.source, project=excluded.project, title=excluded.title,
             tags=excluded.tags, updated_at=excluded.updated_at, content=excluded.content""",
        (rel, source, frontmatter.get("project") or None, title, frontmatter.get("tags", ""), mtime, body),
    )
    conn.commit()
    conn.close()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path or not file_path.endswith(".md"):
        return 0

    abs_path = Path(file_path)
    source = resolve_source(abs_path)
    if source is None:
        return 0  # outside Vault/ and RAG/ — nothing to do

    upsert_one(abs_path, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
