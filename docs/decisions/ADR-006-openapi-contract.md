# ADR-006: Make OpenAPI The HTTP Contract

## Status

Proposed

## Context

Go and TypeScript clients need one versioned description of routes, schemas, errors, and compatibility.

## Decision

Maintain OpenAPI 3.1 as the source of truth, validate Go requests/responses against it, and generate the TypeScript client/types.

## Alternatives Considered

Duplicated handwritten DTOs drift; GraphQL adds a runtime and authorization model not required by current resource workflows.

## Consequences

Contract review and breaking-change checks become CI gates. Generated code is never edited manually and domain models remain internal.
