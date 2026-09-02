---
name: api-patterns
description: Use when choosing or reviewing API style, contracts, response formats, versioning, pagination, or compatibility.
---

# API Patterns

## Boundaries

Use for API contract decisions. Do not use it as the primary implementation or
security guide.

## Operating Loop

1. Identify consumers, trust boundaries, latency needs, compatibility requirements,
   and existing API conventions.
2. Preserve the established style unless it causes a concrete problem.
3. Define resources or operations, errors, pagination, idempotency, versioning, and
   deprecation behavior before implementation.
4. Review backward compatibility and observable failure behavior.
5. Verify with the repository's contract tests, schema tools, or focused integration
   checks.

## Decisions

- Choose REST, RPC, GraphQL, events, or another style from consumer needs, not habit.
- Keep internal errors private while returning actionable client-safe errors.
- Add versioning only when compatibility cannot be managed within the existing
  contract.
- Treat authentication, authorization, abuse controls, and sensitive data as a
  separate security review.

## Optional Reference

Load [legacy-guide.md](references/legacy-guide.md) only for its checklist; ignore
missing-file maps and stack-specific assumptions in that archived guide.
