# ADR-014: Use EKS As A Staged Production Platform

## Status

Proposed

## Context

The target should demonstrate portable workload orchestration, independent API/worker scaling, GitOps, and AWS identity integration, while local V1 must remain cheap.

## Decision

Target Amazon EKS for staging/production after application foundations; use Docker Compose locally and evaluate a smaller dev runtime to control cost.

## Alternatives Considered

ECS/Fargate is operationally simpler and remains a valid cost alternative; self-managed Kubernetes adds undifferentiated control-plane work.

## Consequences

EKS adds fixed cost and platform expertise. Helm, EKS Pod Identity (with explicit IRSA exceptions), autoscaling, upgrades, quotas, policies, and observability become explicit operational responsibilities.
