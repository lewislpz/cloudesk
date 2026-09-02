# ADR-010: Enforce Tenant Isolation In Every Layer

## Status

Proposed

## Context

An authenticated user may belong to multiple organizations, and accidental ID-only access could expose another tenant's data.

## Decision

Use organization-prefixed API resources, authorize active membership and permission, require organization-scoped repository methods/SQL, encode tenant-aware constraints and keys, and apply selective PostgreSQL RLS as defense in depth.

## Alternatives Considered

Application-only ad hoc checks are fragile; database-per-tenant is operationally excessive for the target; RLS-only obscures application policy.

## Consequences

All caches, jobs, events, object keys, idempotency records, logs, and tests must carry tenant context. RLS session context and pool hygiene require integration testing.
