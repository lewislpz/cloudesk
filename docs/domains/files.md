# Files Domain

## Purpose

The Files module owns metadata and authorization for tenant objects stored in Amazon S3 or a local S3-compatible development service.

## Model And Lifecycle

A file record includes organization, uploader, related resource, opaque storage key, original filename, media type, expected/actual size, checksum, status, scan status, timestamps, and retention/deletion metadata. PostgreSQL owns the lifecycle; S3 owns bytes only.

```mermaid
stateDiagram-v2
    [*] --> PENDING_UPLOAD
    PENDING_UPLOAD --> UPLOADED: completion verified
    UPLOADED --> SCANNING: scan required
    SCANNING --> READY: clean
    SCANNING --> QUARANTINED: suspicious
    UPLOADED --> READY: scan not required
    PENDING_UPLOAD --> EXPIRED
    READY --> DELETED
    QUARANTINED --> DELETED
```

## Upload Flow

```mermaid
sequenceDiagram
    actor Browser
    participant API as Go API
    participant DB as PostgreSQL
    participant S3
    Browser->>API: request upload (tenant resource, type, size)
    API->>DB: authorize and create PENDING_UPLOAD metadata
    API->>S3: create short-lived constrained presigned URL
    API-->>Browser: URL + opaque file ID
    Browser->>S3: direct upload
    Browser->>API: complete upload
    API->>S3: verify object metadata/checksum
    API->>DB: mark UPLOADED / enqueue scan
```

## Security And Failure Rules

- Object keys are opaque and tenant-prefixed; bucket listing is never granted to browsers.
- URLs are short lived and operation-specific; possession is treated as temporary bearer access.
- Type, extension, size, checksum, and resource permission are validated; dangerous inline content is downloaded with safe disposition.
- Bucket access is private, encrypted, versioned where required, and restricted by workload identity.
- A failed or abandoned upload expires and is reconciled; an S3 delete occurs after durable deletion intent and is retryable.
- Malware scanning is a production-target asynchronous step for risky content. Quarantined objects cannot receive download URLs.

Lifecycle and recovery policies are defined in [backups](../operations/backups.md).
