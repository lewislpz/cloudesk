---
name: software-architecture
description: Use when designing architecture, analyzing software structure, or making cross-cutting implementation decisions.
---

# Software Architecture Development Skill

This skill provides guidance for quality focused software development and architecture. It is based on Clean Architecture and Domain Driven Design principles.

## Decision Rules

### General Principles

- Follow the repository's established language and framework conventions.
- Prefer early returns when they reduce nesting and improve readability.
- Remove meaningful duplication without introducing premature abstractions.
- Split code when a unit has multiple responsibilities or is difficult to test and review;
  use size as a signal, not a hard limit.

### Best Practices

#### Library-First Approach

- Search for existing repository and ecosystem solutions before writing custom code.
  - Check the package ecosystem appropriate to the repository
  - Evaluate existing solutions and services
  - Consider third-party APIs for common functionality
- Prefer a maintained dependency when it materially reduces risk and its operational,
  security, and maintenance costs fit the repository.
- **When custom code IS justified:**
  - Specific business logic unique to the domain
  - Performance-critical paths with special requirements
  - When external dependencies would be overkill
  - Security-sensitive code requiring full control
  - When existing solutions don't meet requirements after thorough evaluation

#### Architecture and Design

- **Clean Architecture & DDD Principles:**
  - Follow domain-driven design and ubiquitous language
  - Separate domain entities from infrastructure concerns
  - Keep business logic independent of frameworks
  - Define use cases clearly and keep them isolated
- **Naming Conventions:**
  - **AVOID** generic names: `utils`, `helpers`, `common`, `shared`
  - **USE** domain-specific names: `OrderCalculator`, `UserAuthenticator`, `InvoiceGenerator`
  - Follow bounded context naming patterns
  - Each module should have a single, clear purpose
- **Separation of Concerns:**
  - Do NOT mix business logic with UI components
  - Keep database queries out of controllers
  - Maintain clear boundaries between contexts
  - Ensure proper separation of responsibilities

#### Anti-Patterns to Avoid

- **Unexamined build-versus-buy decisions:**
  - Do not build security-sensitive or commodity infrastructure without documenting
    why repository-native or maintained external options are unsuitable.
- **Poor Architectural Choices:**
  - Mixing business logic with UI components
  - Database queries directly in controllers
  - Lack of clear separation of concerns
- **Generic Naming Anti-Patterns:**
  - `utils.js` with 50 unrelated functions
  - `helpers/misc.js` as a dumping ground
  - `common/shared.js` with unclear purpose
- Remember: Every line of custom code is a liability that needs maintenance, testing, and documentation

#### Code Quality

- Proper error handling with typed catch blocks
- Break down complex logic into smaller, reusable functions
- Avoid deep nesting when extraction or early returns make intent clearer.
- Keep functions and files focused; use reviewability, cohesion, and testability as
  the split criteria.
