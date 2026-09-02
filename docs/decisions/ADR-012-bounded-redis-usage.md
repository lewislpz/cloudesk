# ADR-012: Keep Redis Optional And Non-Authoritative

## Status

Proposed

## Context

Distributed rate limits and hot caches may help, but Redis failure must not lose business state.

## Decision

Use Redis only for short-lived cache, distributed rate-limit counters, and proven coordination needs. PostgreSQL remains authoritative and cache keys include organization scope.

## Alternatives Considered

No Redis simplifies operations and remains the local/V1 default; using Redis for sessions, queues, or durable state creates avoidable recovery risk.

## Consequences

Read caches fail open to bounded database reads; sensitive abuse limits fail closed or use conservative local limits. Timeouts and circuit behavior prevent Redis failure from exhausting the API.
