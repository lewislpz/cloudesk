# ADR-002: Use Next.js And TypeScript For The Frontend

## Status

Proposed

## Context

The product needs responsive authenticated workflows, typed API integration, accessible interaction states, and pragmatic server rendering.

## Decision

Use Next.js App Router, React, TypeScript, Tailwind CSS, and TanStack Query; add React Hook Form and Zod for complex forms.

## Alternatives Considered

A client-only React SPA simplifies rendering boundaries but gives up useful server rendering and routing conventions; other meta-frameworks do not improve the stated stack goals.

## Consequences

Server/client boundaries require discipline. Generated OpenAPI types reduce duplication while TypeScript improves contract feedback, not runtime trust.
