# ADR-007: Use Amazon SQS For Initial Messaging

## Status

Proposed

## Context

Production workers need durable at-least-once delivery, managed operations, DLQs, and AWS-native IAM without complex broker administration.

## Decision

Use Amazon SQS standard queues per workload class, with local adapters for development. Ordering is encoded per aggregate where needed rather than assumed globally.

## Alternatives Considered

NATS offers strong developer ergonomics but adds operation/state choices; RabbitMQ offers routing but needs broker operations; Kafka is unjustified.

## Consequences

Consumers must tolerate duplicates and loose ordering. Queue topology, visibility timeout, DLQ, long polling, IAM, and cost need deliberate tuning.
