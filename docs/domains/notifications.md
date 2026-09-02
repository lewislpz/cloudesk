# Notifications Domain

## Purpose

Notifications deliver relevant product events through in-app and email channels without coupling core transactions to provider availability.

## Sources And Rules

Eligible intents include invitation, task assignment, mention, deadline/overdue task, invoice issue/send/overdue, and operationally significant export completion. Domain modules emit durable facts; the Notifications module applies preferences, channel policy, deduplication, and templates.

- In-app records are PostgreSQL-backed and tenant-scoped.
- Email is asynchronous and provider delivery state is not confused with business state.
- Each intent has a stable deduplication key such as `(event_id, recipient, channel, template_version)`.
- Retries are bounded; permanent address/content failures go to a DLQ and suppress blind retry.
- Preferences never suppress mandatory security or billing notices when policy requires them.
- Notification payloads minimize sensitive data and links require normal authorization.

## Delivery States

`PENDING`, `PROCESSING`, `DELIVERED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, and `SUPPRESSED` support inspection and controlled replay. Provider callbacks, if added, are authenticated and idempotent.

See [asynchronous processing](../architecture/async-processing.md) and [resilience](../architecture/resilience.md).
