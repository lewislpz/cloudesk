# ADR-017: Use Argo CD As The GitOps Controller

## Status

Proposed

## Context

The selected GitOps model needs Kubernetes-native reconciliation, health visibility, environment boundaries, and mature Helm support.

## Decision

Use Argo CD in the production platform phase with one application boundary per environment/workload grouping and least-privilege project controls.

## Alternatives Considered

Flux is capable and simpler in some models; Argo CD is selected for operational UI, portfolio visibility, and ecosystem fit. CI-driven deployment is rejected by ADR-016.

## Consequences

Argo CD itself needs backup/rebuild documentation, SSO/RBAC, upgrade ownership, notification policy, and protection from applying incompatible migrations.
