---
name: interface-design
description: Use when designing, reviewing, or refining user interfaces, visual systems, responsive layouts, or interaction states.
---

# Interface Design

Create interfaces that are coherent, usable, accessible, and grounded in the target product.

## Context First

1. Inspect existing screens, components, design tokens, brand guidance, and user flows.
2. Preserve an established visual language unless the task explicitly changes it.
3. If no visual system exists, define a small direction covering typography, color, spacing, shape, and imagery.
4. Never import product identity, visual preferences, or assumptions from another repository.

## Design Requirements

- Establish a clear visual hierarchy and one primary action per view.
- Design for narrow and wide layouts, not only a single viewport.
- Include loading, empty, error, disabled, validation, success, and destructive states where relevant.
- Meet accessibility expectations for contrast, focus, keyboard use, labels, and reduced motion.
- Reuse components and tokens when repetition reflects the same product concept.
- Prefer purposeful visual decisions over generic gradients, excessive glass effects, or decorative motion.

## Design Handoff

Document:

- user goal and critical flow
- layout and responsive behavior
- component and token reuse
- interaction and feedback states
- accessibility requirements
- unresolved decisions

When using a design-generation tool, provide the same context and requirements, inspect its output critically, and adapt the result to repository conventions before implementation.

## Anti-Rationalization

- Do not skip states because the screen appears simple.
- Do not treat generated visuals as implementation-ready.
- Do not invent brand tokens when established ones exist.
- Do not optimize aesthetics at the expense of task completion or accessibility.
