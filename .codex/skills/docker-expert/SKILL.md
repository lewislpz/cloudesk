---
name: docker-expert
description: Use when implementing or reviewing Dockerfiles, Compose, container security, networking, build performance, or runtime behavior.
---

# Docker

## Boundaries

Use for container concerns. Do not redesign application architecture or deployment
orchestration unless the task explicitly includes it.

## Operating Loop

1. Inspect Dockerfiles, Compose files, ignore rules, build context, target platforms,
   runtime requirements, and existing validation commands.
2. Classify the task as build correctness, image size, security, development
   ergonomics, networking, persistence, or runtime reliability.
3. Preserve existing base-image and orchestration choices unless a measurable problem
   justifies change.
4. Apply least privilege, deterministic dependencies, minimal build context, and
   explicit runtime configuration.
5. Validate configuration first, then build and run only the narrowest relevant
   targets.

## Decision Rules

- Never bake secrets into image layers.
- Prefer multi-stage builds when they reduce runtime contents or toolchain exposure.
- Use non-root execution when the application permits it.
- Add health checks only when they represent meaningful service health.
- Keep development conveniences out of production targets.

## Optional Reference

Load [legacy-guide.md](references/legacy-guide.md) only for examples matching the
detected language and Docker tooling.
