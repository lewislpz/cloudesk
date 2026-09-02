# Proposed Backup And Restore Controls

## Purpose And Scope

This is a planned backup policy for authoritative business data and recovery sources;
no backup exists yet. Multi-AZ, replicas, Git, S3 versioning, and immutable images each
solve different failures and none alone is a complete backup. Recovery objectives and
disaster orchestration are in [disaster recovery](disaster-recovery.md).

## Recovery Inventory

| Asset | Proposed protection | Restore verification |
| --- | --- | --- |
| RDS PostgreSQL | Automated backups/PITR, proposed 35-day production window; encrypted manual snapshot before high-risk migrations; deletion protection and final-snapshot policy | Quarterly isolated PITR at sampled point, schema/tenant/financial/outbox/idempotency checks, application smoke and measured recovery point/time |
| S3 business objects | Private encrypted versioned buckets; noncurrent-version retention, incomplete-upload cleanup, lifecycle consistent with deletion/legal policy; cross-Region copy only after explicit residency/risk decision | Recover representative current, overwritten, deleted, quarantined, PDF and export objects and reconcile PostgreSQL metadata/checksum/state |
| Terraform state | S3 backend versioning, KMS, access logs, native lock file, deletion-denied role; production decision for encrypted cross-account/off-Region copy | Restore chosen version to isolated key, verify lineage/serial/inventory, refresh-only and normal plan; never hand-edit state |
| GitOps/application desired state | Protected Git history, reviewed Helm values and Argo configuration; independent repository/provider recovery plan | Bootstrap Argo, reconcile isolated cluster, verify no secret values and no unmanaged drift |
| ECR artifacts | Immutable digest, scan evidence, lifecycle retaining deployed and rollback/recovery digests; optional cross-account/Region replication by DR tier | Pull/verify signature/digest and start the known-good release without rebuild |
| Secrets/KMS | Secrets Manager configuration, rotation/recreation procedure, protected KMS keys/grants and deletion windows | Prove recovery environment can obtain/rotate required secrets without copying plaintext into docs/state |
| SQS/outbox/DLQ | PostgreSQL outbox is durable publish intent; SQS/DLQ retention is short-term transport, not a business backup | Replay canary with same event ID and inbox deduplication; reconcile in-flight messages around DB restore |

The PostgreSQL deletion ledger survives tenant-data purge long enough to reapply
completed deletion obligations to an older restore. Restoring a backup must not
resurrect data that policy already required deleted.

## Backup Operations

- Terraform owns retention, encryption, alarms, deletion protection, lifecycle, and
  copy policy; console mutations are break-glass and reconciled.
- Backup roles are separate from application, normal apply, and restore roles. KMS
  grants, cross-account copies, and CloudTrail are tested; a backup encrypted by an
  unavailable/deleted key is not recoverable.
- Monitor last success, restorable-window bounds, copy lag/failure, snapshot age,
  versioning/lifecycle drift, state versions, ECR digest retention, and restore-drill
  age. Alerts contain metadata only.
- Never copy production data to local/dev/staging. Restore drills use an isolated
  production-recovery boundary with access, egress, telemetry, and a verified teardown plan.
- Backup retention must match financial/audit, privacy, deletion, legal hold, and cost
  policies. “Keep forever” is not a safe default.

## Standard RDS PITR Exercise

1. Choose a timestamp and compute expected latest durable transactions; record start.
2. Restore to a new isolated RDS instance with no customer traffic or worker egress.
3. Apply only documented compatible configuration; never point production at it yet.
4. Validate migrations, constraints, tenant isolation samples, invoice/time totals,
   audit/outbox/inbox/idempotency consistency, and deletion ledger.
5. Reconcile representative S3 versions and run read-only plus controlled synthetic
   application smoke tests using the pinned ECR digest.
6. Measure achieved recovery point and restore/application-ready times, document gaps,
   then securely destroy the drill environment under its approved teardown policy.

A successful backup job is not restore evidence. Quarterly restore results are
retained with timestamps, artifact versions, measured RPO/RTO, findings, owner, and
remediation deadline.
