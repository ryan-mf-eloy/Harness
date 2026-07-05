#!/usr/bin/env python3
"""Full rebuild of Index/harness.sqlite from Vault/ and RAG/.

Usage:
  index_rebuild.py            # drop and recreate the index from scratch
  index_rebuild.py --check    # verify FTS5 support + schema integrity only, no rebuild

Run this after bulk edits made directly in the Obsidian app (which don't go
through Claude Code's PostToolUse hook, see index_upsert.py), or any time
the index looks stale.
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone

from _index_common import (
    DB_PATH,
    RAG_DIR,
    ROOT,
    SCHEMA_SQL,
    VAULT_DIR,
    extract_title,
    iter_source_files,
    parse_frontmatter,
)


def check_only() -> int:
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
    except sqlite3.OperationalError as exc:
        print(f"FTS5 NOT supported by this Python's sqlite3 build: {exc}", file=sys.stderr)
        print("Fallback options: pip install apsw, or use Node + better-sqlite3.", file=sys.stderr)
        return 1
    print(f"FTS5 OK (sqlite3 {sqlite3.sqlite_version}).")
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        print(f"Index exists at {DB_PATH.relative_to(ROOT)}, {count} documents.")
    else:
        print(f"No index yet at {DB_PATH.relative_to(ROOT)} — run without --check to build one.")
    return 0


def rebuild() -> int:
    for suffix in ("", "-wal", "-shm", "-journal"):
        candidate = DB_PATH.parent / (DB_PATH.name + suffix)
        if candidate.exists():
            candidate.unlink()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)

    rows = []
    sources = list(iter_source_files(VAULT_DIR, "vault")) + list(iter_source_files(RAG_DIR, "rag"))
    for rel_path, source, abs_path in sources:
        text = abs_path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = parse_frontmatter(text)
        title = extract_title(body, abs_path.stem)
        mtime = datetime.fromtimestamp(abs_path.stat().st_mtime, tz=timezone.utc).isoformat()
        rows.append((
            rel_path.as_posix(),
            source,
            frontmatter.get("project") or None,
            title,
            frontmatter.get("tags", ""),
            mtime,
            body,
        ))

    conn.executemany(
        """INSERT INTO documents(path, source, project, title, tags, updated_at, content)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Indexed {len(rows)} documents -> {DB_PATH.relative_to(ROOT)}")
    return 0


def main() -> int:
    if "--check" in sys.argv[1:]:
        return check_only()
    return rebuild()


if __name__ == "__main__":
    raise SystemExit(main())
