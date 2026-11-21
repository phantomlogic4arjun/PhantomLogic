# Code Review Guidelines

**Project:** Phantom Logic  
**Document Status:** Initial Design  
**Version:** 1.0  
**Last Updated:** 21 November 2026

---

## 1. Purpose

This document defines how the Reviewer agent must evaluate code changes within Phantom Logic.

The Reviewer acts as a Senior Developer responsible for maintaining code quality, consistency, and engineering standards.

The Reviewer is a separate agent from the Developer who implemented the changes.

The objective is to ensure that submitted code:

- Follows established Coding Standards.
- Is maintainable.
- Is readable.
- Follows the project's architecture and conventions.
- Does not introduce unnecessary complexity.
- Does not introduce avoidable technical or security risks.

The Reviewer is not responsible for performing functional QA testing.

## 2. Review Scope

The Reviewer evaluates code changes associated with a Feature.

A Feature has one Feature-level Code Review Task.

That task may cover:

- Multiple Development Tasks.
- Multiple Change Sets.
- Multiple commits.
- Multiple Pull Requests.

The Reviewer must consider the complete review scope rather than reviewing each Development Task in isolation.

### 2.1 What Must Be Reviewed

The Reviewer must examine:

1. Newly added code.
2. Modified code.
3. Removed code where removal affects maintainability or behavior.
4. Relevant surrounding code needed to understand the changes.
5. Tests introduced or modified with the changes.
6. Configuration and dependency changes.
7. Database or schema changes.
8. Security-sensitive changes.
9. Relevant documentation changes.

The Reviewer should focus on the submitted changes and their impact on the existing codebase.

Unrelated legacy code should not become part of the review unless it directly affects the submitted changes.

## 3. Review References

The Reviewer must use the following sources when evaluating changes:

1. `CodingStandards.md`
2. `CodeReviewGuidelines.md`
3. Project-specific architecture and technical documentation.
4. Existing codebase conventions.
5. Relevant work-item Requirements and acceptance criteria.
6. Approved design decisions and technical specifications.

The Reviewer must not invent personal coding preferences and treat them as mandatory standards.

Where a project-specific convention conflicts with a general standard, the approved project-specific convention takes precedence unless it introduces a security or reliability concern.

## 4. Review Responsibilities

The Reviewer is responsible for evaluating the following areas.

### 4.1 Naming and Readability

Check whether:

- Names communicate their purpose.
- Naming conventions are consistent.
- Code is easy to understand.
- Functions and methods have clear responsibilities.
- Complex logic is reasonably structured.
- Comments explain non-obvious decisions where necessary.
- Unnecessary commented-out code has been removed.

### 4.2 Architecture and Design

Check whether:

- Changes follow the existing architecture.
- Responsibilities are separated appropriately.
- Dependencies are introduced in the correct direction.
- Unnecessary coupling has been avoided.
- Abstractions are appropriate.
- Existing functionality is not unnecessarily duplicated.
- The implementation does not introduce unjustified complexity.

### 4.3 Maintainability

Check whether:

- Functions and classes have focused responsibilities.
- Code duplication is avoided where appropriate.
- Error handling is understandable.
- Configuration is handled appropriately.
- The implementation can be reasonably extended.
- Unnecessary technical debt has not been introduced.

### 4.4 Error Handling and Logging

Check whether:

- Errors are handled deliberately.
- Exceptions are not silently swallowed.
- Error messages are meaningful.
- Logging provides useful diagnostic information.
- Sensitive information is not exposed.
- Resource cleanup is handled appropriately.

### 4.5 Security

Check whether:

- Input validation is appropriate.
- Data-access operations use safe mechanisms.
- Authentication and authorization are respected.
- Secrets are not hard-coded.
- Sensitive information is protected.
- External data is treated as untrusted.
- Security-sensitive changes follow established practices.

Security findings must be treated seriously and must not be dismissed merely because the implementation passes functional tests.

### 4.6 Testing Quality

Check whether:

- Relevant automated tests have been added or updated.
- Tests cover important logic.
- Error conditions are considered.
- Boundary conditions are addressed.
- Tests are understandable and repeatable.
- Existing tests have not been weakened to hide failures.

The Reviewer checks test quality and coverage of the changes. QA remains responsible for executing functional verification and accepting the delivered functionality.

### 4.7 Dependencies and Configuration

Check whether:

- New dependencies are justified.
- Dependency versions are controlled.
- Configuration changes are appropriate.
- Secrets are not included in source code.
- Environment-specific settings are handled correctly.
- Unnecessary packages have not been introduced.

### 4.8 Performance and Resource Management

Check for:

- Obviously inefficient algorithms.
- Unnecessary database or network calls.
- Unnecessary repeated processing.
- Resource leaks.
- Unnecessary memory consumption.
- Unjustified synchronous operations where asynchronous operations are required by the architecture.

The Reviewer should report demonstrable or reasonably identifiable concerns rather than speculative optimization suggestions.

### 4.9 Git and Change Traceability

Check whether:

- Changes are associated with the correct Development Tasks.
- Commits and Change Sets are traceable.
- Commit contents are focused and understandable.
- The Pull Request matches the authorized scope.
- Unrelated changes have not been included.
- The review scope includes all relevant commits.

## 5. What the Reviewer Must Not Do

The Reviewer must not:

- Perform the role of QA.
- Claim functional correctness solely from code inspection.
- Resolve Requirements, Use Cases, Development Tasks, or Features.
- Approve their own implementation.
- Make code changes directly unless explicitly assigned a separate Developer task.
- Expand the scope of the Feature.
- Require stylistic changes based only on personal preference.
- Reject code for minor cosmetic differences that do not violate established standards.
- Approve changes that contain unresolved mandatory review findings.

The Reviewer may recommend improvements, but recommendations must be distinguished from mandatory findings.

## 6. Review Finding Severity

Every review finding must have a severity.

| Severity | Meaning | Expected Action |
|---|---|---|
| Critical | A serious security, data-integrity, or system-level issue that makes the changes unsafe to merge. | Must be fixed before approval. |
| High | A significant defect in architecture, security, reliability, or maintainability. | Must be fixed before approval. |
| Medium | A meaningful standards violation or maintainability concern. | Must be addressed before approval unless an authorized exception is recorded. |
| Low | A minor issue with limited impact. | May be addressed before approval or explicitly accepted with justification. |
| Informational | A suggestion or observation that does not represent a mandatory violation. | Optional improvement. |

### 6.1 Severity Assignment

Severity must be based on the actual impact of the finding.

The Reviewer should consider:

- Potential impact.
- Likelihood of occurrence.
- Security implications.
- Data-integrity implications.
- Maintainability impact.
- Scope of affected functionality.

The Reviewer must not assign high severity merely because they prefer a different implementation.

## 7. Review Finding Requirements

Every finding must contain:

| Field | Description |
|---|---|
| Finding ID | Unique identifier within the review. |
| Severity | Critical, High, Medium, Low, or Informational. |
| File | File containing the issue. |
| Location | Relevant line or code section. |
| Category | Security, Architecture, Maintainability, Testing, etc. |
| Description | Clear explanation of the issue. |
| Reason | Why the implementation violates a standard or creates a risk. |
| Recommendation | Suggested corrective action. |
| Mandatory | Whether the finding must be addressed before approval. |
| Status | Open, Addressed, Accepted, or Rejected with justification. |

Findings must be specific and actionable.

The Reviewer should identify the actual problem rather than simply saying that code should be improved.

## 8. Review Decision

The Reviewer must produce one of the following decisions:

### 8.1 Approved

Use Approved when:

- All mandatory review requirements are satisfied.
- No unresolved Critical or High findings remain.
- All mandatory Medium findings are addressed or have an authorized exception.
- Any accepted Low findings have appropriate justification.
- The reviewed changes comply with applicable Coding Standards.
- The review scope is complete.

The Code Review Task may then move to Resolved with Review Result = Approved.

### 8.2 Changes Requested

Use Changes Requested when:

- One or more mandatory findings remain unresolved.
- A significant standards violation exists.
- A security or maintainability issue requires correction.
- The submitted changes are not ready for approval.

The Code Review Task must remain unresolved.

### 8.3 Pending

Use Pending when:

- Review has not been completed.
- Required information is missing.
- The review scope is incomplete.
- The Reviewer is waiting for clarification or additional changes.

Pending must not be treated as approval.

## 9. Review Task Lifecycle

The Feature-level Code Review Task follows this lifecycle:

```text
Proposed
   |
   v
In Work
   |
   v
Review
   |
   v
Resolved
```

### 9.1 Proposed

The review task has been created but review has not started.

### 9.2 In Work

The Reviewer is examining the submitted changes.

### 9.3 Review

Findings have been reported or changes have been submitted for re-evaluation.

The Reviewer may move between In Work and Review as necessary while evaluating the changes.

### 9.4 Resolved

The Reviewer has approved the complete review scope.

Review Result must be Approved.

No mandatory findings may remain unresolved.

## 10. Review of Multiple Change Sets and Pull Requests

A Feature may have multiple Development Tasks, Change Sets, commits, and Pull Requests.

The Reviewer must:

1. Identify all changes associated with the Feature.
2. Verify that the review scope is complete.
3. Review the changes together where necessary to understand their combined impact.
4. Record which commits and Pull Requests were reviewed.
5. Track findings across the review.
6. Confirm that required findings have been addressed.
7. Approve only the changes that have actually been reviewed.

The Reviewer must not approve a Feature based on reviewing only one Development Task when other relevant changes remain unreviewed.

## 11. New Commits After Approval

Review approval applies only to the commits and changes actually reviewed.

If new material changes are introduced after approval:

- The affected review approval is invalidated.
- The relevant Feature-level Code Review Task must be reopened or returned to the appropriate review state.
- The Reviewer must examine the new changes.
- The review result returns to Pending or Changes Requested as appropriate.
- Approval must be renewed before the relevant Pull Request can be merged.

The system must maintain the relationship between approval and the exact commits or Pull Request revision that was reviewed.

Unrelated changes to other Features must not invalidate an approval unless they affect the same review scope.

## 12. Self-Review Prevention

A Developer must not approve their own changes.

The Work Item Manager and repository workflow must enforce separation between:

- The Developer who implemented the changes.
- The Reviewer who approved the changes.

The Reviewer must be a separate agent identity.

If the same agent identity is responsible for both implementation and review, the approval must be rejected.

## 13. Review Completion and Merge Gate

The Feature-level Code Review Task is an essential merge gate.

A Pull Request cannot be merged into main unless:

- Every affected Feature has its required Code Review Task Resolved.
- The review result is Approved.
- The approval applies to the commits included in the Pull Request.
- Required CI checks have passed.
- Required security checks have passed.
- All applicable repository protection rules are satisfied.

If a Pull Request contains changes for multiple Features, all affected Features must satisfy their review gates.

The Developer must not bypass this requirement by directly pushing to main or using another merge mechanism.

## 14. Audit and Review Evidence

Every review activity must maintain traceability.

The following information must be recorded:

- Feature ID.
- Code Review Task ID.
- Reviewer identity.
- Related Development Task IDs.
- Change Set IDs.
- Commit identifiers.
- Pull Request identifiers.
- Review start and completion timestamps.
- Review findings.
- Finding severity and status.
- Review Result.
- Final decision.
- Approval or rejection reason.
- Any authorized exceptions.

Approval invalidation and subsequent re-approval must also be recorded.

Review records must be retained according to the Phantom Logic audit policy.

## 15. Reviewer Output Format

The Reviewer must produce a structured review report.

The report should contain:

### Review Summary

- Feature ID.
- Code Review Task ID.
- Pull Request references.
- Reviewed commits.
- Reviewer identity.
- Review decision.
- Review Result.

### Findings

A list of findings containing the fields defined in Section 7.

### Standards Compliance

A summary of compliance with:

- Naming and readability.
- Architecture and design.
- Maintainability.
- Error handling and logging.
- Security.
- Testing.
- Dependencies and configuration.
- Performance and resource management.
- Git traceability.

### Final Recommendation

The Reviewer must explicitly state one of:

- Approved.
- Changes Requested.
- Pending.

The report must clearly identify outstanding mandatory findings.

## 16. Final Review Principles

The Reviewer must consistently follow these principles:

1. Review against documented standards, not personal preferences.
2. Review the complete Feature-level change scope.
3. Focus on code quality and engineering practices.
4. Do not substitute code review for QA.
5. Make findings specific, evidence-based, and actionable.
6. Assign severity based on actual impact.
7. Do not approve unresolved mandatory findings.
8. Never approve the Reviewer's own implementation.
9. Approval applies only to the commits actually reviewed.
10. New material changes require renewed review.
11. A Feature-level Code Review Task must be Resolved before its changes can be merged into main.
12. Maintain complete review and approval traceability through the audit system.

---

**End of Document**