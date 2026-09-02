---
name: frontend-dev-guidelines
description: Use when implementing or reviewing frontend architecture, UI state, data flows, performance, accessibility, or styling.
---

# Frontend Development

## Boundaries

Use for frontend implementation and architecture. Do not impose React, Suspense,
TanStack Router, Tailwind, MUI, aliases, or folder layouts before detecting them.

## Operating Loop

1. Detect framework, rendering model, routing, state, data fetching, styling, design
   system, tests, and accessibility conventions.
2. Trace the user flow and identify loading, empty, error, success, disabled, and
   destructive states.
3. Preserve established component and feature boundaries unless they cause a concrete
   problem.
4. Separate presentation, interaction state, remote state, and domain logic where
   their responsibilities differ.
5. Verify behavior, accessibility, responsiveness, and relevant performance risks
   with project-native tools.

## Decision Rules

- Prefer repository components, tokens, and feedback patterns.
- Introduce memoization, lazy loading, or virtualization only for a measured or
  credible performance need.
- Keep API contracts typed when the stack supports it and handle failures explicitly.
- Require clear confirmation or recovery for destructive actions proportional to
  impact.

## Optional Reference

Load [react-suspense-feature-guide.md](references/react-suspense-feature-guide.md)
only when the repository already uses its React, Suspense, routing, and styling
conventions.
