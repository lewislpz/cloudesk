# ADR-001: Use Go For The Backend

## Status

Proposed

## Context

ClouDesk needs explicit HTTP, transactional, worker, concurrency, and shutdown behavior with a small operational footprint.

## Decision

Use Go for the modular backend API and worker binaries, favoring the standard library and small focused libraries.

## Alternatives Considered

TypeScript end-to-end would reduce languages but weakens the portfolio's explicit Go goal; Java offers mature frameworks but adds ceremony disproportionate to V1.

## Consequences

Teams gain simple deployment and strong concurrency primitives but must maintain cross-language contracts and enforce package boundaries deliberately.
