---
name: software-architecture
description: Use when designing architecture, analyzing system structure, or making cross-cutting boundary and dependency decisions.
---

# Software Architecture

## Boundaries

Use for cross-cutting decisions and system boundaries. Do not impose Clean
Architecture, DDD, microservices, or a dependency before inspecting the system.

## Operating Loop

1. Identify the system goals, constraints, current boundaries, dependency direction,
   runtime topology, and change pressure.
2. Locate the decision that is hard to reverse and separate it from local
   implementation choices.
3. Compare the smallest viable options using explicit tradeoffs: complexity,
   operability, security, performance, migration cost, and reversibility.
4. Preserve existing architecture unless evidence justifies migration.
5. Define contracts, ownership, failure behavior, rollout, and verification.

## Decision Rules

- Prefer cohesive boundaries aligned with change and ownership.
- Keep policy independent from volatile infrastructure where that reduces coupling.
- Add abstractions only when they remove demonstrated complexity.
- Evaluate build-versus-buy using operational and security costs, not implementation
  effort alone.
- Record unresolved risks and migration steps.

## Optional Reference

Load [legacy-guide.md](references/legacy-guide.md) only when Clean Architecture or DDD
is relevant to the detected repository.
