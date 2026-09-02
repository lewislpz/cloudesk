---
name: typescript-expert
description: Use when solving advanced TypeScript or JavaScript typing, migration, module, tooling, monorepo, or compiler-performance problems.
---

# TypeScript

## Boundaries

Use for advanced TypeScript and JavaScript problems. For routine React structure or
general code quality, prefer the narrower relevant skill.

## Operating Loop

1. Detect package manager, TypeScript version, module system, build tool, monorepo
   layout, strictness, generated types, and project-native commands.
2. Reproduce the type, module, build, or performance issue with the narrowest
   diagnostic command.
3. Preserve public contracts and existing configuration unless the change is
   intentionally migratory.
4. Prefer simpler types and project references over clever type-level machinery.
5. Verify type checking, affected tests, and build outputs using existing scripts.

## Decision Rules

- Do not install or execute optional tools merely because they appear in examples.
- Avoid broad `any`, unsafe assertions, and global augmentation unless the boundary
  requires and documents them.
- Treat ESM/CJS changes and strictness changes as migrations with compatibility plans.
- Profile compiler performance before changing types for speed.
- Keep runtime validation separate from static typing.

## Optional Reference

Load [legacy-guide.md](references/legacy-guide.md) selectively for advanced examples;
its tool recommendations are options, not defaults.
