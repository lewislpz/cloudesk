# Terraform And Infrastructure Promotion

## Purpose And Status

This document defines the proposed Terraform operating model for ClouDesk. It is an
implementation contract, not evidence of provisioned infrastructure: the repository
currently contains no Terraform configuration, state, AWS resources, or CI workflows.

The design implements [ADR-015](../decisions/ADR-015-terraform-iac.md) and stays
consistent with the [single-region Multi-AZ target](../decisions/ADR-013-aws-single-region-multi-az.md),
the [staged EKS platform](../decisions/ADR-014-eks-production-platform.md), and the
[GitOps delivery boundary](../decisions/ADR-016-gitops-delivery-model.md). Environment
shape is defined in [environments](environments.md), AWS ownership in
[AWS architecture](aws.md), and recovery objectives in
[disaster recovery](../architecture/disaster-recovery.md).

## Ownership Boundary

Terraform owns AWS account baselines and durable cloud primitives:

- VPCs, subnets, routes, endpoints, security groups, and NAT gateways;
- KMS keys, state storage, IAM roles and policies, GitHub OIDC trust, and EKS Pod
  Identity roles/associations (with explicit IRSA exceptions);
- EKS clusters, managed node groups or Karpenter prerequisites, ECR, RDS, S3, SQS,
  Secrets Manager containers, Route 53, ACM, WAF, CloudFront, budgets, and the
  selected AWS observability foundations;
- the minimal, pinned Argo CD bootstrap needed to establish GitOps reconciliation.

GitOps owns Kubernetes namespaces, service accounts, platform add-ons, Helm releases,
and application workloads after bootstrap. The AWS Load Balancer Controller owns the
ALB and target groups generated from a reviewed GitOps `Ingress`; Terraform owns the
VPC/subnet discovery tags, its workload IAM role/association, and the explicit ALB security-group boundary.
Terraform may discover the controller-created ALB by an exact name/tag contract when
configuring CloudFront and DNS, but it must not import or manage that ALB.

No AWS or Kubernetes object may be managed by both systems. Argo CD self-management
is handed over only through a documented state-removal/adoption procedure; deleting
the Terraform resource before GitOps has adopted the exact live object is prohibited.
Application image promotion and Kubernetes drift belong to GitOps, not Terraform.

## Account And Environment Isolation

The target account model is:

| AWS account | Purpose | Terraform state and apply boundary |
| --- | --- | --- |
| Management | AWS Organizations and billing only | Dedicated organization root; no workloads |
| Security/log archive | Organization audit and recovery copies | Dedicated security root with restricted operators |
| Shared tooling | CI integration and artifact-promotion support | Dedicated shared roots |
| Non-production | Separate dev and staging VPCs and services | Separate roots, state keys, roles, and approvals for each environment |
| Production | Production only | Dedicated state bucket/key hierarchy, KMS key, roles, and mandatory human approval |

Dev and staging may share the non-production account to control portfolio cost, but
they do not share a VPC, Terraform root, state object, secret path, or apply role.
Production never shares an account or state object with non-production. A smaller
initial AWS Organizations bootstrap may combine security/log archive and shared
tooling, but the management account remains workload-free and production remains
separate. Moving to or from consolidation requires a reviewed migration plan rather
than copying state.

Terraform CLI workspaces are not environment boundaries. Directory roots plus AWS
accounts, IAM, and separate backend keys make an accidental environment selection
visible in code review and enforceable in policy.

## Proposed Repository Layout

The implementation should begin under one infrastructure tree in the product
repository. A separate infrastructure repository is justified only when ownership or
permissions require it.

```text
infrastructure/terraform/
├── bootstrap/
│   ├── organization/             # accounts/OUs and organization-wide guardrails
│   ├── state/                    # state buckets, KMS, logging, recovery-copy policy
│   └── access/                   # GitHub OIDC and operator/apply role foundations
├── modules/
│   ├── account-baseline/
│   ├── network/
│   ├── registry/
│   ├── data-services/            # RDS, service buckets, optional Redis
│   ├── messaging/                # queues, DLQs, policies, alarms
│   ├── eks/
│   ├── workload-iam/
│   ├── edge/                     # Route 53, ACM, WAF, CloudFront
│   ├── observability/
│   └── budget/
├── roots/
│   ├── shared-tooling/
│   │   ├── registry/
│   │   └── ci-foundation/
│   └── environments/
│       ├── dev/
│       │   ├── foundation/
│       │   ├── data/
│       │   ├── platform/
│       │   └── edge/
│       ├── staging/
│       │   └── ...
│       └── production/
│           └── ...
├── policies/                     # machine-enforced IaC policy
└── tests/                        # module and disposable-account tests
```

Each root is independently initializable and has its own backend key and dependency
lock file. Roots are split by lifecycle and blast radius rather than by every AWS
service:

1. `foundation` owns regional networking, baseline KMS and shared security boundaries.
2. `data` owns RDS, S3, SQS and optional ElastiCache resources with independent
   retention and destruction controls.
3. `platform` owns EKS, node capacity, cluster IAM, Pod Identity roles/associations, and the minimal Argo CD
   bootstrap.
4. GitOps reconciles cluster add-ons, ingress, and workloads.
5. `edge` runs after the controller-created ALB exists and owns the CloudFront/WAF/ACM/
   Route 53 path to that origin.

This ordering is an explicit deployment graph, not an invitation to use `-target`.
Normal plans always cover a complete root.

Reusable modules expose cohesive inputs and outputs and contain no backend or provider
configuration. Provider configurations and account assumption live only in roots.
Modules are private to this repository initially; extracting or publishing them is
appropriate only after a second real consumer proves a stable interface.

## Root Contracts And Cross-State Dependencies

Every root declares its account ID, region, environment, state key, expected caller
identity, module revision, and required tags. A precondition must fail when the active
account or region differs from the root contract.

Only non-secret identifiers needed by a later layer are exported. Prefer exact AWS
lookups by immutable ID or mandatory tags, or publish a small, non-secret environment
contract to Parameter Store. `terraform_remote_state` is allowed only when a root
cannot use an AWS lookup and the consumer role has read access to that one upstream
state object. It must not grant broad bucket access, and sensitive outputs are never
used as a configuration bus.

Changing a root output is an API change. Consumers are located and planned before the
producer applies; removals use an additive/deprecation period. Cyclic state
dependencies are prohibited.

## Terraform Core, Providers, And Modules

The initial compatibility policy is explicit without silently following `latest`:

| Dependency | Root constraint | Reusable-module constraint | Selection policy |
| --- | --- | --- | --- |
| Terraform CLI | `>= 1.10.5, < 2.0.0` | same minimum, no tighter patch pin | Repository tool file and CI pin one tested stable patch; prereleases are forbidden |
| `hashicorp/aws` | `>= 6.0, < 7.0` | minimum compatible `>= 6.0` | Each root commits the exact selected release and checksums in `.terraform.lock.hcl` |
| `hashicorp/helm` | `>= 3.0, < 4.0`, platform bootstrap only | not used elsewhere | Exact selected release locked per platform root |
| `hashicorp/kubernetes` | `>= 2.0, < 3.0`, only if the minimal bootstrap requires it | not used by AWS modules | Exact selected release locked per platform root |

An implementation spike must validate the selected patch releases together before
the first AWS apply. Additional providers require a concrete resource need and the
same bounded constraint and checksum policy. Do not use utility providers to generate
long-lived credentials that would persist plaintext values in state.

Provider and Terraform upgrades use a dedicated pull request, review upstream upgrade
notes, regenerate platform checksums, run all affected plans, and promote through dev,
staging, then production. Major upgrades require an ADR or an explicit amendment to
ADR-015. Remote modules, if ever introduced, use immutable release versions or commit
SHAs; floating branches are forbidden.

## Naming And Tagging

AWS names use lowercase tokens where supported:

```text
clouddesk-<environment>-<region-code>-<component>[-<purpose>]
```

Globally unique names add a stable account ID or deterministic non-secret suffix. Do
not place tenant IDs, customer names, email addresses, or other business data in AWS
names or tags. `environment` is exactly `dev`, `staging`, or `production`; `prod` is
not a second spelling.

The AWS provider applies these mandatory default tags and modules propagate them to
resource types that do not inherit provider defaults:

| Tag | Contract |
| --- | --- |
| `Application` | `ClouDesk` |
| `Environment` | `dev`, `staging`, or `production` |
| `Owner` | Owning team, initially `platform` |
| `ManagedBy` | `Terraform` |
| `CostCenter` | Approved cost-allocation value; never an empty placeholder |
| `DataClassification` | `Public`, `Internal`, `Confidential`, or `Restricted` |
| `Repository` | Canonical repository identifier |
| `TerraformRoot` | Stable path-qualified root identifier |

Required tags cannot be overridden by a module caller. Policy tests reject missing or
invalid values. Controller-created resources use matching Kubernetes annotations/tags
where AWS supports them, while their `ManagedBy` value identifies the controller
rather than falsely claiming Terraform ownership.

## Remote State And Native Locking

State uses the S3 backend with partial, non-secret backend configuration:

- `use_lockfile = true` enables native S3 lock files; every runner uses one pinned
  Terraform version that CI proves supports this backend contract;
- DynamoDB locking is not created for new roots because the S3 backend's DynamoDB
  locking path is deprecated. A legacy migration may configure both locks temporarily,
  prove that all runners support S3 locking, and then remove DynamoDB in a separate
  reviewed change;
- state buckets block public access, require TLS, enable versioning, encrypt with a
  customer-managed KMS key, record access, and deny deletion outside a break-glass
  recovery role;
- backend IAM allows `GetObject`/`PutObject` on the exact state object. It allows
  `GetObject`/`PutObject`/`DeleteObject` on the adjacent `.tflock`, but does not grant
  `DeleteObject` on the state object;
- production uses a dedicated bucket/key hierarchy and KMS key. Shared-tooling and
  non-production state may share a hardened bucket only with prefix-scoped policies;
- state keys are deterministic, for example
  `clouddesk/<account-purpose>/<environment>/<root>/terraform.tfstate`.

This follows the official [Terraform S3 backend contract](https://developer.hashicorp.com/terraform/language/backend/s3),
including native lock-file permissions, bucket versioning, and the deprecation of
DynamoDB-based locking.

Versioning is the primary accidental-change recovery source. The production readiness
decision must explicitly choose between an encrypted cross-account backup/replica in
the security/log archive account and accepting the slower state reconstruction path.
An off-region copy is a separately approved recovery artifact, not an active
multi-region runtime or a default claim of regional RTO. Any destination uses an
independent KMS key, and a copied `.tflock` is never authoritative during recovery.
State bucket and KMS deletion controls, version retention, the chosen recovery-copy
policy, and restore tests are required before production.

State is sensitive even when Terraform marks outputs as sensitive. It may include
resource identifiers, policies, generated values, or provider-returned data. State and
binary plan access is restricted to environment-specific CI roles and a small
break-glass operator group; it is never attached to issues, pasted into logs, or
committed to Git.

CI concurrency is keyed by account, environment, and root. A waiting job times out
and reports the owner rather than using `force-unlock`. Forced unlock is permitted only
after CloudTrail/GitHub evidence proves no writer is active and the lock ID is recorded.

## Bootstrap And State Recovery

Bootstrap is deliberately small and separately controlled because Terraform cannot
initially depend on a backend or OIDC role that does not exist.

1. An authorized operator uses an AWS IAM Identity Center session, never a static
   access key, to establish accounts/OUs and run the state bootstrap locally.
2. `bootstrap/state` creates state buckets, KMS keys, logging, versioning, recovery
   copies, and deletion controls. Its initial local state is treated as a secret.
3. The bootstrap state is immediately migrated to its final remote backend and the
   remote object, version, lineage, and a no-change plan are verified before the local
   copy is securely removed.
4. `bootstrap/access` establishes tightly scoped GitHub OIDC and break-glass roles.
   Subsequent root operations run in CI; bootstrap changes retain additional review.
5. The bootstrap runbook records account IDs, regions, bucket/key names, KMS aliases,
   recovery-copy locations, and role ARNs, but no credentials or state content.

For state corruption or deletion:

1. freeze applies and revoke or disable the affected apply role;
2. preserve the current object version, lock metadata, CloudTrail events, and plan/run
   evidence for investigation;
3. select the last verified S3 version or recovery copy and restore it to an isolated
   key first;
4. verify encryption access, lineage, serial, and expected resource inventory, then
   compare a refresh-only plan and a normal plan against AWS;
5. restore the production key only after review, re-enable applies, and reconcile any
   real drift explicitly.

If no trustworthy state survives, recreate only the empty backend, inventory AWS
resources, write configuration, and import them root by root. Never push guessed or
hand-edited JSON state. A regional rebuild uses reviewed Terraform plus recovered
state where valid, GitOps desired state, immutable artifacts, and restored data as
defined by [disaster recovery](../architecture/disaster-recovery.md).

## IAM, GitHub OIDC, And Workload Identity

GitHub Actions uses AWS OIDC federation only. Each account/environment has separate
plan and apply roles with trust restricted to the canonical repository, expected
GitHub organization, `sts.amazonaws.com` audience, and an exact branch or protected
GitHub Environment `sub` claim. Pull requests from forks receive no AWS role.

- Plan roles can read the resources in their root and read state; they can create and
  remove only the corresponding lock file. They cannot mutate target resources or
  write production state.
- Apply roles can mutate only resource families and state prefixes owned by that root.
  They are not account administrators and cannot alter their own OIDC trust, state
  protection, or organization guardrails.
- Bootstrap roles are separate from normal apply roles. Human access uses IAM Identity
  Center with MFA; break-glass sessions are short, alerted, and audited.
- Session names include repository, workflow, run ID, and commit so CloudTrail can
  attribute a change. Session duration is bounded to the root's expected apply time.

Terraform creates one least-privilege EKS Pod Identity role and association per
Kubernetes service account and workload purpose. GitOps creates the matching service
account; no workload annotation is required for Pod Identity. The association binds
cluster, namespace, and service-account name, while IAM trust uses the EKS Pod Identity
service principal and policies may use emitted session tags. Application pods never
receive node-role or static AWS credentials. Any IRSA exception records why, creates
cluster OIDC trust explicitly, and receives equivalent least privilege.

## Secrets And Sensitive Values

Terraform creates secret containers, KMS policies, rotation wiring, and workload
permissions, not application secret values in Git or ordinary `tfvars` files.

- Prefer AWS-managed generation where available, such as RDS-managed master
  credentials stored in Secrets Manager.
- Runtime workloads fetch secrets through the documented Kubernetes/Secrets Manager
  integration and Pod Identity. CI receives no application database password.
- Environment variable files, command-line `-var` values, GitHub output, plan JSON,
  module outputs, and state outputs must not carry secret material.
- When a provider forces a sensitive value into state, document the exception, mark
  every output sensitive, minimize readers, rotate after exposure, and prove log and
  plan redaction.
- Secret rotation is an application/platform operation. `ignore_changes` may be used
  only on a provider-managed secret value with a documented external owner; it must
  not hide policy, metadata, or rotation drift.

## Plan, Approval, And Apply Workflow

Every pull request runs repository-local deterministic checks and a speculative plan
for each affected root. Plans identify the exact commit, root, account, region,
Terraform/provider lock hashes, backend state serial, and policy-check results.
Human-facing summaries must not expose sensitive values.

After merge, CI creates a fresh saved binary plan from the merged commit. The apply job
uses that exact plan, verifies its hash and commit, and refuses stale plans when state,
configuration, locks, or provider selections changed. The restricted plan artifact has
minimal retention and is available only to the apply workflow.

| Environment/root | Apply policy |
| --- | --- |
| Dev | May auto-apply an approved merged change after all gates; concurrency remains serialized |
| Staging | Promotion PR plus protected environment; platform reviewer checks plan and application compatibility |
| Production | Separate promotion PR and protected environment with mandatory authorized human approval; proposer cannot use an unreviewed re-plan |
| Bootstrap, organization, state, IAM trust | Always protected and reviewed regardless of environment |

Production applies have a maintenance/change record when the plan includes replacement,
networking, IAM trust, data-store, or state changes. If a plan changes after approval,
approval is invalid and must be obtained on the new plan. `terraform apply -auto-approve`
is acceptable only inside an already approved protected job applying the verified
saved plan; interactive local production apply is prohibited.

## Infrastructure Promotion

Promotion changes configuration, not state. A module or root change is applied to dev,
observed, applied to production-shaped staging, and then promoted by a separate PR to
production. The production root consumes the same reviewed module commit and provider
selection proven in staging; environment-specific variables express capacity,
retention, and availability differences.

State is never copied between environments. Production data is never used to validate
dev. Global/shared-tooling changes are promoted through a sandbox or non-production
equivalent before their protected root. The promotion record links source commit,
plans, applies, smoke checks, and restore or rollback considerations.

Terraform does not promote application images or Helm values. CI builds an immutable
image once, and the [GitOps flow](../decisions/ADR-016-gitops-delivery-model.md) promotes
its digest independently. Infrastructure and workload changes that depend on each
other use backward-compatible sequencing: provision capability first, deploy the
consumer, observe, then remove the old capability in a later change.

## Drift Detection And Reconciliation

Scheduled CI runs a refresh-backed `terraform plan -detailed-exitcode` for every root
at least daily and after relevant AWS security/configuration alerts. Exit code 2 opens
or updates an owned drift finding with account, root, resources, and run link; it does
not auto-apply. Production drift pages the platform/security owner only when the
change affects an agreed critical control.

The owner chooses one explicit reconciliation path:

1. remove unauthorized drift by applying reviewed Terraform;
2. accept intentional emergency state by first encoding and reviewing configuration,
   then proving a no-surprise plan; or
3. import a previously unmanaged resource through the import procedure below.

Broad `ignore_changes` blocks, refresh-disabled plans, and scheduled automatic applies
are prohibited. Narrow ignores document the external controller, exact attributes,
and removal trigger. Terraform does not report GitOps/Kubernetes drift or the
controller-owned ALB as its own drift.

## Verification And Security Gates

The planned CI matrix is proportional to scope:

- `terraform fmt -check -recursive` and `terraform validate` for every module/root;
- provider lock-file verification for CI and supported developer platforms;
- `tflint` with AWS rules and repository naming/tagging rules;
- Checkov (or one centrally selected equivalent) for encryption, public exposure,
  logging, IAM, backup, and destructive-default policies;
- `terraform test` for module contracts, validation, tags, and negative cases using
  mocked providers where behavior permits;
- speculative plans plus policy checks rejecting wildcard IAM, public data stores,
  unencrypted state/data, missing backup/deletion controls, wrong account/region, and
  unapproved replacement of critical resources;
- disposable sandbox-account integration tests for networking, IAM denial, encrypted
  storage, EKS prerequisites, and teardown. They never run destructive tests in
  staging or production;
- an advisory cost delta for material changes, with a blocking budget review when a
  change introduces a fixed-cost service or exceeds the environment threshold.

Security scanners supplement, not replace, reviewed plans and AWS-level verification.
The production gate must verify actual bucket public-access blocks, KMS policies,
CloudTrail attribution, OIDC trust claims, restore behavior, and least-privilege denial
paths before declaring the design operational.

## Destruction And Replacement Protection

CI has no general production destroy workflow. Production RDS, state buckets, KMS
keys, service S3 buckets, ECR repositories, hosted zones, and recovery copies use
service-native deletion protection/retention plus Terraform `prevent_destroy` where
supported. Organization SCPs or role policies deny critical deletion outside an
audited break-glass path.

A legitimate destructive change requires a dedicated plan, named resource inventory,
backup/restore evidence, dependency and data-retention review, explicit production
approval, and a post-change validation. `terraform destroy`, `-target`, state removal,
replacement flags, and local production applies are not routine recovery shortcuts.
Ephemeral sandbox roots are the only roots with a normal automated destroy path, and
they enforce account allowlists and TTL tags.

## Imports, Refactors, And Evolution

Console-created or externally managed AWS resources are not silently adopted:

1. stop manual mutation and identify the authoritative owner;
2. capture inventory, dependencies, tags, account, and recovery implications;
3. write the intended configuration and an explicit Terraform import block;
4. import into a non-production-equivalent root first where possible;
5. require a plan showing no unintended update or replacement before normal
   management begins; and
6. remove the import block only after the migration is recorded and reproducible.

Refactors use Terraform `moved` blocks and proceed one root/environment at a time.
They do not use raw `terraform state mv` as an undocumented team workflow. Removing a
resource from Terraform while retaining the AWS object uses an explicit ownership
transfer and supported removal mechanism, then verifies that the new owner has
adopted it. Provider address changes and module splits preserve state lineage and are
tested against a copied state in isolation before production.

State schema, module output, provider-major, account-boundary, and backend changes are
hard-to-reverse migrations. Each requires rollback/recovery steps and promotion
evidence. Smaller implementation details remain local to modules so ClouDesk can
evolve without combining states or creating a platform abstraction before a real
second consumer exists.

## Open Decisions Before Implementation

- Select the AWS region and record its short naming code.
- Set account IDs, canonical GitHub organization/repository claims, cost-center value,
  state retention, backup region, and authorized approval groups.
- Validate exact stable Terraform and provider patch versions and commit the generated
  lock files; the ranges above are the compatibility boundary, not proof of testing.
- Choose the concrete policy scanner and cost threshold once CI ownership and budgets
  exist.
- Measure whether dev needs EKS or can use a cheaper runtime while preserving the same
  application contracts; this does not change staging/production Terraform isolation.

These values are configuration and governance inputs. They do not reopen the selected
Terraform, S3 native-locking, GitHub OIDC, account-isolation, or GitOps ownership
decisions.
