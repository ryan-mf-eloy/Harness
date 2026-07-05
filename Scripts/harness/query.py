#!/usr/bin/env python3
"""Query the Harness FTS5 index and print ranked, snippeted results.

This is the actual token-saving mechanism: it returns short ranked snippets
with file paths, not full file contents — read the 1-2 files that matter
with the Read tool afterward, instead of grepping/reading whole folders.

Usage:
  query.py "<search terms>" [--limit N] [--source vault|rag|project-docs] [--project SLUG]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

from _index_common import DB_PATH, ROOT, connect


def to_fts_match_expr(raw_query: str) -> str:
    """Turn free-typed user input into a safe FTS5 MATCH expression.

    FTS5's bareword query syntax treats -, :, (, ), *, and keywords like
    AND/OR/NOT/NEAR specially. A raw query containing a hyphenated word
    (e.g. "auto-memory") breaks with "no such column: ..." because FTS5
    parses the hyphen as part of its own query grammar, not as a literal
    character. Quoting each token as its own phrase sidesteps all of that:
    every token is matched literally regardless of what punctuation it
    contains.
    """
    tokens = raw_query.split()
    if not tokens:
        return '""'
    return " ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--source", choices=["vault", "rag", "principles", "project-docs"])
    parser.add_argument("--project")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print("No index found. Run index_rebuild.py first.", file=sys.stderr)
        return 1

    conn = connect(create_schema=False)
    sql = """
        SELECT d.path, d.source, d.project, d.title,
               snippet(documents_fts, 2, '[', ']', ' … ', 20) AS snippet,
               bm25(documents_fts, 0.0, 0.0, 1.0) AS score
        FROM documents_fts
        JOIN documents d ON d.id = documents_fts.rowid
        WHERE documents_fts MATCH ?
    """
    params: list[str] = [to_fts_match_expr(args.query)]
    if args.source:
        sql += " AND d.source = ?"
        params.append(args.source)
    if args.project:
        sql += " AND d.project = ?"
        params.append(args.project)
    sql += " ORDER BY score LIMIT ?"
    params.append(str(args.limit))

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"query error (check FTS5 syntax): {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("No results.")
        return 0

    for path, source, project, title, snippet, score in rows:
        proj = f" [{project}]" if project else ""
        print(f"{source}{proj} — {title} ({path})")
        print(f"  {snippet}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
