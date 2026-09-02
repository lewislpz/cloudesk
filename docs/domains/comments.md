# Comments Domain

## Purpose

Comments support discussion and mentions on tasks; project comments remain deferred until user evidence justifies a second context.

## Rules

- A comment includes organization, task, author membership, Markdown-safe body, timestamps, and edit metadata.
- The API validates tenant, task visibility, membership status, length, and supported formatting.
- Rendering sanitizes untrusted content; raw HTML is not trusted.
- Authors may edit within policy; privileged deletion creates a tombstone rather than erasing audit-relevant context.
- Mentions resolve only active memberships in the same organization and emit deduplicated notification intents after commit.
- Attachments use the [Files domain](files.md) and inherit task authorization.

## Audit And Retention

Create is normal activity history; edits and moderation/deletion retain actor and timestamp. Sensitive deleted content can be removed from normal reads while a minimal audit record preserves who acted and why, subject to retention policy.
