# ADR-018: Standardize Telemetry On OpenTelemetry

## Status

Proposed

## Context

Requests cross browser, API, PostgreSQL, outbox, SQS, workers, and AWS services; provider-specific instrumentation would fragment correlation.

## Decision

Instrument traces, metrics, and context propagation with OpenTelemetry and route telemetry through collectors to selected managed or self-hosted backends.

## Alternatives Considered

Vendor-native SDKs may accelerate setup but increase lock-in; logs alone cannot explain asynchronous latency or failure propagation.

## Consequences

Attribute cardinality and sensitive data require governance. Collector capacity, sampling, retention, cost, and degraded-export behavior must be operated.
