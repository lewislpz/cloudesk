# Proposed SLIs, SLOs, And Error Budgets

## Purpose And Status

These are **initial internal targets to validate, not guarantees, contractual
commitments, or evidence of current service**. Values become active only after M11
instrumentation has valid data, an owner, exclusions, and a tested runbook. Review
quarterly and after material architecture or traffic changes.

## Measurement Rules

- Use rolling 28-day windows in production; staging proves calculations but has no
  external SLO. Preserve raw numerator/denominator recording rules across releases.
- Exclude synthetic probes, approved maintenance only when policy says so, obvious
  client validation/auth/permission/not-found/conflict responses, and tenant quota
  `429`. Count unexpected `5xx`, server timeouts, capacity `503`, global-overload
  `429`, and false success as bad. Never exclude a dependency failure merely because
  AWS or a provider caused it.
- “Valid request” exclusions are code- and route-owned; changing them requires SRE
  review. Missing/stale telemetry is unknown and alerts—it is never treated as good.
- Correctness invariants (cross-tenant leakage, duplicate financial effect, lost
  committed event) target zero tolerance and trigger incident response; an error
  budget is not permission to spend them.

## Initial Objective Set

| Capability | SLI | Proposed 28-day target | Budget at target |
| --- | --- | ---: | ---: |
| Public web/API availability | good eligible responses / eligible requests at CloudFront/ALB and app, reconciled | 99.9% | 0.1%; about 40m19s only as time intuition, while event-based accounting is authoritative |
| Interactive API latency | eligible successful requests below 300 ms / eligible successful requests; separate route classes | 95% below 300 ms and 99% below 1 s | 5% / 1% slow events |
| Critical command acceptance | committed or safely replayable idempotent timer/invoice commands / valid attempts | 99.9% | 0.1% failed/unresolved attempts; correctness remains zero-tolerance |
| Outbox publication freshness | committed deliveries published within 60 s / committed eligible deliveries | 99.9% | 0.1% late; any blocked delivery or oldest age above 5 min pages independently |
| Notification terminal time | durable notification intents reaching delivered/suppressed/permanent-failure state within 5 min / eligible intents | 99% | 1% late; provider policy failures remain visible |
| Document/report completion | eligible jobs terminal within 10 min / eligible jobs | 99% | 1% late; define size classes before activation |
| Browser critical journeys | successful server-confirmed completion / valid attempts for login, timer, invoice issue, file authorization | 99.5% per journey | 0.5%; browser data is diagnostic until sampling bias is validated |
| Telemetry pipeline | synthetic log/metric/trace canaries queryable within 5 min / emitted canaries | 99.5% internal objective | 0.5%; never a customer availability guarantee |

Core Web Vitals receive proposed p75 targets by route/device class (LCP at most 2.5 s,
INP at most 200 ms, CLS at most 0.1) after consent, sampling, and bias validation.
They are experience objectives, not proof that a business journey succeeded.

RPO/RTO are recovery objectives and live in [disaster recovery](disaster-recovery.md),
not this availability budget.

## Error Budget Policy

For target `S`, allowed bad fraction is `1-S`; burn rate is observed bad fraction
divided by allowed bad fraction over the same window. At 100% budget remaining,
normal feature delivery proceeds. Below 50%, owners review dominant causes and demand
growth. Below 25%, risky releases and capacity reductions pause. At exhaustion,
reliability fixes, rollback, and incident learning take priority; only security,
data-integrity, or risk-reducing changes bypass with explicit change ownership.

Budget policy never blocks emergency security patches, restores, or correctness
repairs. Low-traffic SLIs require a minimum-event guard plus synthetic/absolute-error
alerts; percentages from a handful of requests do not page reliably.

## Multi-Window Burn Alerts

Apply both long and short windows to reduce noise; initial thresholds must be replayed
against staging/synthetic history before paging:

| Severity | Condition for the same SLO | Meaning/action |
| --- | --- | --- |
| Page fast | burn at least 14.4x over 1 h **and** 5 min | Rapid budget loss; incident response |
| Page sustained | burn at least 6x over 6 h **and** 30 min | Material sustained degradation |
| Ticket/daytime | burn at least 3x over 24 h **and** 2 h | Slow persistent loss; owned remediation |
| Review | burn at least 1x over 72 h **and** 6 h | Budget trend is unsustainable |

In addition, page immediately for cross-tenant/correctness evidence, blocked outbox,
DLQ integrity events, backup/PITR loss, or total traffic/telemetry disappearance when
expected. See [alerting](alerting.md).

## Activation Checklist

Before activating an SLO: name product/technical owner; test query and exclusions;
prove volume and data freshness; replay burn rules; link dashboard/runbook; baseline
at least one representative window; record dependency and maintenance policy; and
obtain product approval if it may become customer-facing. Until then it remains a
proposal.

