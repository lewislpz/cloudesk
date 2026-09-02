# ADR-009: Support Persisted Idempotency Keys For Sensitive Commands

## Status

Proposed

## Context

Client retries and concurrent submissions can duplicate timers, invoice issue, exports, and similar costly mutations.

## Decision

Persist `Idempotency-Key` records scoped by organization, principal, and operation with a canonical request fingerprint and replayable response. Create the result and idempotency record atomically.

## Alternatives Considered

In-memory keys fail across replicas; global keys cause tenant collisions; relying on clients not to retry is unsafe.

## Consequences

Identical retries replay the response; key reuse with different input returns `409`. Retention and payload-size limits require policy.
