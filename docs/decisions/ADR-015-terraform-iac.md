# ADR-015: Manage AWS Infrastructure With Terraform

## Status

Proposed

## Context

AWS topology, IAM, data services, and environment promotion must be reviewable, reproducible, and recoverable.

## Decision

Use version-pinned Terraform modules and environment roots with encrypted remote state, locking, plans in CI, and controlled applies through GitHub OIDC.

## Alternatives Considered

Manual provisioning drifts; CloudFormation/CDK increase AWS coupling or language runtime without a stated benefit.

## Consequences

State bootstrap and recovery require a small separately controlled process. Module interfaces, provider upgrades, drift detection, and secret handling need ownership.
