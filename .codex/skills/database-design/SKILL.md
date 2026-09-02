---
name: database-design
description: Use when designing or reviewing schemas, persistence models, indexes, migrations, queries, or database selection.
---

# Database Design

## Boundaries

Use for persistence decisions. Do not choose a database or ORM before inspecting the
repository and deployment constraints.

## Operating Loop

1. Detect the current database, access layer, migration tooling, data volume,
   consistency requirements, and operational constraints.
2. Model invariants, ownership, relationships, lifecycle, and access patterns.
3. Select keys, constraints, indexes, and transaction boundaries from those patterns.
4. Plan backward-compatible migrations, rollback or roll-forward behavior, and data
   verification.
5. Verify representative queries and migration behavior with project-native tools.

## Decision Rules

- Preserve an existing database and ORM unless the task justifies migration cost.
- Enforce durable invariants in the database when practical.
- Add indexes for demonstrated access patterns and evaluate write cost.
- Treat destructive or irreversible migrations as high risk.
- Use structured columns or JSON based on query and evolution needs, not preference.

## Optional Reference

Load [legacy-guide.md](references/legacy-guide.md) only for its compact checklist.
