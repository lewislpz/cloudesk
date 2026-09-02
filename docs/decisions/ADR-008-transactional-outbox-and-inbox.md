# ADR-008: Use Transactional Outbox And Consumer Inbox

## Status

Proposed

## Context

Publishing after a database commit can lose events, while broker retries can repeat delivery.

## Decision

Write the business change, required audit fact, one immutable `outbox_events` envelope, and one `outbox_deliveries` row per registered destination in the same PostgreSQL transaction. A publisher claims/updates only delivery rows and read-joins the envelope; `UNIQUE (event_id, destination)` makes fan-out progress independent. Each consumer records its event ID atomically with its durable effect where possible.

## Alternatives Considered

Best-effort publish loses events; distributed transactions are unavailable and disproportionate; full event sourcing is not required.

## Consequences

Delivery is at least once, not exactly once. Routing changes must be versioned so the source transaction creates the intended delivery rows. Cleanup, lag monitoring, 30-day initial delivery/inbox retention, controlled replay, and idempotent external effects are required.
