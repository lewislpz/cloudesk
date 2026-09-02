# ClouDesk Product Vision

## Purpose

ClouDesk is a proposed multi-tenant SaaS for freelancers, consultancies, small agencies, and professional-service teams. It brings client delivery, project execution, time capture, invoicing, files, collaboration, reporting, notifications, and auditability into one coherent workflow.

## Product Outcome

The first useful release should let a team create an organization, invite members, manage clients and projects, assign tasks, record billable time, and turn approved time into an invoice. Reliability and tenant isolation are product behavior, not later infrastructure polish.

## Product Principles

- Make billable work traceable from task to time entry to invoice line.
- Keep organization boundaries visible and deny cross-organization access by default.
- Prefer explicit state machines and durable invariants over generic CRUD.
- Keep V1 operable by a small team; add distributed complexity only for measured needs.
- Make important actions explainable through audit events and correlation IDs.
- Treat accessibility, responsive behavior, and actionable failures as baseline quality.

## Personas

- **Owner:** configures the organization, billing, security, and membership.
- **Operations manager:** oversees clients, delivery, workload, and invoice lifecycle.
- **Contributor:** executes tasks and records time.
- **Finance collaborator:** prepares, issues, sends, and reconciles invoices.
- **Viewer:** reads permitted delivery and reporting information without mutation rights.

## Success Signals

Proposed product signals include activation through first project, timer-to-invoice completion rate, weekly active organizations, billable-time capture rate, overdue invoice value, task cycle time, and support/security incidents. Technical signals are defined in [SLIs and SLOs](../operations/sli-slo.md).

## Scope Horizon

- **Local V1:** core organization-to-invoice workflow on one local stack.
- **Production target:** single AWS region, Multi-AZ data services, EKS workloads, observable asynchronous processing, and automated delivery.
- **Future evolution:** payments, advanced forecasting, stronger MFA policy, regional expansion, and service extraction only when explicit triggers occur.

This document describes intent, not implemented functionality. See the [requirements](requirements.md) and [roadmap](../roadmap/milestones.md).
