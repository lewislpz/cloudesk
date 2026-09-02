---
name: backend-dev-guidelines
description: Use when implementing or reviewing backend services, business logic, APIs, validation, persistence boundaries, or backend tests.
---

# Backend Development

## Boundaries

Use for backend implementation decisions. Do not impose layered architecture, JPA,
Spring Boot, or a service layer when the repository uses another established model.

## Operating Loop

1. Detect language, framework, architecture, dependency injection, persistence,
   validation, error handling, and test conventions.
2. Trace the request or event path through existing boundaries before editing.
3. Keep business rules in the repository's domain or application boundary and keep
   transport and persistence details isolated.
4. Preserve contracts, transaction semantics, authorization, and observability.
5. Verify behavior at the narrowest meaningful level, then run integration checks for
   changed boundaries.

## Decision Rules

- Validate untrusted input and enforce core invariants server-side.
- Keep transport models, domain models, and persistence models separate when their
  lifecycles or exposure differ.
- Use transactions around atomic business operations, not by blanket convention.
- Avoid unbounded reads and accidental sensitive-data exposure.
- Match existing error and observability patterns.

## Optional Reference

Load [spring-boot-layered-jpa.md](references/spring-boot-layered-jpa.md) only when the
repository actually uses Spring Boot with layered JPA conventions.
