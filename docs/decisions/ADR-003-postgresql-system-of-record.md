# ADR-003: Use PostgreSQL As The System Of Record

## Status

Proposed

## Context

ClouDesk has relational tenant ownership, financial invariants, concurrency, reporting, and transactionally related events.

## Decision

Use PostgreSQL locally and Amazon RDS for PostgreSQL Multi-AZ in production as the authoritative business store.

## Alternatives Considered

Aurora PostgreSQL is deferred until scale or recovery economics justify it. Document databases weaken relational constraints; Redis is unsuitable for durable truth.

## Consequences

Strong transactions and mature tooling fit the model, while connection capacity, indexes, vacuum, failover, and migration compatibility must be actively managed.
