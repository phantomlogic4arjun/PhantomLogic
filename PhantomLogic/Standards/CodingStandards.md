# Coding Standards

**Project:** Phantom Logic  
**Document Status:** Initial Design  
**Version:** 1.0  
**Last Updated:** 21 November 2026

---

## 1. Purpose

This document defines the coding standards that all Developer agents must follow when implementing software for Phantom Logic.

The objective is to maintain a consistent codebase that is:

- Easy to understand.
- Easy to maintain.
- Secure.
- Testable.
- Reliable.
- Consistent across different Developers and projects.

These standards apply to all code produced or modified by Developer agents.

The standards are technology-independent wherever possible. Language-specific conventions may be documented separately when a project requires them.

## 2. General Principles

Every Developer must follow these principles:

1. Write code that is easy to understand rather than unnecessarily clever.
2. Prefer simple solutions over unnecessary complexity.
3. Follow established project conventions.
4. Avoid introducing unnecessary dependencies.
5. Keep implementations focused on their intended responsibilities.
6. Avoid duplicating existing functionality.
7. Consider maintainability when making implementation decisions.
8. Never introduce functionality that is outside the authorized work-item scope.
9. Do not silently ignore errors or unexpected conditions.
10. Include appropriate tests for implemented functionality.

## 3. Naming Conventions

Names must clearly communicate the purpose of the element being defined.

### 3.1 General Rules

- Use meaningful names.
- Avoid ambiguous abbreviations.
- Avoid single-character names except for conventional short-lived loop variables.
- Use consistent naming conventions within a project.
- Avoid names that are misleading or unrelated to the actual responsibility.

### 3.2 Naming by Element

| Element | Standard |
|---|---|
| Classes | Descriptive nouns |
| Functions / Methods | Descriptive verbs or verb phrases |
| Variables | Meaningful nouns or noun phrases |
| Constants | Follow the language's established constant convention |
| Interfaces | Follow the language and project convention |
| Modules / Files | Reflect their primary responsibility |
| Test Methods | Clearly describe the behavior being tested |

Developers must not introduce a different naming convention into an existing codebase without justification.

## 4. Code Organization

Code must be organized according to responsibility.

### 4.1 Separation of Concerns

- Each module, class, and function should have a clear responsibility.
- Business logic should not be unnecessarily mixed with presentation logic.
- Data access should be separated from business rules where appropriate.
- External integrations should be isolated behind suitable interfaces or abstractions when beneficial.
- Infrastructure-specific implementation details should not unnecessarily leak into business logic.

### 4.2 Function and Method Design

- Functions should perform a focused task.
- Avoid excessively long functions.
- Avoid excessive nesting.
- Avoid large conditional structures when simpler alternatives are available.
- Keep parameters and return values understandable.
- Avoid unnecessary side effects.

### 4.3 Class and Module Design

- Classes should represent a coherent responsibility.
- Avoid classes that accumulate unrelated functionality.
- Avoid unnecessary inheritance.
- Prefer composition where it produces a simpler and more maintainable design.
- Avoid circular dependencies.

### 4.4 Collection Mutability

Developers must choose collection types according to whether the data is intended to be modified.

- Prefer immutable collection types when data should not be modified in place.
- In Python, use tuples for collections that should remain unchanged after creation.
- Avoid mutable default arguments. Use appropriate default factories when mutable collections are required.
- Do not expose mutable internal collections when callers should not be able to modify them directly.
- When a collection must change, perform the change through the component responsible for validating and authorizing that change.
- Use mutable collections only when their mutability is required by the design.

Immutability must support clear ownership, predictable behavior, and controlled changes. It should not be introduced where it adds unnecessary complexity.

## 5. Readability and Maintainability

Code must be understandable to another Developer who did not write it.

Developers must:

- Use consistent formatting.
- Maintain logical grouping of related code.
- Avoid unnecessary comments that merely repeat the code.
- Add comments where reasoning or non-obvious behavior needs explanation.
- Remove obsolete and commented-out code.
- Avoid unexplained magic numbers and hard-coded values.
- Use configuration for environment-specific settings where appropriate.

Code must not be compressed or shortened at the expense of readability.

## 6. Error and Exception Handling

Errors must be handled deliberately.

Developers must:

- Handle expected failure conditions appropriately.
- Avoid silently swallowing exceptions.
- Preserve useful error information when propagating exceptions.
- Provide meaningful error messages where appropriate.
- Avoid exposing sensitive implementation details to users.
- Avoid using exceptions as ordinary control flow.
- Ensure that failures do not leave the application in an inconsistent state.

Error handling must be appropriate to the language and application architecture.

## 7. Logging

Logging must help diagnose application behavior without exposing sensitive information.

Developers must:

- Use the project's established logging framework.
- Log meaningful operational events.
- Include useful contextual information.
- Record relevant failures and exceptions.
- Avoid excessive logging.
- Never log passwords, access tokens, secrets, or other sensitive information.
- Avoid using logging as a replacement for proper error handling.

## 8. Security Standards

Security must be considered throughout implementation.

Developers must:

1. Validate untrusted input.
2. Use parameterized queries or safe data-access mechanisms.
3. Avoid hard-coded credentials and secrets.
4. Follow secure authentication and authorization practices.
5. Apply least-privilege principles.
6. Avoid exposing sensitive data in responses, logs, or error messages.
7. Use secure communication mechanisms.
8. Validate external data before using it.
9. Avoid unsafe deserialization and execution of untrusted input.
10. Follow established security practices for dependencies and third-party integrations.

Security-sensitive changes must receive the appropriate security review before release.

## 9. Dependency Management

Developers must:

- Prefer existing project dependencies when they satisfy the requirement.
- Avoid introducing dependencies without a clear reason.
- Use reputable and maintained packages.
- Avoid unnecessary dependency duplication.
- Keep dependency versions controlled through the project's dependency-management mechanism.
- Avoid introducing packages with known unresolved critical security issues.
- Document significant new dependencies and their purpose.

## 10. Configuration and Environment Management

- Environment-specific values must not be unnecessarily hard-coded.
- Secrets must be stored using approved secret-management mechanisms.
- Development, testing, staging, and production configurations must remain appropriately separated.
- Configuration changes must not unintentionally break existing environments.
- Default configurations must not expose insecure settings.

## 11. Testing Standards

Developers must provide appropriate automated tests for their changes.

Testing expectations include:

- Unit tests for important business logic.
- Integration tests for interactions between components.
- Tests for important error conditions.
- Tests for boundary conditions and invalid input.
- Regression tests when fixing defects.

Tests must:

- Be repeatable.
- Be understandable.
- Avoid unnecessary dependencies on external systems.
- Avoid depending on execution order.
- Clearly identify the behavior being tested.

A test must not be weakened or removed merely to make a failing implementation pass.

## 12. Performance and Resource Management

Developers must avoid unnecessary resource consumption.

They should:

- Avoid unnecessary database queries and repeated processing.
- Use appropriate data structures and algorithms.
- Release resources appropriately.
- Avoid memory leaks and unmanaged resource leaks.
- Avoid unnecessary network requests.
- Consider scalability where relevant to the requirement.

Optimization should be based on actual requirements and evidence rather than unnecessary complexity.

## 13. API and Integration Standards

When implementing APIs or external integrations:

- Follow established interface conventions.
- Use appropriate HTTP methods and response codes where applicable.
- Validate incoming requests.
- Handle external service failures.
- Apply appropriate timeouts and retry policies.
- Avoid exposing internal implementation details.
- Maintain backward compatibility unless a breaking change is explicitly authorized.
- Document significant interface changes.

## 14. Documentation

Developers must update relevant documentation when implementation changes affect:

- Public interfaces.
- Configuration.
- Deployment procedures.
- Architecture.
- Operational behavior.
- Important business rules.

Documentation should be concise, accurate, and consistent with the actual implementation.

## 15. Git and Change Management

All changes must follow the Phantom Logic development workflow.

Developers must:

- Work on authorized Development Tasks.
- Associate Change Sets and commits with their Development Tasks.
- Provide meaningful commit messages.
- Keep commits focused on related changes.
- Avoid including unrelated modifications.
- Work on the shared `dev` branch.
- Submit changes through Pull Requests.
- Never push directly to `main`.
- Never bypass mandatory review and CI gates.

Every code change must be traceable to its originating work item.

## 16. Scope Control

Developers must implement only authorized work.

If an implementation requires changes outside the approved scope:

1. Explain why the additional work is necessary.
2. Identify the affected Requirements.
3. Notify the Product Manager.
4. Obtain authorization through the appropriate Change Request or work-item process.
5. Implement the additional work only after authorization.

Developers must not independently expand requirements or introduce unrelated refactoring.

## 17. Existing Codebase Compatibility

When modifying existing software:

- Follow the established architecture unless a change is authorized.
- Maintain existing conventions.
- Avoid unnecessary large-scale refactoring.
- Preserve existing functionality unless explicitly changing it.
- Identify potential compatibility issues.
- Avoid introducing breaking changes without authorization.

Existing code that does not fully meet these standards should not automatically be rewritten as part of unrelated work.

## 18. Exceptions to Standards

A Developer may occasionally need to deviate from a standard because of technical constraints.

In such cases:

- The deviation must be justified.
- The affected code must be identified.
- The reason must be documented.
- The deviation must be brought to the Reviewer's attention.
- Approval must be obtained where the deviation affects security, architecture, or maintainability significantly.

Standards must not be bypassed silently.

## 19. Compliance

All Developer agents are expected to follow this document.

The Reviewer uses this document together with `CodeReviewGuidelines.md` when evaluating submitted changes.

The Work Item Manager and Orchestrator may use compliance results as part of development workflow enforcement.

---

**End of Document**