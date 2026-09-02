# ADR-004: Start With A Modular Monolith And Independent Workers

## Status

Proposed

## Context

Many business capabilities share transactions and a small team initially owns the whole product. Premature services add network and consistency costs.

## Decision

Keep one modular Go codebase with enforced domain APIs and separate API/outbox/specialized worker processes.

## Alternatives Considered

Microservices and serverless-per-function designs add deployment and coordination overhead before independent ownership or scaling exists.

## Consequences

Local development and refactoring stay simple. A module may be extracted only for sustained independent scaling, availability, workload isolation, ownership, or release needs, backed by metrics and a new ADR.
