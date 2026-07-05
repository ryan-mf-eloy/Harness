---
description: System-design-level architectural conventions — ADRs, module boundaries, dependency direction
---

# Architecture Culture

- **ADRs.** Any decision that changes a module boundary, introduces a new
  external dependency, changes a data model, or picks between two or more
  viable architectural approaches gets a short Architecture Decision Record
  (Context / Decision / Consequences / Alternatives Considered — see the
  Decision template in `Vault/00-System/Templates/`).
- **Dependency direction.** Lower layers must not import from higher layers.
  What counts as a "layer" is project-specific (domain → application →
  infrastructure → presentation is a common default) — confirm the target
  project's actual layering rather than assuming this one.
- **Composition over inheritance** at the architecture level — distinct
  from Object Calisthenics, which is the same principle applied at the
  class level.
- **Three-or-more-modules signal.** If satisfying one requirement requires
  touching three or more modules, treat that as a signal to pause and
  consider whether a boundary is drawn wrong, rather than pushing through.
  Surface this via the `pre-change-impact-check` skill's risk
  classification rather than silently proceeding.
- **No speculative abstraction.** Don't generalize ahead of a second real
  use case — this is YAGNI applied at the architecture level, complementing
  the code-level "reuse over new" principle in `engineering-principles.md`.
