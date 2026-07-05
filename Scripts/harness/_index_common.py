"""Shared schema and helpers for the Harness SQLite FTS5 index.

Imported by index_rebuild.py, index_upsert.py, and query.py — kept in one
place so the three scripts can never drift into inconsistent schemas.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # Harness/
DB_PATH = ROOT / "Index" / "harness.sqlite"
VAULT_DIR = ROOT / "Vault"
RAG_DIR = ROOT / "RAG"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY,
    path        TEXT NOT NULL UNIQUE,
    source      TEXT NOT NULL,          -- 'vault' | 'rag' | 'project-docs'
    project     TEXT,
    title       TEXT NOT NULL,
    tags        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL,
    content     TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title, tags, content,
    content = 'documents',
    content_rowid = 'id',
    tokenize = 'porter unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, tags, content)
    VALUES (new.id, new.title, new.tags, new.content);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, tags, content)
    VALUES ('delete', old.id, old.title, old.tags, old.content);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, tags, content)
    VALUES ('delete', old.id, old.title, old.tags, old.content);
    INSERT INTO documents_fts(rowid, title, tags, content)
    VALUES (new.id, new.title, new.tags, new.content);
END;

CREATE INDEX IF NOT EXISTS idx_documents_source  ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project);
"""

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a naive YAML frontmatter block from the body. Not a full YAML
    parser on purpose — the taxonomy only uses flat scalar values, and
    pulling in a dependency for this would be over-engineering it."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw, body = match.group(1), text[match.end():]
    frontmatter: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip().strip('"').strip("[]")
    return frontmatter, body


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def connect(create_schema: bool = True) -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    if create_schema:
        conn.executescript(SCHEMA_SQL)
    return conn


def iter_source_files(base: Path, source: str):
    if not base.exists():
        return
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        yield rel, source, path
