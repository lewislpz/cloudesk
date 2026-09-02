# ADR-019: Begin With Kubernetes Rolling Deployments

## Status

Proposed

## Context

V1 needs safe immutable updates without the complexity of dual production stacks or progressive routing.

## Decision

Use rolling updates with readiness gates, surge/unavailable budgets, graceful termination, backward-compatible contracts, and digest-pinned rollback.

## Alternatives Considered

Blue/green increases capacity cost; canary and Argo Rollouts add value only after reliable SLO signals and sufficient traffic exist.

## Consequences

Old and new versions overlap, so APIs, messages, and schema changes must be compatible. Canary becomes future evolution when metrics can support automated analysis.
