# Reporting And Analytics Domain

## Purpose

Reporting exposes delivery and financial insight without introducing a data warehouse before access patterns and scale justify it.

## Initial Metrics

Active projects, completed tasks, tracked and billable hours, revenue, outstanding/overdue invoices, team utilization, and client profitability are computed within an explicit organization and date range.

## Query Tiers

- **Interactive operational queries:** bounded, indexed aggregates over current PostgreSQL data for dashboard cards and lists.
- **Precomputed aggregates:** daily tenant summaries created by idempotent jobs when measured queries exceed latency or load budgets.
- **Exports:** asynchronous, point-in-time jobs writing authorized files to S3 with retention metadata.
- **Future analytical platform:** considered only when reporting workloads materially harm OLTP or cross-period analysis outgrows PostgreSQL.

## Correctness And Access

Financial reports derive from issued invoice snapshots; utilization derives from valid time entries and explicit capacity assumptions. All aggregates and cache keys include organization scope. Currency values are never summed across currencies without an explicit conversion policy and rate source. Reporting permission is separate from ordinary resource visibility.

## Performance Triggers

Measure query duration, scanned rows, buffer reads, replica/primary load, export queue age, and cache hit rate. Add precomputation before read replicas; add a replica before a warehouse only if consistency and query shape permit it. The likely first bottleneck is PostgreSQL connection/query pressure from tenant lists and aggregates, not API CPU.
