---
name: clean-code
description: Use when implementing or refactoring code and you need concise, pragmatic quality rules that fit Codex's workflow.
version: 3.0
priority: CRITICAL
---

# Clean Code

## Core Principles

- Prefer the simplest design that solves the current problem.
- Keep functions focused and names descriptive.
- Remove duplication when it reduces cognitive load.
- Avoid speculative abstractions.
- Leave the touched area clearer than you found it.

## Naming

- Variables should reveal intent: `userCount`, not `n`
- Functions should describe action: `loadUser`, `buildPayload`
- Booleans should read like predicates: `isReady`, `hasAccess`, `canRetry`
- Constants should explain meaning, not hide magic numbers

## Structure

- Favor guard clauses over deep nesting.
- Keep related logic close to where it is used.
- Do not create helper files for one trivial use.
- Prefer composition over oversized functions or classes.

## Before Editing

Check these first:

1. Who imports this file?
2. What contracts or types depend on it?
3. What tests or commands verify the change?
4. Does the change belong in this file at all?

## Verification

- Use the smallest project-native command that gives confidence.
- Prefer existing scripts such as `npm test`, `pytest`, `go test`, `cargo test`, `mvn test`, or targeted equivalents.
- Do not invent external validation tooling that is not present in the repo.
- Classify failures before retrying and do not repeat an unchanged failed action.

## Output Style

- Write code before explanation when the task is implementation.
- Avoid tutorial narration and obvious comments.
- Summaries should focus on what changed, why, and how it was verified.
