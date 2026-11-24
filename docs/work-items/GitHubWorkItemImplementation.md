# GitHub Work Item Implementation

**Project:** Phantom Logic
**Document Status:** Initial Design
**Version:** 1.1
**Last Updated:** 21 November 2026

---

## 1. Purpose

This document defines how Phantom Logic will implement its Work Item Management system using GitHub.

It translates the work-item hierarchy, state transitions, development workflow, and code-review requirements defined in the following documents into a practical GitHub implementation:

- `Documentation/WorkItemManagement.md`
- `Documentation/StateTransitionMatrix.md`
- `Standards/CodingStandards.md`
- `Standards/CodeReviewGuidelines.md`

The objective is to use GitHub for work-item storage, collaboration, source control, and automation while maintaining deterministic enforcement of Phantom Logic's business rules.

## 2. Architectural Principles

The implementation will follow these principles.

### 2.1 GitHub as the Work Management Platform

GitHub will provide:

- Issues for work items.
- Issue Types for work-item classification.
- Issue Fields for structured work-item metadata.
- Native parent/sub-issue relationships.
- Issue relationships for associations between work items.
- GitHub Projects for work-item tracking and reporting.
- Pull Requests for code promotion and review.
- GitHub Actions for automation and enforcement.
- Repository rulesets for branch protection.

### 2.2 Work Item Manager as the Workflow Authority

The Python Work Item Manager will be responsible for enforcing Phantom Logic's workflow rules.

It will:

- Validate work-item relationships.
- Validate state transitions.
- Enforce agent permissions.
- Apply authorized state propagation.
- Evaluate parent completion eligibility.
- Enforce Change Request and Bug rules.
- Enforce code-review requirements.
- Maintain Blocked return states.
- Reject invalid operations.
- Record significant operations in the audit system.

GitHub will store the resulting work-item information, but agents must not bypass the Work Item Manager when performing controlled workflow operations.

### 2.3 GitHub Actions as the Enforcement Mechanism

GitHub Actions will execute automated checks and invoke the Work Item Manager where required.

Examples include:

- Validating Pull Requests.
- Checking Feature-level review completion.
- Checking required work-item associations.
- Preventing unauthorized merges.
- Updating work-item states after qualifying events.
- Triggering audit operations.

### 2.4 Deterministic Workflow

The Work Item Manager must be deterministic.

The same input and current work-item state must always produce the same validation result and permitted transition.

An AI agent may request an operation, but it must not independently override workflow rules.

---

## 3. High-Level Architecture

```text
                         GitHub
                            |
             +--------------+--------------+
             |              |              |
           Issues        Projects       Pull Requests
             |              |              |
             +--------------+--------------+
                            |
                     GitHub Webhooks
                            |
                            v
                   GitHub Integration
                            |
                            v
                    Work Item Manager
                            |
             +--------------+--------------+
             |              |              |
         Validation     State Rules    Permissions
             |              |              |
             +--------------+--------------+
                            |
                            v
                       Audit Writer
                            |
                            v
                         Audit Log
```

GitHub Actions will also invoke the Work Item Manager for operations that must be checked before a Pull Request can merge.

The Work Item Manager must be usable independently of GitHub so that its business rules can be tested without making real GitHub API calls.

---

## 4. GitHub Work Item Representation

Every Phantom Logic work item will be represented by a GitHub Issue.

GitHub Issue Types will distinguish the different work-item categories.

### 4.1 Issue Type Mapping

| Phantom Logic Work Item | GitHub Issue Type |
|---|---|
| Epic | Epic |
| Feature | Feature |
| Use Case | Use Case |
| Requirement | Requirement |
| Development Task | Development Task |
| Architecture Task | Supporting Task |
| Design Task | Supporting Task |
| Security Task | Supporting Task |
| DevOps Task | Supporting Task |
| Code Review Task | Code Review Task |
| Test Case | Test Case |
| Bug | Bug |
| Change Request | Change Request |

Supporting Tasks share one Issue Type. Their specific category will be recorded through a dedicated Issue Field.

Issue Types should be configured in GitHub account settings and applied consistently.

The proposed types are within GitHub's supported limit of 25 custom Issue Types.

### 4.2 Issue Titles

Issue titles must be concise and descriptive.

Examples:

```text
[Feature] Inventory Management
[Use Case] Create Inventory Item
[Requirement] Validate Inventory Item Details
[Development Task] Implement Inventory Creation
[Bug] Inventory Quantity Allows Negative Values
[Change Request] Add Inventory Export
[Code Review] Inventory Management
[Test Case] Validate Inventory Quantity
```

The Issue Type is the authoritative classification. The title prefix is optional descriptive text and must not be used as the primary means of identifying the work-item type.

### 4.3 Issue Bodies

Each Issue must use a structured body template appropriate to its Issue Type.

Examples of required content:

**Requirement**

- Description.
- Business rules.
- Acceptance criteria.
- Dependencies.
- Related Test Cases.

**Development Task**

- Implementation objective.
- Related Use Case.
- Related Requirements.
- Expected implementation scope.

**Bug**

- Description.
- Steps to reproduce.
- Expected behavior.
- Actual behavior.
- Violated Requirement.
- Failed Test Case, where applicable.
- Evidence.

**Change Request**

- Requested change.
- Business justification.
- Affected Requirements.
- Impact assessment.
- Approval information.

**Code Review Task**

- Related Feature.
- Review scope.
- Related Development Tasks.
- Pull Requests.
- Reviewed commits.
- Review Result.
- Review findings.

Templates improve consistency, but the Work Item Manager must validate required information. A template alone is not an enforcement mechanism.

---

## 5. Work Item Hierarchy and Relationships

GitHub's native parent/sub-issue relationships will represent the primary hierarchy.

### 5.1 Parent-Child Mapping

The intended hierarchy is:

```text
Epic (Optional)
└── Feature
    ├── Use Case
    │   ├── Requirement
    │   └── Development Task
    │
    ├── Supporting Task
    └── Code Review Task
```

The relationship mapping is:

| Parent | Child |
|---|---|
| Epic | Feature |
| Feature | Use Case |
| Feature | Supporting Task |
| Feature | Code Review Task |
| Use Case | Requirement |
| Use Case | Development Task |

A Use Case must have exactly one Development Task.

A Feature must have exactly one Feature-level Code Review Task.

A Feature may have multiple Use Cases and Supporting Tasks.

### 5.2 Test Case Relationships

Test Cases must be linked directly to Requirements.

They should not be represented as child issues of Requirements because the primary hierarchy is intended to represent planning and implementation decomposition.

Use a native GitHub issue relationship where supported.

The Work Item Manager must maintain and validate the association.

### 5.3 Bug Relationships

Every Bug must be linked to at least one Requirement that it violates.

Where applicable, it must also be linked to the failed Test Case.

A Bug must not be accepted as a valid work item without at least one valid Requirement relationship.

### 5.4 Change Request Relationships

Every Change Request must be linked to at least one existing Requirement that it affects or changes.

The Work Item Manager derives affected Use Cases and Features by following the Requirement's parent relationships.

The Change Request must not require redundant manual links to Use Cases or Features.

### 5.5 Relationship Validation

The Work Item Manager must validate:

- Parent and child Issue Types.
- Required parent relationships.
- Maximum permitted parent relationships.
- Required Requirement associations.
- Required Test Case associations where applicable.
- Missing or invalid references.
- Circular relationships.
- Removed parent or Requirement references.

The Work Item Manager must reject invalid relationships.

### 5.6 Native Relationships and Canonical Associations

GitHub native relationships should be used wherever they represent the required relationship correctly.

For associations such as Requirement-to-Test Case and Requirement-to-Bug, use GitHub's supported issue relationship capabilities.

If a relationship cannot be represented or reliably retrieved through the available GitHub API, the Work Item Manager must maintain a validated association record using the canonical GitHub Issue references.

It must not silently infer relationships from issue titles or arbitrary text.

---

## 6. GitHub Projects Configuration

Phantom Logic will use a central GitHub Project to manage work items.

The Project will provide:

- Work-item visibility.
- State tracking.
- Priority tracking.
- Agent assignment visibility.
- Filtering and grouping.
- Progress reporting.
- Workload visibility.

All relevant Issues should be added to the central Project.

### 6.1 Project Views

The initial Project should include these views:

| View | Purpose |
|---|---|
| All Work Items | Complete view of all work items. |
| Features | Feature-level progress and ownership. |
| Development Board | Development Tasks grouped by State. |
| Requirements | Requirement implementation and QA progress. |
| Bugs | Defect tracking and severity. |
| Change Requests | Requested changes and authorization. |
| Code Reviews | Feature-level review progress. |
| QA Board | Work items currently In Test. |
| Blocked Work | All items in Blocked state. |

Additional views may be introduced when the workflow grows.

### 6.2 Project State Field

The Project's built-in Status field will represent the canonical work-item State.

The values for standard work items are:

- Proposed
- In Work
- In Test
- Resolved
- Blocked
- Removed

The Code Review Task uses:

- Proposed
- In Work
- Review
- Resolved

The Work Item Manager must validate that the selected State is appropriate for the Issue Type.

The GitHub Issue's native open/closed status is not the canonical workflow state.

### 6.3 GitHub Issue Open/Closed Mapping

GitHub Issues have their own open/closed status.

The Work Item Manager will synchronize that status with the canonical State.

| Phantom Logic State | GitHub Issue Status |
|---|---|
| Proposed | Open |
| In Work | Open |
| In Test | Open |
| Blocked | Open |
| Review | Open |
| Resolved | Closed |
| Removed | Closed |

When a Resolved item is reopened to In Work through authorized Change Request or Bug propagation, its GitHub Issue must be reopened.

The Work Item Manager must also ensure that a Removed item cannot be reopened through ordinary workflow operations.

GitHub's native closed status must never be interpreted by itself as proof that a work item is Resolved. A closed issue could also be Removed.

### 6.4 Automatic Project Workflows

GitHub Projects may provide automation for adding items and basic organization.

However, automatic Project workflows must not independently change Phantom Logic's canonical State.

The Work Item Manager remains responsible for all business-rule-driven state transitions.

---

## 7. GitHub Issue Fields and Project Custom Fields

GitHub provides two different mechanisms for storing structured metadata:

1. **GitHub Issue Fields:** Account-level fields that can be used across Issues in repositories owned by the same personal account.
2. **GitHub Projects custom fields:** Fields that belong to an individual Project.

These are separate features and must not be treated as interchangeable.

For Phantom Logic, the preferred approach is to use GitHub Issue Fields for reusable work-item metadata.

This keeps the metadata associated with the Issue itself rather than tying it to one particular Project.

Issue Fields can also be displayed in the central GitHub Project.

### 7.1 Field Design

The initial Issue Field design is:

| Field | Type | Applicable Work Items | Purpose |
|---|---|---|---|
| Priority | Single Select | All applicable items | Work priority. |
| Agent ID | Text | Assigned work items | Identifies the responsible agent. |
| Agent Role | Single Select | Assigned work items | Product Manager, Developer, Reviewer, QA, etc. |
| Review Result | Single Select | Code Review Task | Pending, Changes Requested, Approved. |
| Severity | Single Select | Bug | Critical, High, Medium, Low. |
| Supporting Task Category | Single Select | Supporting Task | Architecture, Design, Security, DevOps, Other. |
| Blocked Reason | Text | Blocked items | Explains the blocker. |
| Return State | Single Select | Blocked items | State to restore when the blocker clears. |

GitHub provides a default Priority Issue Field. Phantom Logic should configure and reuse that field rather than create a duplicate Priority field.

The Project's built-in Status field represents the canonical State and must not be duplicated with a separate custom State field.

### 7.2 Issue Fields Versus Project Custom Fields

The distinction is important:

| Capability | GitHub Issue Fields | Project Custom Fields |
|---|---|---|
| Scope | Personal account or organization | Individual Project |
| Where values belong | On the Issue | On the Project item |
| Reusable across Projects | Yes, for Issues owned by the same account or organization | No, Project-specific |
| Available in Project views | Yes | Yes |
| Appropriate for | Work-item metadata | Project-specific planning information |

Issue Fields are the source of truth for reusable Issue metadata.

Project custom fields should only be introduced when Phantom Logic needs information that genuinely belongs to the Project rather than the Issue.

The same concept must not be represented by two different fields. For example, Phantom Logic must not maintain one Priority Issue Field and a separate Project Priority field.

### 7.3 Project Status Is Not an Issue Field

The Project's built-in Status field remains the canonical work-item State.

It is a Project field and is separate from GitHub Issue Fields.

The Work Item Manager must read and update this Project field when performing authorized state transitions.

No additional Issue Field or Project custom field named State should be created.

### 7.4 Default and Custom Fields

GitHub personal accounts provide default Issue Fields, including:

- Priority
- Effort
- Start date
- Target date

Phantom Logic should review these defaults before creating additional fields.

The initial implementation should avoid unnecessary fields.

The proposed additional fields should only be created where they provide information required by the workflow.

### 7.5 Field Ownership and Enforcement

Fields must not be treated as freely editable metadata when they affect workflow enforcement.

For example:

- State changes must pass through the Work Item Manager.
- Review Result must be updated through the Reviewer workflow.
- Return State must be controlled by the Work Item Manager.
- Severity must be validated for Bugs.
- Supporting Task Category must be validated against permitted values.
- Agent assignment must follow the appropriate authorization rules.

The Work Item Manager must validate field values before accepting them.

GitHub may allow users to edit Issue Fields through the web interface or Project views. Therefore, the Work Item Manager must detect unauthorized changes and either reject, revert, or flag them for authorized reconciliation.

### 7.6 Field Configuration and Limits

Issue Fields are configured at the personal account level under GitHub account settings.

They can be pinned to selected Issue Types so that the relevant fields appear when creating or viewing those Issues.

The initial configuration should:

- Pin Severity to Bug.
- Pin Supporting Task Category to Supporting Task.
- Pin Review Result to Code Review Task.
- Pin Agent ID and Agent Role to the relevant assigned work-item types.
- Make Priority available to applicable work-item types.
- Keep Blocked Reason and Return State available for work items that can enter Blocked.

GitHub supports up to 25 Issue Fields per personal account. Single-select fields support multiple configured options, subject to GitHub's documented limits.

GitHub Projects support up to 50 fields in total. Issue Fields and system fields count toward this Project limit.

The initial design deliberately uses a small field set to avoid unnecessary complexity.

Before configuration, verify the current available limits and permissions for the account and repository.

---

## 8. Labels

Labels will be used for lightweight categorization and filtering, not as the primary work-item classification mechanism.

Suggested labels:

**Area**

- `area:backend`
- `area:frontend`
- `area:database`
- `area:infrastructure`
- `area:security`

**Workflow**

- `workflow:blocked`
- `workflow:needs-attention`

**Scope**

- `scope:approved`
- `scope:change-request`

**Other**

- `documentation`
- `technical-debt`

Labels must not duplicate Issue Types or canonical State values unnecessarily.

---

## 9. GitHub API Integration

The Work Item Manager will communicate with GitHub through a dedicated integration layer.

The integration layer will isolate GitHub API operations from workflow business rules.

### 9.1 GitHub Integration Responsibilities

The integration layer will provide operations to:

- Retrieve Issues.
- Create Issues.
- Update Issue Types.
- Retrieve and update Issue Fields.
- Retrieve Project items.
- Retrieve and update Project field values.
- Retrieve parent/sub-issue relationships.
- Create and remove sub-issue relationships.
- Retrieve issue relationships.
- Retrieve Pull Requests.
- Retrieve commits associated with Pull Requests.
- Retrieve Pull Request reviews and review status.
- Add Issues to Projects.
- Update GitHub Issue open/closed status.
- Retrieve workflow and check-run results.

### 9.2 API Choice

Use the GitHub REST API for operations where the required endpoint is available and straightforward.

Use GraphQL when it provides a more efficient or complete way to retrieve related information, especially when several related objects are needed together.

The integration layer must hide these implementation details from the Work Item Manager.

### 9.3 API Versioning

The integration layer must:

- Use the supported GitHub API version.
- Centralize API version configuration.
- Handle pagination.
- Handle rate limits.
- Handle transient failures.
- Validate API responses.
- Avoid assuming optional fields are always present.
- Log relevant integration failures.

API version changes must be deliberate and tested.

### 9.4 Local Data Model

The Work Item Manager should operate on internal Python domain models rather than raw GitHub API responses.

For example:

```text
GitHub API Response
        |
        v
GitHub Integration
        |
        v
Domain Model
        |
        v
Work Item Manager
```

This separation allows workflow logic to be tested without depending on GitHub API response formats.

---

## 10. GitHub Authentication and Permissions

The integration should use a dedicated GitHub App when practical.

A GitHub App provides controlled access and an identity for automated operations.

However, the authentication approach must be verified against the exact GitHub API operations Phantom Logic needs.

In particular, Phantom Logic uses a personal GitHub account and a user-owned Project. Some account-level Issue Type, Issue Field, and Project API operations may have different authentication and permission requirements from ordinary repository operations.

The implementation must not assume that every required operation is supported by a GitHub App installation token.

### 10.1 Least Privilege

The application must receive only the permissions necessary for its responsibilities.

The following are initial permission categories to investigate:

| Resource | Potential Access | Purpose |
|---|---|---|
| Issues | Read and Write | Create, retrieve, and update work-item Issues. |
| Pull Requests | Read and Write where required | Retrieve PR information and perform permitted PR operations. |
| Contents | Read where required | Read repository content when necessary. |
| Checks | Read and Write where required | Retrieve or publish validation results. |
| Actions | Read where required | Retrieve workflow run information. |
| Metadata | Read | Access repository metadata. |
| Projects | Read and Write where required | Retrieve and update Project items and fields. |
| Issue Types | Read and Write where required | Configure and retrieve account-level Issue Types. |
| Issue Fields | Read and Write where required | Configure and retrieve account-level Issue Fields. |

The table identifies the permission areas that must be evaluated. It is not a declaration that every operation is available through the same GitHub App token.

Exact permissions must be determined from the actual API operations implemented.

Before finalizing authentication, test the following operations using the intended authentication method:

1. Retrieve and create Issues in the public repository.
2. Retrieve and update Issue Types.
3. Retrieve and update Issue Field definitions and values.
4. Retrieve the user-owned central Project.
5. Add Issues to the Project.
6. Retrieve and update Project field values.
7. Retrieve Pull Requests, commits, and reviews.
8. Publish or retrieve required validation checks.

If a required user-owned Project or account-level operation is not supported by the selected GitHub App authentication method, use a supported user-authorized authentication flow or another supported method with the minimum required permissions.

Do not grant broad administrative access merely to avoid resolving an authentication limitation.

### 10.2 Agent Identity

Phantom Logic agents may be logical identities rather than separate GitHub users.

The system must maintain an internal mapping between:

- Agent ID.
- Agent Role.
- GitHub identity or application identity.
- Authorized operations.

A shared GitHub App identity does not, by itself, prove which logical agent initiated an operation.

The Work Item Manager must preserve the actual requesting agent identity in its audit record.

### 10.3 Permission Enforcement

Agent permissions must be enforced by the Work Item Manager.

Examples:

- Product Manager authorizes work.
- Developer implements work.
- Reviewer approves code review.
- QA verifies work.
- Orchestrator coordinates work.

A GitHub API token or GitHub App permission does not replace these business-level permissions.

---

## 11. Webhooks and Event Processing

GitHub webhooks will notify the integration system when relevant GitHub events occur.

Potential events include:

- Issues opened, edited, labeled, assigned, or closed.
- Issue type changes.
- Project item changes.
- Issue field changes.
- Pull Request opened, edited, synchronized, or closed.
- Pull Request review submitted.
- Check runs completed.
- Push events.
- Workflow runs completed.

### 11.1 Event Processing

Webhook processing must follow this pattern:

```text
GitHub Event
     |
     v
Webhook Receiver
     |
     v
Validate Signature
     |
     v
Validate Event
     |
     v
Deduplicate Event
     |
     v
Retrieve Current GitHub Data
     |
     v
Work Item Manager
     |
     v
Apply Authorized Operation
     |
     v
Audit
```

### 11.2 Event Reliability

Webhook processing must be:

- Idempotent.
- Safe to retry.
- Resistant to duplicate delivery.
- Resistant to out-of-order events.
- Auditable.

The Work Item Manager must retrieve current authoritative data before applying important transitions.

A webhook payload alone must not be treated as sufficient evidence for a state transition.

### 11.3 Direct GitHub Changes

Users and agents may sometimes edit Issues or Project fields directly through the GitHub interface.

For controlled fields, the Work Item Manager must detect unauthorized changes and either:

- Reject or revert the change, or
- Flag it for authorized reconciliation.

The selected behavior must be consistent and audited.

The preferred approach is to prevent unauthorized changes where GitHub permissions allow it and enforce the remaining restrictions through automation.

---

## 12. Change Request and Bug Enforcement

The Work Item Manager will implement the propagation rules defined in `StateTransitionMatrix.md`.

### 12.1 Change Request

When a Change Request is Proposed:

- No affected hierarchy changes state.

When the Product Manager authorizes it:

- Change Request → In Work.
- Linked Requirements → In Work.
- Corresponding Use Cases → In Work.
- Corresponding Features → In Work.

The Work Item Manager must derive parent relationships and deduplicate parent transitions.

### 12.2 Bug

Every Bug must reference at least one Requirement.

When QA creates a Bug:

- Bug remains Proposed.
- Linked hierarchy remains unchanged.

When the Product Manager authorizes it:

- Bug → In Work.
- Linked Requirements → In Work.
- Corresponding Use Cases → In Work.
- Corresponding Features → In Work.

### 12.3 Multiple Active Change Requests and Bugs

The Work Item Manager must maintain an accurate view of outstanding Change Requests and Bugs affecting each Requirement.

Resolving one item must not automatically resolve the Requirement if another relevant item remains outstanding.

### 12.4 Removed Requirements

If a Change Request or Bug references a Removed Requirement, the operation must be rejected until explicit reinstatement is authorized.

### 12.5 Blocked Items

If an authorized Change Request or Bug affects a Blocked item:

- Preserve the Blocked state.
- Update its Return State to In Work.
- Record the originating work item.
- Restore In Work when the blocker clears.

---

## 13. Pull Request Integration

Pull Requests are the mechanism for promoting changes from `dev` to `main`.

### 13.1 Pull Request Requirements

Every Pull Request must include:

- Relevant Development Task references.
- Relevant Feature references.
- Summary of changes.
- Testing evidence.
- Relevant Change Set or commit references.
- Any necessary implementation notes.

The Work Item Manager must validate the associations.

### 13.2 Multiple Features in One Pull Request

A Pull Request may contain changes for multiple Features.

In that case, the Work Item Manager must identify every affected Feature.

Every affected Feature-level Code Review Task must be Resolved before the Pull Request can merge.

### 13.3 Code Review Approval

The Feature-level Code Review Task is the authoritative Phantom Logic review record.

The Reviewer must:

- Review the relevant commits.
- Record findings.
- Record the review result.
- Resolve the Code Review Task only after approval.

The Pull Request must contain or link to sufficient review evidence for the Work Item Manager to validate the approval.

### 13.4 Review Approval Invalidation

If new material commits are added after approval:

- Approval for the affected review scope is invalidated.
- The relevant Code Review Task must return to an appropriate unresolved state.
- The Reviewer must examine the new changes.
- The merge gate must reject the Pull Request until renewed approval is recorded.

The Work Item Manager must verify that the approval applies to the exact commit or Pull Request revision being merged.

### 13.5 No Automatic Issue Resolution

Pull Requests must not use automatic closing references such as `Closes #123` for work items whose resolution is governed by Phantom Logic's workflow.

A Pull Request merge does not automatically mean that a Requirement, Development Task, Use Case, or Feature is Resolved.

The Work Item Manager controls these transitions.

---

## 14. Main Branch Protection

The `main` branch must be protected.

The preferred implementation is a GitHub repository ruleset targeting `main`.

The ruleset should require:

- Pull Requests before merging.
- Required status checks.
- Successful CI checks.
- Successful Work Item Manager validation.
- Successful Feature-level code-review validation.
- Required security checks where configured.
- No force pushes.
- No deletion of the protected branch.

Administrative bypass must be minimized.

### 14.1 Work Item Validation Check

A GitHub Actions check must validate:

1. Pull Request work-item references.
2. Associated Development Tasks.
3. Associated Features.
4. Required Feature-level Code Review Tasks.
5. Review approval validity.
6. Required CI and security checks.
7. Any other applicable merge conditions.

The check must fail if required evidence is missing or invalid.

### 14.2 Reviewer Separation

The system must ensure that the Developer responsible for the changes cannot satisfy the required independent Reviewer approval.

This must be enforced by the Work Item Manager and the repository's review policy.

### 14.3 Required Status Check Source

Where supported, configure the required status check to accept results from the expected GitHub App or trusted integration.

This reduces the risk of an unrelated integration or user setting a misleading status.

### 14.4 Enforcement Limitation

A GitHub ruleset protects the branch, but the Work Item Manager supplies Phantom Logic-specific business validation.

Neither mechanism should be treated as a substitute for the other.

Repository plan availability and ruleset capabilities must be verified before implementation.

---

## 15. CI, QA, and Deployment Integration

The development and release flow is:

```text
Developer
   |
   v
Shared dev Branch
   |
   v
Pull Request
   |
   v
Code Review + CI + Security Checks
   |
   v
Work Item Manager Validation
   |
   v
Merge to main
   |
   v
Build from main
   |
   v
QA Verification
   |
   v
Staging
   |
   v
Production
```

### 15.1 Development Branch

Developers commit to the shared `dev` branch.

The Work Item Manager must maintain traceability between commits, Change Sets, and Development Tasks.

### 15.2 Pull Request Validation

Before merge, required checks must pass.

### 15.3 Main Build

QA must test only builds generated from `main`.

A build from `dev` is not an accepted QA build.

### 15.4 QA Results

QA results must be recorded against the relevant work items and Test Cases.

A failed QA result must not resolve the corresponding work item.

### 15.5 Deployment Environments

Staging and Production are deployment environments, not permanent Git branches.

Deployment success and release readiness must be recorded separately from the work-item State.

---

## 16. Work Item Manager Python Architecture

The Work Item Manager must be implemented as a deterministic Python component.

The proposed structure is:

```text
PhantomLogic/
└── WorkItems/
    ├── Models/
    │   ├── WorkItem.py
    │   ├── WorkItemType.py
    │   ├── WorkItemState.py
    │   ├── WorkItemRelationship.py
    │   └── TransitionResult.py
    │
    ├── Rules/
    │   ├── StateTransitionRules.py
    │   ├── RelationshipRules.py
    │   ├── HierarchyRules.py
    │   ├── PermissionRules.py
    │   ├── ChangeRequestRules.py
    │   ├── BugRules.py
    │   └── ResolutionRules.py
    │
    ├── GitHub/
    │   ├── GitHubClient.py
    │   ├── GitHubIssueRepository.py
    │   ├── GitHubProjectRepository.py
    │   ├── GitHubPullRequestRepository.py
    │   └── GitHubWebhookHandler.py
    │
    ├── Manager/
    │   ├── WorkItemManager.py
    │   ├── WorkItemValidator.py
    │   ├── StateTransitionManager.py
    │   └── HierarchyManager.py
    │
    └── Tests/
        ├── Models/
        ├── Rules/
        ├── Manager/
        ├── GitHub/
        └── Integration/
```

This is the proposed logical organization. Files should be introduced incrementally as implementation progresses.

### 16.1 Models

Models represent the internal work-item domain.

They must not depend directly on GitHub API response structures.

### 16.2 Rules

Rules contain deterministic business logic.

They must be testable without GitHub connectivity.

### 16.3 GitHub Integration

The GitHub layer handles external API communication.

It translates GitHub data into domain models and translates authorized domain operations into GitHub API calls.

### 16.4 Manager

The Manager coordinates validation, transitions, hierarchy propagation, and integration operations.

### 16.5 Tests

Tests must cover both valid and invalid operations.

The core rules must be tested independently before integration with GitHub.

---

## 17. Audit Integration

The Work Item Manager must integrate with the central Phantom Logic Audit system.

It must not write directly to the audit log.

All audit entries must be submitted through the existing Audit Writer mechanism.

### 17.1 Mandatory Audit Events

At minimum, record:

- Work Item creation.
- Work Item relationship changes.
- State transitions.
- Authorization decisions.
- Change Request propagation.
- Bug propagation.
- Blocked state changes.
- Removed-item operations.
- Reinstatement operations.
- Code Review approval.
- Review approval invalidation.
- Pull Request validation decisions.
- Merge-gate failures.
- Reconciliation of unauthorized GitHub changes.

### 17.2 Audit Context

Audit records must identify:

- Work Item ID.
- Work Item Type.
- Previous and new values where applicable.
- Initiating agent.
- Responsible system component.
- Timestamp.
- Reason.
- Related work items.
- Related Pull Requests or commits where applicable.

The originating operation must be traceable across automated propagation.

---

## 18. Security and Reliability

The implementation must follow secure integration practices.

### 18.1 Secrets

- Never store GitHub credentials in source code.
- Use approved secret-management mechanisms.
- Avoid exposing tokens in logs.
- Rotate credentials when required.

### 18.2 API Reliability

- Handle rate limits.
- Use retry policies for transient failures.
- Avoid duplicate operations.
- Handle pagination.
- Validate responses.
- Fail safely when authoritative data cannot be retrieved.

### 18.3 Webhook Security

- Validate webhook signatures.
- Reject invalid requests.
- Deduplicate event delivery.
- Avoid trusting unverified payload content.
- Log relevant processing failures.

### 18.4 Fail-Closed Behavior

If the Work Item Manager cannot verify a required merge condition, the Pull Request must not be approved for merge.

Missing information must not be treated as successful validation.

---

## 19. Implementation Phases

Implementation will proceed incrementally.

### Phase 1 — GitHub Configuration

Configure:

- Issue Types.
- Issue Fields.
- Issue Field visibility and pinning.
- Labels.
- Central GitHub Project.
- Project views.
- Parent/sub-issue relationships.

Verify the availability of the required personal-account Project and Issue Field operations before deciding the final authentication method.

No custom Python integration is required for this phase.

### Phase 2 — Domain Models

Implement:

- Work Item models.
- Work Item Types.
- State definitions.
- Relationship models.
- Transition results.

Add unit tests.

### Phase 3 — Business Rules

Implement:

- State transition validation.
- Permission validation.
- Hierarchy validation.
- Change Request propagation.
- Bug propagation.
- Blocked return-state handling.
- Parent resolution eligibility.

Test all rules independently.

### Phase 4 — GitHub Integration

Implement the GitHub client and repositories.

Use mocked API responses for automated tests.

Verify that GitHub operations correctly map to the internal domain models.

### Phase 5 — Work Item Manager

Implement the orchestration of domain rules and GitHub operations.

Integrate the existing Audit Writer.

### Phase 6 — GitHub Actions Integration

Implement:

- Work-item validation checks.
- Pull Request validation.
- Code-review gate validation.
- CI and security check integration.
- Webhook processing.

### Phase 7 — Agent Integration

Connect the Orchestrator, Product Manager, Developer, Reviewer, and QA agents to the Work Item Manager.

Agents must request permitted operations through the Manager rather than changing controlled fields independently.

### Phase 8 — End-to-End Testing

Test complete workflows:

- Feature creation.
- Requirement authorization.
- Development Task implementation.
- Multiple Change Sets and commits.
- Feature-level code review.
- Pull Request validation.
- Merge into main.
- QA verification.
- Bug creation and authorization.
- Resolved Requirement reopening.
- Multiple active Bugs.
- Change Request propagation.
- Blocked and Removed item handling.
- Parent resolution.

Only after these tests pass should the workflow be used for actual autonomous development.

---

## 20. Design Decisions and Constraints

The following decisions are established for the initial implementation:

1. GitHub Issues represent work items.
2. GitHub Issue Types distinguish work-item categories.
3. GitHub Issue Fields store reusable structured work-item metadata.
4. GitHub native parent/sub-issue relationships represent the primary hierarchy.
5. GitHub issue relationships represent associations between related work items where supported.
6. GitHub Projects provide centralized tracking and reporting.
7. The Project Status field represents the canonical work-item State.
8. GitHub's native open/closed status is synchronized with, but does not replace, the canonical State.
9. The Python Work Item Manager is the authority for workflow rules.
10. GitHub Actions execute automated validation and enforcement.
11. Repository rulesets protect `main`.
12. Developers use the shared `dev` branch.
13. Changes reach `main` only through Pull Requests.
14. QA tests only builds generated from `main`.
15. Every Feature has one Feature-level Code Review Task.
16. The Reviewer is separate from the Developer.
17. Every Change Request and Bug must reference at least one Requirement.
18. The Work Item Manager derives affected Use Cases and Features from Requirement relationships.
19. Every significant operation is auditable through the central Audit Writer.
20. Business rules must be testable independently of GitHub.
21. The implementation must fail safely when required validation cannot be completed.
22. Account-level Issue Fields are preferred for reusable Issue metadata; Project custom fields are reserved for Project-specific information.
23. The authentication method must be validated against the actual API operations required for the personal-account repository and Project.

---

## 21. Repository Visibility and GitHub Plan Assumption

**Decision:** Phantom Logic's primary GitHub repository will remain public during the initial development and implementation of the autonomous company platform.

The GitHub Work Item Management architecture must be designed to work with GitHub Free capabilities for public repositories wherever practical.

### 21.1 Design Implications

1. Use GitHub Issues and custom Issue Types to represent Phantom Logic work items.
2. Use GitHub Issue Fields for reusable structured metadata.
3. Use GitHub Projects for centralized work-item tracking and reporting.
4. Use native parent/sub-issue relationships for the primary work-item hierarchy.
5. Use Pull Requests for promoting changes from `dev` to `main`.
6. Use GitHub Actions for CI, workflow validation, and enforcement checks.
7. Use repository rulesets to protect `main`, require pull requests and required status checks, and prevent force pushes and branch deletion.
8. Use the Python Work Item Manager as the authority for Phantom Logic workflow rules. GitHub's native features support and enforce those rules but do not replace the Work Item Manager.
9. Configure reusable Issue Fields at the personal account level and make them available to the public Project where required.

### 21.2 Public Issue Field Visibility

GitHub Issue Fields have visibility settings.

For Issue Fields that must appear in the public Phantom Logic Project, their visibility must be set to **Public**.

Restricted Issue Fields are not displayed in public Projects.

The default visibility for Issue Fields is Restricted, so this setting must be checked during configuration.

The Work Item Manager must not store confidential information in public Issue Fields.

### 21.3 Security Requirements

- Never commit credentials, API tokens, passwords, private keys, or other secrets.
- Use GitHub Actions Secrets or an appropriate secure credential store for sensitive configuration.
- Do not place private customer data, confidential business information, or sensitive operational information in public Issues, Pull Requests, logs, or repository files.
- Restrict repository write and administrative permissions to authorized users.
- Review GitHub Actions permissions and third-party dependencies before granting access to repository contents or secrets.
- Do not assume that making an Issue Field Restricted makes the underlying public Issue or its other contents private.
- Keep sensitive operational information outside the public repository and public Project.

### 21.4 Future Flexibility

The architecture must avoid unnecessary dependencies on paid GitHub features.

If Phantom Logic later requires private source code, advanced security capabilities, or additional organizational controls, repository visibility and the GitHub plan can be reconsidered without redesigning the Work Item Manager's core business rules.

---

## 22. Official GitHub References

The implementation should follow current GitHub documentation.

- [Issue Types and Fields for Personal Accounts](https://github.blog/changelog/2026-11-11-issue-types-and-fields-are-available-for-personal-accounts/)
- [Managing GitHub Issue Fields](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields)
- [Adding and Managing Issue Fields](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-and-managing-issue-fields)
- [About Issue Fields in Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields)
- [GitHub REST API: Sub-Issues](https://docs.github.com/en/rest/issues/sub-issues)
- [Parent Issue and Sub-Issue Progress Fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields)
- [GitHub App Permissions](https://docs.github.com/en/apps/creating-github-apps/setting-up-a-github-app/choosing-permissions-for-a-github-app)
- [GitHub Rulesets: Available Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [Creating Repository Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)

GitHub capabilities, API behavior, authentication support, and plan availability must be rechecked when the corresponding implementation phase begins.

---

**End of Document**