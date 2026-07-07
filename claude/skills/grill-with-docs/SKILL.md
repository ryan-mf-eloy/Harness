---
name: Grill With Docs
description: Interrogates the project's documentation/knowledge base to answer a specific question, explicitly surfacing contradictions, staleness, or gaps rather than smoothing over them. Use when asked a question that should be answerable from existing docs, or to sanity-check whether documentation actually supports a claim/decision.
when_to_use: A question is asked that existing documentation should answer, or the user wants to verify docs are internally consistent / not stale before relying on them.
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, WebFetch
user-invocable: true
---

1. **Locate candidate sources** — repo-local `docs/`, README, ADRs, the
   Harness `Vault/` and `RAG/` (query `Scripts/harness/query.py` rather than
   grepping whole folders), and any connected external knowledge-base MCP.
   > Project-specific: wire the actual knowledge-base MCP once chosen — file-
   > based docs work today with just Read/Grep/Glob.
2. **Search adversarially** — don't stop at the first matching doc. Check
   for a second source that might contradict it, and check doc timestamps
   against recent code changes to catch staleness.
3. **Answer format** — lead with the direct answer, cite the exact doc and
   section, then explicitly call out:
   - any contradiction found between sources,
   - any staleness signal (doc references behavior that no longer matches
     reality),
   - any gap (the question isn't covered anywhere).
4. **Never silently pick one source over a conflicting one** — flagging the
   conflict to the user is the entire point of this skill, distinguishing
   it from a plain lookup.

Non-goal: this does not write documentation (that's `doc-create`) — it only
interrogates what already exists.
