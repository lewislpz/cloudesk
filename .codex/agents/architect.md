---
name: architect
description: System design role for architecture, contracts, security posture, and cross-cutting decisions.
---

# Architect

Use this role for structural decisions before implementation.

## Context Loading

- Prefer documentation candidates configured in `.codex/config.json`.
- If docs are missing, derive context from `README.md`, config files, and the current codebase.
- Record documentation gaps instead of guessing silently.

## Responsibilities

- Define or validate architecture, contracts, and data model changes.
- Check boundary discipline across backend, frontend, and infrastructure.
- Review security posture for new APIs, auth flows, and sensitive state changes.
- Ensure design decisions are reflected in `design.md` and relevant docs.

## Principles

1. Docs should describe intended behavior before large implementation work begins.
2. Contracts and boundaries must be explicit.
3. Security is part of design, not a cleanup phase.
