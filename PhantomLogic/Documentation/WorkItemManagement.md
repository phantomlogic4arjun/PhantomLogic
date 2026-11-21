# Work Item Management

**Project:** Phantom Logic  
**Document Status:** Initial Design  
**Version:** 3.0  
**Last Updated:** 21 November 2026

---

## 1. Purpose

This document defines how Phantom Logic manages software development work through structured work items.

The Work Item Management system provides a centralized, auditable mechanism for:

- Defining and organizing development work.
- Managing relationships between Features, Use Cases, Requirements, and implementation Tasks.
- Tracking Change Requests and Bugs.
- Controlling work authorization and state transitions.
- Tracking Development Tasks, Change Sets, and Git commits.
- Managing independent code reviews.
- Coordinating development, QA, and release workflows.
- Enforcing completion criteria before work items can be resolved.
- Integrating work item activities with the central audit system.

The objective is to make work management deterministic, consistent, and enforceable rather than relying on individual agents to interpret processes independently.

The Work Item Manager will be implemented as a deterministic Python component. AI agents will interact with it through defined operations rather than directly modifying work item records.

## 2. Architectural Principles

The following principles guide the design.

### 2.1 Deterministic Work Management

The Work Item Manager is responsible for enforcing:

- Valid work item types and relationships.
- Permitted state transitions.
- Work authorization.
- Parent-child state dependencies.
- Change Request and Bug relationship propagation.
- Development Task and Change Set associations.
- Code review requirements.
- Completion criteria.
- Agent permissions.

Agents may recommend actions, but the Work Item Manager validates and executes permitted changes.

### 2.2 Separation of Responsibilities

Different agents have different responsibilities.

- Product Manager determines what work is authorized.
- Architect, Designer, Security, and DevOps provide specialist input.
- Developer implements approved work.
- Reviewer independently reviews code changes.
- QA verifies implementation against requirements.
- Orchestrator coordinates the overall workflow.

No agent should be able to bypass the Work Item Manager's rules.

### 2.3 Explicit Relationships

Work items must have clearly defined relationships.

The system should derive relationships wherever possible instead of storing redundant information.

For example, a Change Request linked to a Requirement does not need separate manually maintained links to its parent Use Case and Feature. The Work Item Manager can determine those relationships automatically.

### 2.4 Auditability

Important work item activities must be recorded through the central audit mechanism.

This includes:

- Creation and modification of work items.
- Work authorization.
- State transitions.
- Relationship changes.
- Development Task and Change Set associations.
- Code review decisions.
- QA results.
- Blocked and reopened work.
- Resolution and removal.

## 3. Work Item Types and Hierarchy

The system supports the following work item types.

### 3.1 Epic

An Epic represents a large business or product objective.

An Epic may contain multiple Features.

Epics are optional. Not every project needs them.

### 3.2 Feature

A Feature represents a significant product capability or functional area.

A Feature contains:

- One or more Use Cases.
- One or more Feature-level supporting Tasks, where applicable.
- Exactly one Feature-level Code Review Task.

A Feature is the primary unit for organizing and reviewing a functional area of development.

A Feature can be associated with an Epic.

### 3.3 Use Case

A Use Case describes a specific user interaction, workflow, or functional scenario within a Feature.

Each Use Case belongs to exactly one Feature.

Each Use Case has:

- One Development Task.
- One or more Requirements.

### 3.4 Requirement

A Requirement describes a specific expected behavior, business rule, or system capability.

Each Requirement belongs to exactly one Use Case.

Requirements are the basis for implementation and QA verification.

A Requirement should be sufficiently clear and testable.

### 3.5 Development Task

A Development Task represents the implementation work associated with a Use Case.

Each Use Case has one Development Task.

A Development Task may contain multiple Change Sets.

Each Change Set may contain multiple Git commits.

A Development Task is not resolved by the Developer. It must go through QA verification.

### 3.6 Supporting Tasks

Supporting Tasks represent work that supports a Feature but is not the primary implementation of a Use Case.

Examples include:

- Architecture Task.
- Design Task.
- Security Task.
- DevOps Task.
- Infrastructure Task.
- Documentation Task.

Supporting Tasks are linked directly to the relevant Feature.

They may be assigned to the appropriate specialist agent.

### 3.7 Code Review Task

Each Feature has exactly one Code Review Task.

The Code Review Task covers the code changes associated with that Feature, including multiple Development Tasks, Change Sets, commits, and Pull Requests.

A Feature-level Code Review Task is owned by the Reviewer agent.

Code Review Tasks have their own lifecycle, defined in Section 5.

Code review is independent of QA testing.

### 3.8 Test Case

A Test Case defines a specific verification scenario for a Requirement.

Test Cases are linked directly to Requirements.

A Requirement may have multiple Test Cases.

Test Cases are executed by the QA agent.

### 3.9 Bug

A Bug represents a defect where the actual system behavior violates an existing Requirement.

Every Bug must be linked to at least one Requirement that it violates.

A Bug may also be linked to one or more failed Test Cases.

A Bug may affect multiple Requirements, Use Cases, or Features.

The Work Item Manager determines the corresponding Use Cases and Features through the linked Requirements.

### 3.10 Change Request

A Change Request represents a proposed modification to existing product behavior, functionality, or requirements.

Every Change Request must be linked to at least one existing Requirement that is being changed or affected.

A Change Request may affect multiple Requirements, Use Cases, or Features.

The Work Item Manager determines the corresponding Use Cases and Features through the linked Requirements.

A Change Request may result in changes to existing implementation or additional implementation work.

### 3.11 Other Work Item Types

The system may also support:

- Change Sets.
- Release Tasks.
- Deployment Tasks.
- Maintenance Tasks.

These may be introduced as the implementation evolves.

## 4. Work Item Relationships

### 4.1 Primary Hierarchy

The primary work item hierarchy is:

```text
Epic
  └── Feature
        ├── Use Case
        │     ├── Development Task
        │     └── Requirement
        │           └── Test Cases
        │
        ├── Supporting Tasks
        │
        └── Code Review Task
```

An Epic is optional.

A Feature can exist without an Epic.

A Feature must contain at least one Use Case before it can be considered complete.

### 4.2 Change Request Relationships

A Change Request must be linked to one or more Requirements.

```text
Change Request
  ├── Requirement R1
  └── Requirement R2
```

The Work Item Manager follows the Requirement relationships to determine the affected Use Cases and Features.

The relationship is derived as follows:

```text
Change Request
  └── Requirements
        └── Use Cases
              └── Features
```

The system should not require agents to manually create redundant links from a Change Request to its Use Cases and Features.

### 4.3 Bug Relationships

A Bug must be linked to one or more Requirements that it violates.

```text
Bug
  ├── Requirement R1
  └── Requirement R2
```

A Bug may additionally be linked to failed Test Cases.

The Work Item Manager determines the affected Use Cases and Features by following the linked Requirements.

### 4.4 Relationship Validation

The Work Item Manager must validate relationships when work items are created or modified.

Examples:

- A Requirement must belong to a Use Case.
- A Use Case must belong to a Feature.
- A Development Task must belong to a Use Case.
- A Code Review Task must belong to a Feature.
- A Test Case must belong to a Requirement.
- A Change Request must link to at least one Requirement.
- A Bug must link to at least one Requirement.
- A Change Set must belong to a Development Task.

Invalid or incomplete relationships must be rejected.

The system must prevent circular or inconsistent relationships.

## 5. Work Item States

### 5.1 Standard Work Item States

The standard lifecycle is:

1. Proposed
2. In Work
3. In Test
4. Resolved

Two exceptional states are also supported:

- Blocked
- Removed

### 5.2 State Definitions

**Proposed**

The work item has been identified and documented but has not yet been authorized for implementation.

**In Work**

The work item has been authorized and work is actively being performed.

**In Test**

Implementation is complete and the work item is awaiting or undergoing QA verification.

**Resolved**

The work item has satisfied its completion criteria and the required verification has passed.

**Blocked**

Work cannot proceed because of a dependency, decision, technical issue, or other impediment.

The system must preserve the state that existed before the item became Blocked.

When the blocker is cleared, the item returns to its previous state unless an authorized decision determines otherwise.

**Removed**

The work item is no longer required or will not be implemented.

Removal requires authorization and a recorded reason.

### 5.3 Code Review Task States

Code Review Tasks have a separate lifecycle:

1. Proposed
2. In Work
3. Review
4. Resolved

Definitions:

**Proposed:** The Code Review Task has been created but review has not started.

**In Work:** The Reviewer is performing the code review.

**Review:** The review findings and requested changes are being addressed or the review is awaiting a final decision.

**Resolved:** The review has been approved and all required findings have been addressed.

Code Review Tasks do not use the standard In Test state.

### 5.4 Review Result

The Code Review Task also has a separate Review Result field:

- Pending
- Changes Requested
- Approved

The Review Result is not a work item state.

For example, a Code Review Task may be in the Review state with a Review Result of Changes Requested.

The Code Review Task can only become Resolved when its Review Result is Approved.

The Developer cannot approve or resolve their own Feature-level Code Review Task.

## 6. Work Item Fields

The common fields for work items include:

| Field | Description |
|---|---|
| ID | Unique identifier |
| Title | Short description |
| Description | Detailed explanation |
| Work Item Type | Feature, Use Case, Requirement, Bug, etc. |
| State | Current lifecycle state |
| Priority | Relative importance |
| Assigned Agent | Responsible agent |
| Created By | Agent that created the item |
| Created Date | Creation timestamp |
| Updated Date | Last modification timestamp |
| Parent ID | Parent work item, where applicable |
| Related Items | Explicit relationships to other work items |
| Acceptance Criteria | Conditions for completion |
| Block Reason | Explanation when Blocked |
| Resolution Reason | Explanation when Resolved |
| Removal Reason | Explanation when Removed |
| Audit Reference | Reference to relevant audit events |

Additional fields may be defined for specific work item types.

### 6.1 Change Request Fields

In addition to common fields:

- Change Request Reason.
- Business Justification.
- Impact Description.
- Linked Requirements.
- Approval Decision.
- Implementation Notes.

### 6.2 Bug Fields

In addition to common fields:

- Bug Description.
- Expected Behavior.
- Actual Behavior.
- Reproduction Steps.
- Severity.
- Priority.
- Environment.
- Linked Requirements.
- Linked Failed Test Cases.
- Root Cause, when identified.
- Fix Description.

### 6.3 Development Task Fields

In addition to common fields:

- Linked Use Case.
- Change Sets.
- Implementation Summary.
- Development Completion Notes.
- Associated Pull Requests.

### 6.4 Change Set Fields

A Change Set represents a logical grouping of code changes made for a Development Task.

Fields include:

- Change Set ID.
- Development Task ID.
- Description.
- Git Branch.
- Commit References.
- Pull Request References, where applicable.
- Created By.
- Created Date.

A Change Set can contain multiple commits.

A Development Task can contain multiple Change Sets.

### 6.5 Code Review Task Fields

In addition to common fields:

- Feature ID.
- Reviewer Agent.
- Review Result.
- Reviewed Change Sets.
- Reviewed Commits.
- Pull Request References.
- Review Findings.
- Required Corrections.
- Approval Details.

## 7. Agent Responsibilities

### 7.1 Orchestrator

The Orchestrator coordinates the overall development workflow.

Responsibilities:

- Coordinate agents.
- Assign work to appropriate agents.
- Monitor dependencies and progress.
- Identify blockers.
- Ensure required workflow gates are satisfied.
- Coordinate Feature-level completion.
- Monitor audit events.

The Orchestrator does not routinely manage individual work item state transitions.

It should not be responsible for moving every work item from Proposed to In Work.

### 7.2 Product Manager

The Product Manager controls work authorization.

Responsibilities:

- Create and refine Features.
- Define Use Cases and Requirements.
- Create Change Requests and Bugs where appropriate.
- Review and prioritize work.
- Authorize work to begin.
- Move approved work items from Proposed to In Work.
- Ensure Change Requests and Bugs have valid Requirement relationships.
- Review scope changes.

The Product Manager is responsible for authorizing implementation work.

### 7.3 Architect

Responsibilities:

- Review architectural implications.
- Define technical architecture.
- Identify technical dependencies.
- Create Architecture Tasks when required.
- Provide architectural guidance.

### 7.4 Designer

Responsibilities:

- Define user experience and interface requirements.
- Create design specifications.
- Review design implementation.
- Create Design Tasks when required.

### 7.5 Developer

Responsibilities:

- Implement approved Development Tasks.
- Create and maintain Change Sets.
- Associate Git commits with the appropriate Change Sets.
- Follow Coding Standards.
- Address Reviewer findings.
- Address Bugs assigned for implementation.
- Move completed Development Tasks to In Test.

The Developer cannot:

- Authorize their own work.
- Resolve Development Tasks.
- Approve their own Code Review Tasks.
- Bypass required code review or QA gates.
- Push directly to main.

### 7.6 Reviewer

The Reviewer acts as an independent Senior Developer.

Responsibilities:

- Review Feature-level code changes.
- Review associated Change Sets, commits, and Pull Requests.
- Evaluate coding standards and engineering practices.
- Identify maintainability and design issues.
- Request corrections where necessary.
- Approve code changes when review criteria are satisfied.
- Resolve the Feature-level Code Review Task after approval.

The Reviewer focuses on:

- Coding standards.
- Naming conventions.
- Readability.
- Maintainability.
- Separation of concerns.
- Duplication.
- Consistency with project conventions.
- Appropriate error handling.
- Security-related coding practices.
- General engineering quality.

The Reviewer is not a replacement for QA.

The Reviewer should use the established Coding Standards and Code Review Guidelines rather than personal preferences.

The Developer and Reviewer must be different agents for a given review.

### 7.7 QA

Responsibilities:

- Execute Test Cases.
- Verify Requirements.
- Validate Use Cases.
- Verify Development Tasks.
- Verify Features.
- Record test results.
- Create Bugs when actual behavior violates Requirements.
- Re-test fixes after they are promoted to main.
- Resolve work items when their completion criteria are satisfied.

QA only tests builds generated from main.

QA must not resolve a failed Test Case.

QA must not resolve a Requirement, Use Case, or Feature without satisfying the applicable completion criteria.

### 7.8 Security

Responsibilities:

- Review security implications.
- Perform security assessments.
- Identify vulnerabilities.
- Create Security Tasks when required.
- Verify security-related completion criteria.

### 7.9 DevOps

Responsibilities:

- Manage build and deployment pipelines.
- Configure CI/CD.
- Manage environments.
- Maintain deployment processes.
- Support release and infrastructure requirements.

## 8. State Transition Governance

### 8.1 General Transition Rules

The Work Item Manager validates all state transitions.

The following transitions are generally supported for standard work items:

| Current State | Next State | Authority |
|---|---|---|
| Proposed | In Work | Product Manager |
| In Work | In Test | Developer, for completed implementation Tasks |
| In Test | Resolved | QA, after successful verification |
| Any active state | Blocked | Authorized agent, with reason |
| Blocked | Previous State | Work Item Manager, after blocker clearance |
| Proposed | Removed | Product Manager, with reason |
| Other permitted states | Removed | Authorized approval, with reason |

The Work Item Manager must enforce additional item-specific rules described in this document.

A state transition is not automatically permitted simply because it appears in the table.

### 8.2 Work Authorization

The Product Manager authorizes work.

When work is approved:

- The relevant Feature can move from Proposed to In Work.
- The relevant Use Cases can move from Proposed to In Work.
- The relevant Requirements can move from Proposed to In Work.
- Associated implementation Tasks can move from Proposed to In Work.

The Work Item Manager validates that the authorization exists before making these transitions.

The Orchestrator does not need to manually move every item into In Work.

### 8.3 Development Task Completion

When implementation is complete:

- The Developer records the implementation summary.
- The Developer ensures the Change Sets and commits are associated with the Development Task.
- The Developer moves the Development Task to In Test.

The Developer cannot resolve the Development Task.

QA must verify the implementation before resolution.

### 8.4 Resolution Authority

QA is responsible for verifying and resolving Requirements, Test Cases, Development Tasks, Use Cases, and Features, subject to the completion rules in Section 9.

The Work Item Manager enforces the required conditions.

The Work Item Manager does not independently determine that functionality works correctly. That determination belongs to QA.

The Reviewer is responsible for resolving Code Review Tasks after approval.

## 9. Hierarchical Completion and Resolution Rules

Resolution follows a bottom-up process.

A parent work item cannot be resolved while its required child work items remain unresolved.

### 9.1 Requirement Resolution

A Requirement can be Resolved only when:

- Its implementation is complete.
- Its associated Development Task has passed QA verification.
- All mandatory Test Cases linked to the Requirement have Passed.
- No outstanding release-blocking Bug violates the Requirement.
- Any other applicable acceptance criteria have been satisfied.

A Requirement cannot be resolved simply because its Development Task is marked In Test.

### 9.2 Use Case Resolution

A Use Case can be Resolved only when:

- All Requirements belonging to the Use Case are Resolved.
- Its Development Task is Resolved.
- Any applicable acceptance criteria have been satisfied.

The Work Item Manager must check every Requirement belonging to the Use Case.

If even one Requirement remains unresolved, the Use Case cannot be Resolved.

### 9.3 Feature Resolution

A Feature can be Resolved only when:

- All Use Cases belonging to the Feature are Resolved.
- All Feature-level supporting Tasks are Resolved, where applicable.
- The Feature-level Code Review Task is Resolved.
- Required security gates are complete.
- Required CI checks have passed.
- There are no unresolved release-blocking Bugs affecting the Feature.
- All other Feature-level acceptance criteria are satisfied.

The Work Item Manager must evaluate these conditions before allowing the Feature to become Resolved.

If even one Use Case remains unresolved, the Feature cannot be Resolved.

### 9.4 Code Review and QA Are Separate Gates

Code review approval does not mean the Feature is ready to be Resolved.

Similarly, successful QA verification does not eliminate the requirement for code review.

Both gates must be satisfied.

### 9.5 Automatic Parent Completion Evaluation

When a child work item becomes Resolved, the Work Item Manager may evaluate its parent.

For example:

1. A Requirement becomes Resolved.
2. The Work Item Manager checks whether all Requirements under its Use Case are Resolved.
3. If all are Resolved, it checks whether the Use Case's other completion criteria are satisfied.
4. If satisfied and QA verification is recorded, the Use Case may be resolved.
5. The Work Item Manager then checks whether all Use Cases under the Feature are Resolved.
6. It also checks the Feature-level Code Review Task and other Feature completion gates.
7. The Feature may be resolved only after all conditions are satisfied.

The Work Item Manager performs the eligibility checks and enforces the result.

QA remains responsible for confirming successful verification.

The system must not resolve parent work items merely because a child changed state.

## 10. Change Request and Bug Management

### 10.1 Change Request Definition

A Change Request represents a requested change to existing product behavior or requirements.

Every Change Request must be linked to at least one Requirement.

The linked Requirements identify what existing functionality or expected behavior is being changed.

A Change Request can affect:

- One Requirement.
- Multiple Requirements within one Use Case.
- Requirements across multiple Use Cases.
- Requirements across multiple Features.

### 10.2 Bug Definition

A Bug represents a defect where actual system behavior violates an existing Requirement.

Every Bug must be linked to at least one Requirement that it violates.

A Bug may also be associated with:

- One or more failed Test Cases.
- Relevant Development Tasks.
- Relevant Change Sets or commits, where known.

A Bug must not be treated as a general task without an identified Requirement violation.

If the expected behavior is unclear or no Requirement exists, the Product Manager must first clarify the expected behavior and establish the appropriate Requirement relationship.

### 10.3 Automatic Relationship Discovery

The Work Item Manager is responsible for determining the affected Use Cases and Features for Change Requests and Bugs.

It does this by following the existing Requirement relationships.

Example:

```text
Feature A
  ├── Use Case A1
  │     ├── Requirement R1
  │     └── Requirement R2
  │
  └── Use Case A2
        └── Requirement R3

Feature B
  └── Use Case B1
        └── Requirement R4

Change Request CR-001
  ├── Requirement R1
  └── Requirement R4
```

The Work Item Manager determines:

- Affected Requirements: R1 and R4.
- Affected Use Cases: A1 and B1.
- Affected Features: Feature A and Feature B.

The same mechanism applies to Bugs.

Agents do not need to manually link the corresponding Use Cases and Features.

The Work Item Manager should derive these relationships dynamically from the Requirements.

### 10.4 State Propagation When Work Begins

A Change Request or Bug in Proposed state does not automatically change the state of its linked Requirements, Use Cases, or Features.

Once the Product Manager authorizes the work and it begins, the Work Item Manager performs the following transitions:

For a Change Request:

- Change Request → In Work.
- Linked Requirements → In Work.
- Corresponding Use Cases → In Work.
- Corresponding Features → In Work.

For a Bug:

- Bug → In Work.
- Linked Requirements → In Work.
- Corresponding Use Cases → In Work.
- Corresponding Features → In Work.

This applies to every linked Requirement and every corresponding Use Case and Feature.

### 10.5 Reopening Previously Resolved Work

A Change Request or Bug may affect work that was previously Resolved.

When authorized work begins, the Work Item Manager must reopen the affected hierarchy.

For example:

```text
Feature A                  Resolved
  └── Use Case A1          Resolved
        └── Requirement R1 Resolved

Bug BUG-001
  └── Requirement R1
```

When the Bug is authorized and work begins:

```text
Feature A                  In Work
  └── Use Case A1          In Work
        └── Requirement R1 In Work

Bug BUG-001                In Work
```

The Work Item Manager must perform these transitions even when the affected items were previously Resolved.

The reopening must be recorded in the audit log.

### 10.6 Multiple Change Requests and Bugs

Multiple Change Requests and Bugs may affect the same Requirement.

The Work Item Manager must maintain awareness of all active work affecting that Requirement.

Resolving one Change Request or Bug must not automatically resolve the linked Requirement.

For example:

```text
Requirement R1
  ├── Change Request CR-001
  └── Bug BUG-001
```

If CR-001 is completed but BUG-001 remains unresolved, Requirement R1 cannot be resolved.

The Requirement can be resolved only after all relevant implementation work is complete, all required QA verification passes, and no outstanding issue prevents resolution.

### 10.7 Resolution of Change Requests and Bugs

A Change Request or Bug can be resolved only after its own completion criteria are satisfied.

For a Change Request:

- All approved changes have been implemented.
- Required code reviews have been approved.
- Changes have been merged into main.
- QA verification has passed.
- Required acceptance criteria have been satisfied.

For a Bug:

- The defect has been corrected.
- Required code reviews have been approved.
- The fix has been merged into main.
- QA has verified the fix.
- Relevant regression tests have passed.

Resolving a Change Request or Bug does not automatically resolve its linked Requirements, Use Cases, or Features.

The Work Item Manager must independently evaluate the completion conditions for each affected item.

### 10.8 Parent Resolution After Reopened Work

After a reopened Requirement has been verified:

- The Requirement may become Resolved after QA passes.
- Its Use Case may become Resolved only if all Requirements under it are Resolved and its other completion conditions are satisfied.
- Its Feature may become Resolved only if all Use Cases under it are Resolved and all Feature-level completion gates are satisfied.

A previously Resolved Feature must not automatically return to Resolved merely because one Bug or Change Request is resolved.

The entire completion hierarchy must be evaluated again.

## 11. Git and Development Workflow

### 11.1 Branching Strategy

The initial development strategy uses:

- `main` — protected production-ready branch.
- `dev` — shared development branch.

Developers work on the shared dev branch.

Multiple Developers may contribute changes for different Features and Use Cases to dev.

Developers must not push directly to main.

### 11.2 Development Task and Change Set Tracking

Each Development Task may contain multiple Change Sets.

Each Change Set may contain multiple Git commits.

Example:

```text
Feature A
  └── Use Case A1
        └── Development Task DT-001
              ├── Change Set CS-001
              │     ├── Commit 1
              │     └── Commit 2
              │
              └── Change Set CS-002
                    ├── Commit 3
                    └── Commit 4
```

Every Change Set and commit must be associated with the relevant Development Task.

This provides traceability between requirements, implementation, and source code.

### 11.3 Pull Requests

Changes are promoted from dev to main through Pull Requests.

A Pull Request may contain changes for:

- One Feature.
- Multiple Features.
- Multiple Development Tasks.

The Work Item Manager must be able to determine which Features and Development Tasks are affected by a Pull Request.

### 11.4 Code Review Before Merge

Every Feature has one Feature-level Code Review Task.

Before a Pull Request can be merged into main:

- The affected Feature-level Code Review Tasks must be identified.
- All required Code Review Tasks must be Resolved.
- The required Review Result must be Approved.
- All required CI checks must pass.
- Other mandatory merge conditions must be satisfied.

If a Pull Request contains changes for multiple Features, every affected Feature-level Code Review Task must be Resolved before merge.

If a Code Review Task is not Resolved, the merge must be blocked.

### 11.5 Review Across Multiple Change Sets and Pull Requests

A Feature-level Code Review Task may cover multiple Development Tasks, Change Sets, commits, and Pull Requests.

The Reviewer must consider the complete relevant change set for the Feature.

The review task must not be resolved until all required changes have been reviewed and approved.

If additional changes are introduced after approval, the Work Item Manager must determine whether the previous approval remains valid or whether another review is required.

The default should be to require re-review of changes that materially affect the approved code.

## 12. QA and Release Workflow

### 12.1 QA Environment

QA tests only builds generated from main.

QA does not test the shared dev branch.

This ensures that QA verifies code that has passed the required code review and merge gates.

### 12.2 Standard Workflow

The expected workflow is:

1. Product Manager authorizes work.
2. Developer implements the approved Development Task on dev.
3. Developer associates commits with the appropriate Change Sets and Development Task.
4. Developer moves the Development Task to In Test when implementation is complete.
5. Reviewer performs the Feature-level code review.
6. Reviewer resolves the Code Review Task after approval.
7. Pull Request is checked against all required review and CI gates.
8. Changes are merged into main.
9. A build is generated from main.
10. QA executes the required Test Cases.
11. QA records results and creates Bugs when Requirements are violated.
12. QA resolves work items when their completion criteria are satisfied.
13. Work Item Manager evaluates Use Case and Feature completion conditions.

### 12.3 Bug Fix Workflow

When QA identifies a Bug:

1. QA creates the Bug.
2. QA links it to the Requirement that is violated.
3. QA links the failed Test Case where applicable.
4. Product Manager reviews and authorizes the fix.
5. Work Item Manager moves the Bug and its affected Requirement, Use Case, and Feature hierarchy to In Work.
6. Developer implements the fix on dev.
7. The relevant Development Task and Change Sets are updated or created.
8. Reviewer reviews the affected Feature-level changes.
9. Required Code Review Tasks must be Resolved.
10. Changes are merged into main.
11. A new build is generated from main.
12. QA retests the Bug fix and performs relevant regression testing.
13. QA resolves the Bug and affected work items when their completion criteria are satisfied.

QA must not retest a fix on dev.

### 12.4 Release Environments

The release process uses:

- main.
- Staging.
- Production.

Staging and Production are deployment environments, not permanent Git branches.

The same verified build artifact should be promoted from Staging to Production.

The system should avoid rebuilding different artifacts between these environments.

## 13. Work Item Manager Architecture

The Work Item Manager is a deterministic Python component.

It is responsible for enforcing work item rules.

### 13.1 Responsibilities

The Work Item Manager handles:

- Work item creation and modification.
- Work item relationship validation.
- State transition validation.
- Work authorization checks.
- Automatic relationship discovery.
- Change Request and Bug state propagation.
- Reopening affected work items.
- Parent-child resolution validation.
- Development Task and Change Set tracking.
- Code Review Task enforcement.
- Agent permission checks.
- GitHub synchronization.
- Audit event generation.

### 13.2 Relationship Discovery

The Work Item Manager must be able to traverse the work item hierarchy.

Given a Requirement ID, it should determine:

- Its parent Use Case.
- Its parent Feature.
- Other relevant related work items.

Given a Change Request or Bug, it should determine all affected Requirements, Use Cases, and Features.

This logic must be deterministic and covered by automated tests.

### 13.3 State Transition Enforcement

Agents must not directly modify work item states through GitHub or other interfaces in a way that bypasses the Work Item Manager.

The Work Item Manager validates:

- Agent identity and permissions.
- Current state.
- Requested state.
- Work authorization.
- Relationship dependencies.
- Completion criteria.
- Applicable review and QA gates.

Invalid transitions must be rejected with a clear explanation.

### 13.4 Parent-Child Resolution Evaluation

When a Requirement, Use Case, or other child work item is resolved, the Work Item Manager evaluates the relevant parent completion conditions.

It must not automatically resolve a parent without satisfying all applicable rules.

The evaluation should be repeatable and safe to execute more than once.

### 13.5 GitHub Integration

GitHub will initially serve as the work item storage and collaboration interface.

The Work Item Manager will interact with GitHub through a dedicated integration layer.

The integration should support:

- Creating and updating issues.
- Reading work item data.
- Managing relationships.
- Updating labels and project fields.
- Tracking Pull Requests.
- Tracking commits.
- Enforcing required checks.
- Recording review and QA results.

The Work Item Manager remains the authority for business rules and lifecycle enforcement.

## 14. GitHub Integration

The initial implementation will use:

- GitHub Issues for work item records.
- GitHub Projects for work item tracking and visualization.
- GitHub labels and fields for classification.
- GitHub Pull Requests for code promotion.
- GitHub Actions for automated validation and enforcement.

The implementation should favor standard GitHub capabilities where possible.

Custom automation should be introduced only when native functionality cannot enforce the required workflow.

### 14.1 Work Item Identification

Each work item must have a unique identifier.

The system should maintain consistent references between:

- Features.
- Use Cases.
- Requirements.
- Development Tasks.
- Supporting Tasks.
- Code Review Tasks.
- Test Cases.
- Bugs.
- Change Requests.
- Change Sets.
- Pull Requests.
- Git commits.

### 14.2 Merge Protection

The main branch must be protected.

Required checks should prevent merging when:

- Required Feature-level Code Review Tasks are not Resolved.
- Required CI checks fail.
- Required approvals are missing.
- Other mandatory merge conditions are not satisfied.

A GitHub Actions workflow or equivalent integration should validate the Work Item Manager's merge conditions.

## 15. Coding Standards and Code Review Guidelines

The Reviewer must follow documented standards.

The following documents will define the standards:

- `PhantomLogic/Standards/CodingStandards.md`
- `PhantomLogic/Standards/CodeReviewGuidelines.md`

Coding Standards define the engineering conventions that Developers must follow.

Code Review Guidelines define how the Reviewer evaluates changes.

The Reviewer should focus on objective engineering quality and consistency.

The review should not become a subjective preference exercise.

## 16. Audit Integration

All significant work item operations must integrate with the central Phantom Logic audit system.

The existing AuditWriter framework will be used.

Agents must not write directly to the central audit log.

The Orchestrator coordinates audit recording through the established audit mechanism.

Important events include:

- Work item creation.
- Work item modification.
- Work authorization.
- State transitions.
- Automatic state propagation.
- Requirement relationship changes.
- Change Request and Bug creation.
- Reopening previously Resolved work.
- Development Task completion.
- Change Set and commit association.
- Code review decisions.
- QA results.
- Resolution and removal.
- Merge gate decisions.
- Release and deployment activities.

Automatic state changes must be auditable.

For example, when a Bug causes a previously Resolved Feature to return to In Work, the audit record should identify:

- The Bug that triggered the change.
- The linked Requirement.
- The affected Use Case.
- The affected Feature.
- The previous and new states.
- The authorization that permitted the work.
- The Work Item Manager operation responsible for the transition.

## 17. Security and Permissions

The Work Item Manager must enforce role-based permissions.

Examples:

| Operation | Authorized Agent |
|---|---|
| Create or refine Requirements | Product Manager |
| Authorize work | Product Manager |
| Move authorized work to In Work | Product Manager / Work Item Manager |
| Implement Development Tasks | Developer |
| Move Development Task to In Test | Developer |
| Perform code review | Reviewer |
| Approve Code Review Task | Reviewer |
| Resolve Code Review Task | Reviewer |
| Execute Test Cases | QA |
| Resolve verified Requirements | QA |
| Resolve verified Use Cases | QA, subject to completion rules |
| Resolve verified Features | QA, subject to completion rules |
| Enforce transitions and relationships | Work Item Manager |
| Coordinate overall workflow | Orchestrator |

Additional rules:

- Developers cannot resolve their own Development Tasks.
- Developers cannot approve their own Code Review Tasks.
- Reviewers cannot resolve Requirements or Features merely because code review is complete.
- QA cannot resolve failed Test Cases.
- Agents cannot bypass work authorization.
- Agents cannot bypass required code review or QA gates.
- Agents cannot directly modify protected Git branches.
- Removed work items require an authorized decision and reason.

The Work Item Manager must validate every operation rather than trusting the requesting agent.

## 18. Testing Strategy

The Work Item Manager must have comprehensive automated tests.

Testing should cover:

### 18.1 Work Item Tests

- Creation of each work item type.
- Required field validation.
- Relationship validation.
- Invalid relationship rejection.
- Duplicate relationship handling.

### 18.2 State Transition Tests

- Valid transitions.
- Invalid transitions.
- Agent permission enforcement.
- Blocked state behavior.
- Restoration of previous state.
- Removal authorization.

### 18.3 Change Request and Bug Tests

- Mandatory Requirement linking.
- Automatic Use Case discovery.
- Automatic Feature discovery.
- Multiple Requirements.
- Multiple Use Cases.
- Multiple Features.
- State propagation.
- Reopening previously Resolved work.
- Multiple active Bugs and Change Requests affecting the same Requirement.
- Preventing premature Requirement resolution.

### 18.4 Hierarchical Resolution Tests

- Requirement resolution conditions.
- Use Case resolution when all Requirements are Resolved.
- Preventing Use Case resolution when any Requirement remains unresolved.
- Feature resolution when all Use Cases are Resolved.
- Preventing Feature resolution when any Use Case remains unresolved.
- Feature-level Code Review Task enforcement.
- Supporting Task completion.
- QA verification requirements.
- Re-evaluation after reopened work.

### 18.5 Development and Review Tests

- Development Task to Change Set association.
- Multiple Change Sets per Development Task.
- Multiple commits per Change Set.
- Feature-level Code Review Task association.
- Multiple Features in one Pull Request.
- Blocking merge when any affected Feature-level Code Review Task is unresolved.
- Re-review when approved changes are materially modified.

### 18.6 Audit Tests

- Audit event generation.
- Automatic state propagation audit records.
- Reopening audit records.
- Authorization audit records.
- Code review and QA audit records.

## 19. Implementation Roadmap

Implementation should proceed incrementally.

### Phase 1: Finalize Work Item Design

- Finalize work item types.
- Finalize relationships.
- Finalize states.
- Finalize transition permissions.
- Finalize Change Request and Bug behavior.
- Finalize hierarchical completion rules.
- Finalize code review workflow.

### Phase 2: Define Engineering Standards

Create:

- `PhantomLogic/Standards/CodingStandards.md`
- `PhantomLogic/Standards/CodeReviewGuidelines.md`

### Phase 3: Define GitHub Work Item Structure

- Configure issue types.
- Define labels and fields.
- Configure GitHub Projects.
- Define work item relationships.
- Define Pull Request conventions.

### Phase 4: Implement Work Item Domain Model

- Define work item models.
- Implement relationship validation.
- Implement state transition rules.
- Implement permission validation.
- Implement automatic relationship discovery.
- Implement Change Request and Bug propagation.
- Implement hierarchical resolution evaluation.
- Write automated tests.

### Phase 5: Implement GitHub Integration

- Build GitHub client.
- Implement issue creation and updates.
- Implement relationship synchronization.
- Implement Project integration.
- Implement Pull Request and commit tracking.

### Phase 6: Implement Work Item Manager

- Implement deterministic workflow operations.
- Integrate GitHub client.
- Integrate audit recording.
- Enforce permissions and transitions.
- Implement merge gate validation.

### Phase 7: Integrate Agents

Integrate agents incrementally.

Each agent should use the Work Item Manager for work item operations.

### Phase 8: Implement CI/CD Enforcement

- Configure GitHub Actions.
- Enforce Pull Request requirements.
- Validate Feature-level code review completion.
- Validate CI checks.
- Prevent unauthorized merges.

### Phase 9: End-to-End Testing

Test complete workflows:

- New Feature development.
- Multiple Use Cases in a Feature.
- Multiple Requirements in a Use Case.
- Change Request affecting multiple Features.
- Bug reopening a Resolved Feature.
- Multiple Bugs affecting one Requirement.
- Feature-level code review.
- QA verification.
- Staging and Production deployment.

## 20. Design Decisions and Future Considerations

The following decisions are established:

1. Work Item Manager is deterministic Python code, not an AI agent.
2. Product Manager controls work authorization.
3. Orchestrator coordinates work but does not routinely manage individual state transitions.
4. Every Use Case has one Development Task.
5. Every Use Case can have multiple Requirements.
6. Test Cases are linked directly to Requirements.
7. Every Feature has one Feature-level Code Review Task.
8. A Development Task can have multiple Change Sets.
9. A Change Set can contain multiple Git commits.
10. Reviewer is a separate agent from Developer.
11. Code Review Tasks use Proposed, In Work, Review, and Resolved states.
12. QA tests only builds generated from main.
13. Developers work on the shared dev branch.
14. Changes are promoted to main through Pull Requests.
15. All affected Feature-level Code Review Tasks must be Resolved before a Pull Request can merge.
16. Every Change Request must link to at least one Requirement.
17. Every Bug must link to at least one Requirement that it violates.
18. The Work Item Manager derives affected Use Cases and Features from linked Requirements.
19. Authorized Change Requests and Bugs automatically move affected Requirements, Use Cases, and Features to In Work.
20. Previously Resolved work can be reopened when an authorized Change Request or Bug affects it.
21. A Use Case can only be Resolved when all its Requirements are Resolved and its other completion criteria are satisfied.
22. A Feature can only be Resolved when all its Use Cases are Resolved and all Feature-level completion gates are satisfied.
23. Resolving a Change Request or Bug does not automatically resolve its linked Requirements, Use Cases, or Features.
24. QA remains responsible for successful verification. The Work Item Manager enforces the conditions for resolution.
25. All significant work item operations must be recorded through the central audit mechanism.

Future considerations include:

- Multiple development branches, if the shared dev workflow becomes insufficient.
- More advanced dependency management.
- Automated impact analysis.
- Work item analytics and reporting.
- Release planning and milestone management.
- More granular approval policies.
- Automated detection of stale or inconsistent work item relationships.

These should be introduced only when there is a clear need.

---

**End of Document**