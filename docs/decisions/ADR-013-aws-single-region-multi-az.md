# ADR-013: Target One AWS Region Across Multiple Availability Zones

## Status

Proposed

## Context

Production needs common-zone failure tolerance without multi-region data and deployment complexity.

## Decision

Use one selected AWS region with workloads spread across three AZs and RDS Multi-AZ. Backups and recovery artifacts support regional disaster recovery without active-active traffic.

## Alternatives Considered

Single-AZ is cheaper but inadequate for production; active-active multi-region multiplies consistency, cost, and operations before a business requirement exists.

## Consequences

AZ loss should degrade capacity, not correctness. Multi-region is reconsidered only for contractual availability, data residency, latency, or proven regional-risk requirements.
