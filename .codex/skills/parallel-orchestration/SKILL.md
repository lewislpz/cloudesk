---
name: parallel-orchestration
description: Use when a task can be split into independent subproblems that benefit from parallel Codex sub-agents.
---

# Parallel Orchestration

## When To Use

Use this skill when you have distinct questions or disjoint implementation slices that can run in parallel without blocking the very next local step.

Use sub-agents only when the environment exposes them and the user or host policy
permits delegation. Otherwise apply the same decomposition locally.

## Pattern

1. Keep the immediate blocking task in the main thread.
2. Spawn `explorer` sub-agents for bounded read-only analysis.
3. Spawn `worker` sub-agents only with disjoint delegation contracts.
4. Integrate results in the main thread; do not duplicate delegated work.

## Rules

- Give each sub-agent one concrete output.
- Pass a contract based on `.codex/templates/delegation-contract.json` for write tasks.
- Do not parallelize high-risk implementation and its independent review.
- Reuse prior findings instead of re-exploring the same area.
- Wait only when the main thread is blocked on that result.
