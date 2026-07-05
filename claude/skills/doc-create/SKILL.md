---
name: Document Create
description: Drafts technical documentation (README, design doc, runbook, ADR) following consistent structure and tone conventions. For Word/PDF/Slides/Excel output specifically, defer to the bundled docx/pdf/pptx/xlsx skills for file mechanics while still using these content conventions.
when_to_use: Asked to write or update a README, design doc, runbook, ADR, or other technical documentation.
argument-hint: "<doc-type> <topic>"
---

Doc-type skeletons (structure only — fill with real content, don't pad):

- **README** — What it is / Setup / Usage / Architecture-at-a-glance /
  Contributing.
- **Design doc** — Problem / Goals & Non-goals / Proposed approach /
  Alternatives considered / Open questions.
- **Runbook** — When to use this / Preconditions / Steps (numbered,
  copy-pasteable commands) / Rollback / Who to page if this doesn't work.
- **ADR** — Context / Decision / Consequences / Alternatives Considered
  (same shape as the Decision template in `Vault/00-System/Templates/`).

Conventions: plain, why-first tone (see `principles/PRINCIPLES.md`), no filler, no
emojis. Date-stamp generated docs so a future reader can judge freshness.
Default to Mermaid-in-markdown for diagrams unless an image is genuinely
needed.
