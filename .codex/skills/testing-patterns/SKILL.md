---
name: testing-patterns
description: Use when selecting test levels, adding coverage, designing fixtures or mocks, reviewing tests, or applying TDD.
---

# Testing Patterns

## Boundaries

Use for test strategy and implementation. Do not assume Spring, React, Mockito,
Vitest, MSW, or strict TDD when the repository uses other conventions or the task is
repairing an existing failure.

## Operating Loop

1. Identify the behavior, risk, regression mode, current test framework, and available
   fixtures.
2. Select the lowest test level that proves the behavior without hiding important
   integration risk.
3. Reproduce the failure or create a meaningful failing test before behavior changes
   when practical.
4. Implement the smallest change, refactor after green, and keep tests deterministic.
5. Run focused checks first, then broader checks proportional to blast radius.

## Decision Rules

- Test observable behavior and contracts, not private implementation details.
- Mock external or slow boundaries, not the behavior under test.
- Prefer realistic integration coverage for persistence, serialization, security, and
  framework wiring.
- Keep fixtures readable and relevant to the scenario.
- Document untested risks when reliable automation is not practical.

## Optional Reference

Load [spring-react-examples.md](references/spring-react-examples.md) only when its
Spring Boot or React examples match the detected stack.
