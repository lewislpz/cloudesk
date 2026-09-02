# ADR-005: Use sqlc And pgx For PostgreSQL Access

## Status

Proposed

## Context

Tenant-aware SQL, PostgreSQL features, query review, and transaction control should remain visible.

## Decision

Use `pgx` for connectivity/transactions and `sqlc` to generate typed Go access from reviewed SQL.

## Alternatives Considered

Heavy ORMs reduce routine mapping but can hide tenant predicates and query behavior; hand-written scanning creates avoidable repetitive risk.

## Consequences

SQL stays explicit and testable. Schema/query generation becomes a CI contract, and domain models should not be coupled blindly to generated row structs.
