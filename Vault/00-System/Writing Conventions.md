---
type: reference
tags: [vault, writing, indexing]
status: active
created: 2026-07-06
---

# Writing Conventions — Optimizing for Agent Reading and Indexing

This harness has **two different indexing mechanisms**, and "AI-friendly"
means different concrete things for each. Treating all markdown the same
way would miss real, mechanical differences in how each gets consumed.

## Mechanism 1 — Claude Code's native skill/agent matching

`claude/skills/*/SKILL.md` and `claude/agents/*.md` are not touched by the
SQLite FTS index at all (see `Scripts/harness/_index_common.py` — its scope
is `Vault/`, `RAG/`, `principles/` only). Claude Code itself decides when
to invoke a skill or delegate to a subagent by scanning the `description`
(and `when_to_use`, for skills) frontmatter field — full body content only
loads once invoked. Optimize these fields specifically:

- **Front-load the core use case.** The combined `description` +
  `when_to_use` text is truncated at 1,536 characters in the listing Claude
  actually scans — put the single most important sentence first, not last.
- **Name concrete trigger phrases**, not just abstract capability. "Use
  when asked to create a task, ticket, or issue" matches real requests;
  "handles task lifecycle management" doesn't match anything a user
  actually says.
- **Keep trigger vocabulary distinct across skills.** Two skills both
  keying heavily on the same word (e.g. both leaning on "review") increase
  the odds Claude picks the wrong one. Check neighboring skills before
  finalizing a description.
- **The body is a separate concern.** Once invoked, the whole file loads —
  keep it well-structured for a human/agent actually reading it top to
  bottom (numbered steps, not dense paragraphs), per the general rules
  below. But the `description` field is what determines *whether* it loads
  at all, so it deserves separate, deliberate attention.

## Mechanism 2 — the SQLite FTS5 index (Vault/, RAG/, principles/)

Content here gets chunked into BM25-ranked snippets (`Scripts/harness/query.py`)
— an agent typically sees a short excerpt with the matched terms
highlighted, not the whole file, until it decides to `Read` the full path.
Write for that reality:

- **Every file must open with `# Title` as its first content line.** The
  indexer's `extract_title()` (in `_index_common.py`) reads this exact
  line; without it, the file falls back to its filename, which is a worse
  search result. Make the title specific and descriptive, not generic —
  "RAG — Source of Truth" is findable, "Notes" is not.
- **Front-load the point of each section.** Put the single most important
  sentence at the start of a paragraph/bullet, not buried at the end —
  snippet extraction and a quick human scan both reward this equally.
- **No dangling backward references.** Don't write "as mentioned above,"
  "the following," or "this file" when the reader might only see an
  isolated snippet — name the actual thing: "see
  `principles/PRINCIPLES.md`'s Reasoning & verification discipline
  section," not "see above."
- **One consistent name per concept, everywhere.** Don't call the same
  thing "the FTS index" in one file and "the SQLite database" in another —
  BM25 matching rewards consistent vocabulary; synonyms fragment
  retrievability instead of improving it.
- **Prefer enumerable structure over dense prose.** A bulleted list gives
  the indexer (and a human) discrete, individually-matchable units; a long
  paragraph covering five ideas returns a snippet that's mostly noise
  around whichever one term matched.
- **Cross-reference by exact path, always.** `principles/PRINCIPLES.md`,
  not "the principles file" — a path is unambiguous out of context, prose
  isn't.

## What this does *not* mean

Content a human actually writes for themselves — real meeting notes,
journal-style investigation logs, the free-text body of a Decision or
Learning note — should stay in the user's own natural voice. These
conventions are for the harness's own operational documentation (`AGENTS.md`,
`principles/PRINCIPLES.md`, every `README.md`, skill/agent bodies, and any
`Vault/20-Knowledge/` reference note meant for reuse) — not a mandate to
make personal notes read like a technical spec. Structure the scaffolding;
don't force robotic prose onto the user's own writing.
