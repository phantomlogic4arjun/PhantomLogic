# State Transition Matrix

**Project:** Phantom Logic  
**Document Status:** Design  
**Version:** 2.0  
**Last Updated:** 21 November 2026

---

## 1. Purpose

This document defines the permitted state transitions, transition ownership, and enforcement rules for work items within Phantom Logic.

The objective is to ensure that:

- Work progresses through a predictable lifecycle.
- Each agent has clearly defined state-transition responsibilities.
- Changes to existing requirements are properly propagated through the work-item hierarchy.
- Completed implementation is not confused with successful QA verification.
- Parent work items cannot be resolved while required child work remains incomplete.
- All automated state changes are deterministic, validated, and audited.

The Work Item Manager is responsible for enforcing these rules. Agents may request or initiate permitted transitions, but they cannot bypass the transition rules.

## 2. Work Item Types

The work-item hierarchy consists of:

```text
Epic (Optional)
└── Feature
    ├── Use Case
    │   ├── Requirement
    │   │   ├── Test Case(s)
    │   │   └── Bug(s), when applicable
    │   └── Development Task
    │
    ├── Supporting Tasks
    │   ├── Architecture Task
    │   ├── Design Task
    │   ├── Security Task
    │   └── DevOps Task
    │
    └── Code Review Task (one per Feature)
```

Additional work-item types:

- Change Request
- Bug

A Feature may have multiple Use Cases. Each Use Case has one Development Task and may have multiple Requirements.

A Feature-level Code Review Task covers the code changes associated with the Feature, including changes from multiple Development Tasks, Change Sets, commits, and Pull Requests.

## 3. Standard Work Item States

The standard lifecycle states are:

| State | Description |
|---|---|
| Proposed | Work has been identified but has not been authorized to begin. |
| In Work | Work has been authorized and is actively being implemented or addressed. |
| In Test | Work is available for QA verification. |
| Resolved | Work has satisfied its completion criteria and has been verified or approved by the responsible role. |
| Blocked | Work cannot proceed because of an identified dependency, issue, or external constraint. |
| Removed | Work has been formally removed from scope. |

### 3.1 Exceptional States

**Blocked**

Blocked is an exceptional state. It does not replace the item's normal lifecycle.

When an item becomes Blocked:

- The Work Item Manager records its previous state as its return state.
- The item moves to Blocked.
- When the blocker is cleared, the item returns to its recorded return state.
- If new authorized work affects the item while it is Blocked, its return state is updated to In Work without changing its current Blocked state.

**Removed**

Removed indicates that the item has been formally removed from scope.

- A reason is mandatory.
- Appropriate authorization is mandatory.
- Removed items cannot be automatically reopened.
- Reinstatement requires an explicit Product Manager decision and an audited operation.

## 4. General State Transition Matrix

The following table defines the permitted transitions for standard work items.

| Current State | Target State | Authorized By | Conditions |
|---|---|---|---|
| Proposed | In Work | Product Manager | Work is approved and authorized. |
| Proposed | Removed | Product Manager | Removal is authorized and a reason is recorded. |
| In Work | In Test | Work Item Manager | Implementation is complete, required review and merge gates are satisfied, and the relevant build is available from main. |
| In Work | Blocked | Work Item Manager | A valid blocker is recorded. |
| In Work | Removed | Product Manager | Removal is authorized and a reason is recorded. |
| In Test | Resolved | QA | Verification passes and all completion criteria are satisfied. |
| In Test | In Work | QA / Work Item Manager | Verification fails or additional implementation is required. |
| In Test | Blocked | Work Item Manager | A valid blocker prevents verification. |
| In Test | Removed | Product Manager | Removal is authorized and a reason is recorded. |
| Resolved | In Work | Work Item Manager | An authorized Change Request or Bug requires the item to be reopened. |
| Resolved | Removed | Product Manager | Formal removal is authorized and recorded. |
| Blocked | Previous State | Work Item Manager | The blocker has been cleared. The recorded return state is restored. |
| Blocked | Removed | Product Manager | Removal is authorized and a reason is recorded. |

### 4.1 Restricted Transitions

The following transitions are not permitted:

- Proposed → In Test
- Proposed → Resolved
- In Work → Resolved
- Resolved → Proposed
- Removed → In Work
- Removed → Proposed through an ordinary transition
- Removed → any other state without explicit reinstatement authorization

A Development Task cannot be resolved directly by the Developer.

A Feature, Use Case, or Requirement cannot be resolved simply because its implementation is complete.

### 4.2 Reinstatement of Removed Items

A Removed item cannot be reopened through normal Change Request or Bug propagation.

If an authorized Change Request or Bug references a Removed Requirement:

1. The Work Item Manager rejects the propagation operation.
2. The Product Manager is notified.
3. The Product Manager must explicitly reinstate the Requirement.
4. The reinstatement is recorded in the audit log.
5. The Requirement enters the appropriate lifecycle state through a separately authorized operation.

The same principle applies to Removed parent work items.

## 5. Transition Ownership and Responsibilities

### 5.1 Orchestrator

The Orchestrator oversees the overall execution process.

Responsibilities:

- Monitor work-item progress.
- Coordinate agents.
- Identify dependencies and blockers.
- Ensure required workflow gates are satisfied.
- Coordinate escalation when work cannot proceed.
- Monitor the status of Features and their supporting work.

The Orchestrator does not routinely move work items into In Work or resolve them.

### 5.2 Product Manager

The Product Manager controls work authorization and scope.

Responsibilities:

- Review and approve proposed work.
- Move authorized Features, Use Cases, Requirements, and associated implementation Tasks from Proposed to In Work.
- Authorize Change Requests and Bugs.
- Approve scope changes.
- Authorize removal and reinstatement of work items.

The Product Manager does not certify implementation or QA completion.

### 5.3 Developer

The Developer is responsible for implementation.

Responsibilities:

- Implement authorized work.
- Associate commits and Change Sets with their Development Tasks.
- Complete implementation before moving Development Tasks into In Test.
- Submit changes for code review.
- Address review findings.
- Make fixes when QA identifies defects.

The Developer cannot:

- Resolve their own Development Tasks.
- Approve their own Feature-level Code Review Task.
- Bypass the code-review and Pull Request gates.
- Push directly to main.

### 5.4 Reviewer

The Reviewer is a separate agent acting as a Senior Developer.

Responsibilities:

- Review code changes against established Coding Standards and Code Review Guidelines.
- Evaluate maintainability, readability, naming, separation of concerns, duplication, and consistency with project conventions.
- Identify code-quality and engineering-practice issues.
- Request changes where necessary.
- Approve the Feature-level Code Review Task when all review requirements are satisfied.

The Reviewer does not perform QA or certify functional correctness.

The Reviewer cannot resolve Requirements, Use Cases, Development Tasks, or Features.

The Reviewer must be different from the Developer responsible for the changes being reviewed.

### 5.5 QA

QA is responsible for verification and acceptance.

Responsibilities:

- Execute Test Cases against builds generated from main.
- Record test results.
- Create Bugs when defects are identified.
- Verify Bug fixes.
- Resolve Test Cases only when they pass.
- Verify Requirements, Use Cases, Development Tasks, and Features against their respective completion criteria.
- Resolve eligible work items after successful verification.

QA cannot resolve a failed Test Case or bypass outstanding completion gates.

### 5.6 Work Item Manager

The Work Item Manager is a deterministic system component, not an autonomous decision-making agent.

Responsibilities:

- Validate requested transitions.
- Enforce transition permissions.
- Apply authorized state propagation.
- Evaluate parent completion eligibility.
- Enforce hierarchy and dependency rules.
- Prevent invalid transitions.
- Maintain Blocked return states.
- Reject operations involving Removed items unless reinstatement is authorized.
- Record all significant state changes in the audit log.

The Work Item Manager does not independently certify that implementation or QA has succeeded. It evaluates recorded evidence and enforces the rules defined in this document.

## 6. Development Task Lifecycle

Each Use Case has one Development Task.

A Development Task may have multiple Change Sets, and each Change Set may contain multiple Git commits.

```text
Proposed
   |
   | Product Manager authorizes work
   v
In Work
   |
   | Developer completes implementation
   v
In Test
   |
   | QA verifies implementation
   v
Resolved
```

### 6.1 Developer Responsibilities

The Developer:

1. Works on the authorized Development Task.
2. Creates one or more Change Sets.
3. Associates commits with the appropriate Change Sets.
4. Ensures all relevant commits are associated with the Development Task.
5. Completes implementation.
6. Moves the Development Task to In Test.

The Developer does not resolve the Development Task.

### 6.2 QA Responsibilities

QA verifies the implementation using a build generated from main.

- If verification passes, QA resolves the Development Task.
- If verification fails, QA moves the Development Task back to In Work and records the failure.
- If verification cannot proceed, the Work Item Manager may move it to Blocked.

A Development Task cannot be resolved while its implementation has not passed the required verification.

## 7. Change Sets, Commits, and Pull Request Gates

### 7.1 Change Set Structure

The relationship between development work and Git changes is:

```text
Development Task
   |
   ├── Change Set 1
   │      ├── Commit 1
   │      └── Commit 2
   |
   ├── Change Set 2
   │      ├── Commit 3
   │      └── Commit 4
   |
   └── Change Set 3
          └── Commit 5
```

Every Change Set must be associated with a Development Task.

Every commit included in a Change Set must be traceable to that Change Set and its Development Task.

### 7.2 Branching and Promotion

The development workflow uses:

- `dev` as the shared development branch.
- `main` as the protected integration and release branch.

Developers work on `dev`. Changes are promoted to `main` through Pull Requests.

QA tests only builds generated from `main`.

### 7.3 Code Review Gate

Each Feature has one Feature-level Code Review Task.

The Reviewer examines all relevant changes associated with the Feature, including multiple Development Tasks, Change Sets, commits, and Pull Requests.

A Pull Request containing changes for multiple Features must satisfy the review requirements for every affected Feature.

A Pull Request cannot be merged into main until:

- All required Feature-level Code Review Tasks are Resolved.
- Required CI checks have passed.
- Required security checks have passed.
- All other applicable branch protection requirements are satisfied.

### 7.4 Review Approval Invalidation

A previous review approval must not be treated as approval of new, unreviewed code.

If material code changes are added after approval:

1. The affected Feature-level Code Review Task must be reopened or returned to the appropriate review state.
2. The new commits must be included in the review scope.
3. The Reviewer must examine the new changes.
4. The approval must be renewed before the relevant Pull Request can be merged.

The Work Item Manager must maintain traceability between review approval and the commits or Pull Requests actually reviewed.

### 7.5 Main Branch Protection

The Developer must not be able to merge changes into main without satisfying the required gates.

If a Feature-level Code Review Task is not Resolved, the relevant Pull Request must not be merged.

This must be enforced through repository protections and automated checks, not merely through agent instructions.

## 8. Transition into QA

Implementation completion and QA readiness are separate events.

A Development Task can enter In Test when the Developer has completed implementation.

Requirements, Use Cases, and Features become eligible for In Test through deterministic readiness evaluation by the Work Item Manager.

### 8.1 Requirement → In Test

A Requirement becomes eligible for In Test when:

- Its implementation is included in a build generated from main.
- The relevant Development Task has reached the required implementation and verification-readiness stage.
- Required code review and merge gates have been satisfied.
- Its acceptance criteria and mandatory Test Cases are available for QA.

The Work Item Manager performs the transition when the readiness conditions are satisfied.

### 8.2 Use Case → In Test

A Use Case becomes eligible for In Test when:

- Its Development Task is ready for QA.
- Every Requirement under the Use Case is either In Test or Resolved.
- All relevant implementation changes are available in a build from main.
- Required pre-QA gates have been satisfied.

The Work Item Manager evaluates these conditions and performs the transition.

### 8.3 Feature → In Test

A Feature becomes eligible for In Test when:

- Every Use Case under the Feature is either In Test or Resolved.
- The Feature-level Code Review Task is Resolved.
- All required supporting Tasks are complete or have reached their required pre-QA state.
- Required security and CI gates have passed.
- Relevant changes are available in a build from main.

The Work Item Manager performs the transition when these conditions are satisfied.

### 8.4 QA Completion

QA verifies the relevant work items independently.

Successful verification does not mean every parent can automatically be resolved. The Work Item Manager must evaluate the applicable completion criteria before permitting each resolution.

## 9. Feature-Level Code Review Task Lifecycle

The Feature-level Code Review Task uses a separate lifecycle:

```text
Proposed
   |
   | Reviewer begins review
   v
In Work
   |
   | Review completed; findings require assessment
   v
Review
   |
   | All required changes addressed and approved
   v
Resolved
```

### 9.1 Code Review States

| State | Description |
|---|---|
| Proposed | Review is identified but has not started. |
| In Work | Reviewer is examining the changes. |
| Review | Review findings and requested changes are being addressed or re-evaluated. |
| Resolved | Reviewer has approved the relevant code changes and all required findings are addressed. |

### 9.2 Review Result

The Code Review Task also maintains a separate Review Result field:

- Pending
- Changes Requested
- Approved

The Review Result is not a replacement for the task state.

For example:

- In Work + Pending: Review is underway.
- Review + Changes Requested: Changes are required.
- Resolved + Approved: Review is complete and approved.

### 9.3 Reviewer Restrictions

- The Developer cannot approve their own code.
- The Reviewer must be a separate agent.
- The Reviewer must use the established Coding Standards and Code Review Guidelines.
- The Reviewer must not approve changes that have unresolved mandatory review findings.
- New material changes invalidate approval for the affected review scope.

## 10. Change Request Lifecycle and State Propagation

A Change Request represents an authorized modification to existing requirements or functionality.

Every Change Request must link to at least one existing Requirement that it affects.

The Work Item Manager derives affected Use Cases and Features by following:

```text
Change Request
      |
      v
Requirement(s)
      |
      v
Use Case(s)
      |
      v
Feature(s)
```

Use Cases and Features must not require redundant manual links on the Change Request.

### 10.1 Proposed Change Request

When a Change Request is Proposed:

- No linked Requirement changes state.
- No linked Use Case changes state.
- No linked Feature changes state.
- No implementation work is authorized.

### 10.2 Authorized Change Request

When the Product Manager authorizes the Change Request and work begins:

1. Change Request → In Work.
2. Every linked Requirement → In Work.
3. Every corresponding Use Case → In Work.
4. Every corresponding Feature → In Work.

The Work Item Manager performs this propagation.

### 10.3 Reopening Resolved Work

An authorized Change Request may affect previously Resolved work.

In that case:

- Resolved Requirements are reopened to In Work.
- Resolved Use Cases are reopened to In Work.
- Resolved Features are reopened to In Work.

This is an explicit exception to the ordinary lifecycle and is permitted only through authorized Change Request propagation.

The Work Item Manager must record the reason and the originating Change Request in the audit log.

### 10.4 Multiple Requirements and Shared Parents

If a Change Request affects multiple Requirements:

- Every affected Requirement is transitioned.
- Every corresponding Use Case is transitioned.
- Every corresponding Feature is transitioned.
- Duplicate parent transitions are removed.

A parent is transitioned only once per propagation operation.

Unrelated sibling Requirements are not automatically reopened.

For example, if a Use Case contains three Requirements and a Change Request affects only one, the affected Requirement and its parent Use Case and Feature move to In Work. The other two Requirements remain in their existing states.

### 10.5 Adding Requirements to an Active Change Request

If a Requirement is added to an authorized Change Request:

- The Work Item Manager validates the Requirement.
- The Requirement and its parent hierarchy are transitioned to In Work as applicable.
- The scope change is audited.

### 10.6 Removing Requirements from a Change Request

Removing a Requirement from an active Change Request requires Product Manager authorization.

The Work Item Manager must:

- Validate the authorization.
- Record the scope change.
- Preserve the Requirement's current state.
- Avoid automatically restoring or resolving the Requirement.

### 10.7 Change Request Resolution

Resolving a Change Request does not automatically resolve its linked Requirements, Use Cases, or Features.

Each linked item must independently satisfy its completion criteria.

## 11. Bug Lifecycle and State Propagation

A Bug represents a defect in existing or expected functionality.

Every Bug must link to at least one Requirement that it violates.

Where applicable, the Bug must also link to the failed Test Case that exposed the defect.

The Work Item Manager derives affected Use Cases and Features through the linked Requirements.

### 11.1 Proposed Bug

When QA identifies a defect:

1. QA records the failed Test Case.
2. QA creates a Bug.
3. The Bug is linked to the violated Requirement.
4. The Bug may also be linked to the failed Test Case.
5. The Bug remains Proposed until Product Manager authorization.

Creating a Bug does not automatically reopen the linked hierarchy.

### 11.2 Authorized Bug

When the Product Manager authorizes the Bug and work begins:

1. Bug → In Work.
2. Every linked Requirement → In Work.
3. Every corresponding Use Case → In Work.
4. Every corresponding Feature → In Work.

The Work Item Manager performs this propagation.

### 11.3 Bugs Affecting Resolved Work

If a Bug affects previously Resolved work, the authorized Bug propagation operation reopens the affected Requirements, Use Cases, and Features.

This is necessary to ensure that previously accepted functionality is not treated as complete while a known defect remains outstanding.

### 11.4 Multiple Bugs Affecting the Same Requirement

A Requirement may be affected by multiple active Bugs.

Resolving one Bug does not resolve the Requirement if other relevant Bugs or implementation work remain outstanding.

The Work Item Manager must consider all applicable active Change Requests and Bugs when evaluating Requirement completion.

### 11.5 Bug Resolution

After implementation and code review:

- The relevant changes must be merged into main.
- A build must be generated from main.
- The Bug moves to In Test when its fix is ready for QA.
- QA verifies the fix.
- QA resolves the Bug only when verification passes.

Resolving the Bug does not automatically resolve its linked Requirement, Use Case, or Feature.

### 11.6 Failed Bug Verification

If QA determines that the defect remains:

- The Bug returns to In Work.
- The failure is recorded.
- The Developer addresses the issue.
- The relevant review and merge gates must be satisfied again.
- QA verifies a new build from main.

## 12. Change Request and Bug Propagation Rules

The following rules apply to both Change Requests and Bugs.

| Scenario | Required Behavior |
|---|---|
| Proposed CR/Bug created | No hierarchy state changes. |
| Product Manager authorizes CR/Bug | CR/Bug and affected hierarchy move to In Work. |
| Linked Requirement is Resolved | Reopen it to In Work. |
| Linked Use Case is Resolved | Reopen it to In Work. |
| Linked Feature is Resolved | Reopen it to In Work. |
| Multiple Requirements share a parent | Transition each parent only once. |
| Unaffected sibling Requirement exists | Preserve its current state. |
| Multiple active CRs/Bugs affect one Requirement | Keep Requirement unresolved until all relevant work is complete and verification passes. |
| One CR/Bug is resolved | Do not automatically resolve the hierarchy. |
| Requirement added to active CR/Bug | Validate and propagate In Work. |
| Requirement removed from active CR/Bug | Require authorized scope change; preserve its state. |
| Affected item is Blocked | Preserve Blocked and update its return state to In Work. |
| Linked Requirement is Removed | Reject propagation until explicit reinstatement. |

## 13. Blocked State Handling

Blocked is an exceptional state and must not erase the item's normal lifecycle state.

### 13.1 Entering Blocked

When an item becomes Blocked:

- The Work Item Manager records its current state as the return state.
- The item moves to Blocked.
- The blocker, reason, and relevant dependency are recorded.

### 13.2 Clearing a Blocker

When the blocker is resolved:

- The Work Item Manager restores the recorded return state.
- The blocker resolution is audited.

### 13.3 New Authorized Work While Blocked

If a Change Request or Bug affects a Blocked Requirement, Use Case, or Feature:

- The item remains Blocked.
- Its saved return state is changed to In Work.
- The authorized work is recorded.
- When the blocker clears, the item returns to In Work.

This prevents the item from incorrectly returning to Resolved or another outdated state.

## 14. Hierarchical Resolution Rules

Work items must be resolved from the bottom of the hierarchy upward.

```text
Requirement
    |
    v
Use Case
    |
    v
Feature
```

A child becoming Resolved does not automatically resolve its parent.

The Work Item Manager evaluates parent eligibility, while QA remains responsible for successful verification and confirming completion.

### 14.1 Requirement Resolution

A Requirement can be Resolved only when:

- Its implementation is complete.
- Its associated Development Task is Resolved.
- All mandatory Test Cases have Passed.
- Acceptance criteria are satisfied.
- No relevant active Change Request remains outstanding.
- No unresolved release-blocking Bug violates the Requirement.
- Required verification evidence is recorded.

If any condition is not satisfied, the Requirement cannot be resolved.

### 14.2 Use Case Resolution

A Use Case can be Resolved only when:

- Every Requirement under it is Resolved.
- Its associated Development Task is Resolved.
- Its acceptance criteria are satisfied.
- Required QA verification is complete.
- No relevant outstanding implementation work or release-blocking defects remain.

A Use Case may be In Work while some of its Requirements remain Resolved.

The Work Item Manager must not reopen unaffected Requirements merely because the parent Use Case has reopened.

### 14.3 Feature Resolution

A Feature can be Resolved only when:

- Every Use Case under the Feature is Resolved.
- All required Feature-level supporting Tasks are Resolved.
- The Feature-level Code Review Task is Resolved.
- Required security checks have passed.
- Required CI checks have passed.
- Required QA verification is complete.
- No unresolved release-blocking Bugs remain.
- All Feature acceptance criteria are satisfied.

A Feature cannot be resolved merely because its Development Tasks or Code Review Task are complete.

### 14.4 Parent Resolution Enforcement

The Work Item Manager must evaluate all required children and gates before allowing a parent to be resolved.

The resolution sequence is:

1. Resolve eligible Requirements.
2. Evaluate and resolve eligible Use Cases.
3. Evaluate and resolve eligible Features.
4. Evaluate any associated Epic, if applicable.

The Work Item Manager must not automatically resolve a parent without the required verification and authorization evidence.

## 15. Test Case Lifecycle

Test Cases are linked directly to Requirements.

Their results are recorded separately from the state of the Requirement.

A Test Case can have the following execution results:

- Not Run
- Passed
- Failed
- Blocked

A Test Case is considered complete only when its required execution has been performed and the result is Passed.

### 15.1 Test Case Rules

- QA executes Test Cases against builds generated from main.
- QA may resolve a Test Case only when it has Passed.
- A Failed Test Case cannot be resolved.
- A Failed Test Case associated with a defect should result in a Bug linked to the violated Requirement and failed Test Case.
- A Blocked Test Case must retain its blocked execution result until it can be executed.
- Re-execution must retain traceability to earlier results.

A failed Test Case does not independently reopen a Resolved Requirement. The associated Bug must be authorized by the Product Manager, after which the Work Item Manager performs the required hierarchy propagation.

## 16. State Transition Validation Rules

Before applying any state transition, the Work Item Manager must validate:

1. The requested transition is permitted.
2. The requesting agent has the required authority.
3. The work item exists.
4. Required relationships are valid.
5. Required approval evidence exists.
6. Required completion conditions are satisfied.
7. The item is not Removed.
8. Blocked return-state rules are respected.
9. No conflicting active work prevents the transition.
10. The transition does not violate parent-child completion rules.

If validation fails:

- The transition must be rejected.
- The current state must remain unchanged.
- The reason for rejection must be returned to the requesting agent.
- The attempted operation must be recorded in the audit log when it is a significant workflow action.

## 17. Audit Requirements

Every significant state transition must be recorded in the central audit system.

At minimum, the audit record must capture:

- Work Item ID.
- Work Item Type.
- Previous State.
- New State.
- Initiating Agent or System Component.
- Timestamp.
- Reason for Transition.
- Related Work Item IDs.
- Authorization Reference, where applicable.
- Transition Source, such as manual request, QA verification, or automated propagation.

### 17.1 Mandatory Audit Events

The following operations must be audited:

- Proposed → In Work authorization.
- In Work → In Test.
- In Test → Resolved.
- In Test → In Work following failed verification.
- Resolved → In Work reopening.
- Any transition into or out of Blocked.
- Any transition into Removed.
- Removed-item reinstatement.
- Change Request authorization and propagation.
- Bug authorization and propagation.
- Requirement addition or removal from an active Change Request or Bug.
- Code Review approval and approval invalidation.
- Rejected state-transition attempts where required by audit policy.
- Parent resolution eligibility evaluation and resolution.

Automated propagation must identify the originating Change Request or Bug so that the entire operation can be traced.

## 18. Final Enforcement Principles

The Work Item Manager must enforce the following principles consistently:

1. No work begins without Product Manager authorization.
2. Proposed Change Requests and Bugs do not change the state of existing work.
3. Authorized Change Requests and Bugs reopen all affected Requirements and their parent hierarchy.
4. Unaffected sibling Requirements are not automatically reopened.
5. Resolving a Change Request or Bug does not automatically resolve the affected hierarchy.
6. Multiple active Change Requests and Bugs must be considered before resolving affected Requirements.
7. Blocked items retain their exceptional state and an appropriate return state.
8. Removed items cannot be automatically reopened.
9. Developers cannot resolve Development Tasks.
10. Reviewers cannot review and approve their own changes.
11. Code Review approval is mandatory before the relevant changes can be merged into main.
12. QA tests only builds generated from main.
13. A failed QA verification requires the relevant work to return to In Work.
14. Requirements must be resolved before their Use Cases.
15. Use Cases must be resolved before their Features.
16. Parent resolution requires all applicable child and supporting completion gates.
17. The Work Item Manager enforces transitions but does not independently certify implementation or QA success.
18. Every significant transition and automated propagation must be auditable.

---

**End of Document**