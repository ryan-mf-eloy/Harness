---
type: reference
tags: [playbook, ddd, architecture]
status: active
created: 2026-07-06
---

# Domain-Driven Design and Layer Discipline

## When to use this

When modeling a domain that's non-trivial enough to raise the question —
touches a real business invariant, is shared/reused across modules, or is
already showing signs of "everything talks to everything." Also read this
before deciding "which layer does X belong in" for anything that isn't
obviously presentation, or before drawing a bounded-context boundary. Not
needed for a script, a single CRUD endpoint, or a prototype — see the
calibration rule in `principles/PRINCIPLES.md`'s "DDD-informed modeling"
bullet before reaching for anything below.

## Approach

### Layers (canonical framing; confirm actual names per project)

- **Presentation/API** — HTTP/CLI/GraphQL handling, request/response
  shaping, auth-token parsing, format validation (is this JSON
  well-formed, are required fields present). No business rules here.
- **Application** — orchestrates a use case: loads aggregates via a
  repository, calls domain methods, publishes domain events, commits the
  transaction. Thin — it coordinates, it doesn't decide.
- **Domain** — entities, value objects, aggregates, domain services,
  domain events. All business rules and invariants live here. Has zero
  dependency on frameworks, ORMs, or transport concerns.
- **Infrastructure** — repository implementations, ORM mappings, external
  API clients, email/queue senders. Implements interfaces the domain
  layer defines; the domain never imports from here.

### DDD tactical building blocks (fuller definitions + examples)

- **Entity** — has identity that persists through state changes (a
  `Customer` is still the same customer after changing their address).
  Equality is by identity, not by attribute values.
- **Value Object** — has no identity; equality is by value. Immutable.
  Example: `Money(amount, currency)`, `DateRange(start, end)`. Replacing
  one Value Object with another that has the same values is a no-op.
- **Aggregate / Aggregate Root** — a cluster of entities and value
  objects that must be changed together to preserve an invariant, with
  one designated root as the only entry point for external code. Example:
  an `Order` aggregate root containing `OrderLine` entities — you can't
  add a line item that violates a "max 20 line items" rule except through
  the `Order` root, which enforces it.
- **Repository** — an interface, defined in the domain layer, for
  loading/saving a whole aggregate by its root; the implementation (SQL,
  ORM, in-memory) lives in infrastructure. Domain and application code
  depend only on the interface.
- **Domain Service** — a stateless operation that's a real domain concept
  but doesn't naturally belong to one entity (e.g. `TransferMoney(from,
  to, amount)` touching two `Account` aggregates — it can't live on
  either account alone).
- **Domain Event** — an immutable record of something that already
  happened, named in the past tense (`OrderPlaced`, `PaymentFailed`),
  used to decouple side effects from the triggering operation. The
  domain entity raises the event; an application-layer subscriber reacts
  to it (e.g. sends the confirmation email) — the entity itself never
  calls the email service directly.

### Strategic concepts

- **Bounded Context** — a boundary within which a model and its
  vocabulary are internally consistent, and outside of which the same
  term can mean something different. Example: "Customer" in a Billing
  context (has a payment method, a balance) is a different model from
  "Customer" in a Support context (has a ticket history, a satisfaction
  score) — modeling them as one shared class forces artificial coupling
  and unrelated-field bloat. Ties directly to `principles/PRINCIPLES.md`'s
  existing "three-or-more-modules" signal and "Dependency direction"
  rule — a bounded context is a module boundary drawn along domain-model
  lines specifically, not just code-organization lines.
- **Ubiquitous Language** — the vocabulary used in code (class names,
  method names) should match the vocabulary the domain expert/business
  actually uses, within a given bounded context. If the business says
  "waitlisted," the code says `Waitlisted`, not `PendingStatusType3`.

### Context-mapping patterns (for when bounded contexts interact)

- **Shared Kernel** — two contexts explicitly share a small, jointly-owned
  piece of the model. High coordination cost; use sparingly.
- **Customer–Supplier** — one context's team has effective veto power
  over changes the other depends on (the "supplier" serves the
  "customer's" needs deliberately).
- **Conformist** — the downstream context just accepts the upstream
  model as-is with no translation, because it has no influence over it
  and translation isn't worth the cost.
- **Anti-Corruption Layer (ACL)** — a translation layer at the boundary
  that converts an external/legacy/upstream model into this context's
  own model, so the messy external shape never leaks inward. Use when
  integrating with a third-party API or a legacy system you don't
  control and don't want polluting your domain model.

### Worked "which layer does X go in" examples

1. **"A discount percentage must be between 0 and 100."** Domain layer —
   this is a business rule/invariant, not a format concern. Belongs on
   the entity or value object that owns "discount," not in the route
   handler that receives the request.
2. **"The incoming JSON request body must have `email` and `amount`
   fields."** Presentation/API layer — this is a shape/format concern
   about the transport payload, not a business rule about the domain.
3. **"After an order is placed, send a confirmation email."** Not
   inline in the `Order` entity. Model it as an `OrderPlaced` domain
   event; an application-layer event subscriber calls the email service.
   Keeps the domain entity free of infrastructure dependencies (an email
   sender is an infrastructure concern) while keeping the business fact
   ("an order was placed") in the domain.

## Why (if non-obvious)

Full DDD tactical patterns exist to manage genuine complexity — multiple
entities that must stay consistent together, a concept that means
different things in different parts of the business, side effects that
need decoupling from their trigger. Applying the full pattern set to a
domain that doesn't have that complexity (a single CRUD resource, a
script) adds indirection with no corresponding payoff — that's the
over-engineering failure mode `principles/PRINCIPLES.md` already guards
against via "No speculative abstraction," "Reuse over new," and "Surgical
diffs." Skipping structure a genuinely complex domain needs, on the other
hand, produces the anemic-domain-model failure mode (all logic pushed
into generic `*Service` classes, entities as dumb data-bags) — which
isn't "keeping it simple," it's just moving the complexity somewhere
it's harder to find and easier to get wrong. The calibration rule exists
so the same risk signal already computed for testing/research depth also
decides this, instead of it being a separate judgment call invented fresh
each time.

Choosing a project's actual layer names or bounded-context boundaries is
itself an architectural decision, not a detail — record it with the same
ADR mechanism `principles/PRINCIPLES.md`'s "Record decisions" bullet
already requires for a module-boundary or data-model change, using
`Vault/00-System/Templates/Decision.md`. This playbook is the general
reference for what the concepts mean; a project's own ADR is where the
specific choice for that project gets written down and dated.
