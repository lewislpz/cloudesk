# ADR-020: Use Expand-And-Contract Database Migrations

## Status

Proposed

## Context

Rolling deployments run mixed versions, and immediate destructive schema changes can break either version or cause unrecoverable data loss.

## Decision

Separate schema expansion, compatible code, bounded backfill, read/write switch, and later contraction into independently verified releases.

## Alternatives Considered

Maintenance-window migrations reduce engineering work but undermine availability; automatic ORM schema mutation hides review and sequencing.

## Consequences

Temporary dual schema paths and cleanup work are expected. Backfills need throttling, observability, resumability, and roll-forward plans; destructive contraction requires explicit approval.
