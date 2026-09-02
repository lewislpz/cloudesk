# ADR-016: Use GitOps For Kubernetes Desired State

## Status

Proposed

## Context

Cluster deployments need an auditable desired state, environment promotion, drift correction, and separation between artifact build and runtime reconciliation.

## Decision

After CI publishes an immutable image digest, update reviewed Helm values in a GitOps path; a cluster controller reconciles that commit.

## Alternatives Considered

Direct `kubectl` from CI centralizes powerful credentials and weakens reconciliation; a separate GitOps repository is deferred until permissions or scale justify it.

## Consequences

Git history becomes deployment intent and emergency changes must be reconciled back. Promotion PRs, controller access, rollback, and secret references need policy.
