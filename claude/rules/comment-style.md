---
description: Conventions for in-code comments and how to explain changes in conversation
---

# Comments & Explanation

- Comment only the **why**, never the **what** — code should read like the
  what; comment when a reader would otherwise ask "why on earth did they do
  it this way."
- No commented-out code left behind. No comment that just restates the
  function name in prose above it.
- TODO comments must name an owner or a tracking ticket, never a bare
  `// TODO`.
- When explaining a change in conversation: lead with the **why**, then
  **what changed**, then anything the user needs to do next.
- No emojis unless explicitly requested.
- State intent plainly before a tool call rather than narrating it
  ("Let me read the file." not "Let me read the file:" followed by a colon).
