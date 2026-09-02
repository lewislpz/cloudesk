---
name: writing-plans
description: Use when you have a spec or requirements for a task, BEFORE touching code. This is the tactical blueprint for all implementations.
---

# Writing Implementation Plans

## Rules

1. **Granularity**: Tasks must be independently verifiable and small enough to resume
   safely. Use elapsed-time estimates only when they improve coordination.
2. **Standard Loop**:
   - Reproduce the behavior or write a meaningful failing test when practical.
   - Minimal code (GREEN).
   - Verify (PASS).
   - Mark task as done.
3. **Context**: Use repository-native paths, commands, architecture, and terminology.
4. **Risk**: Include rollout, migration, security, or recovery tasks when relevant.

## Plan Template

```markdown
# [Feature]
> Goal: [value]
> Architecture: [pattern]

### Task N: [File]
1. Reproduce or add a failing test in `<project-native test path>`.
2. Implement the smallest change in `<owned path>`.
3. Run `<project-native focused verification>`.
4. Update `docs/` if necessary.
5. Mark task as `[x]` in `plan.md`.
```
