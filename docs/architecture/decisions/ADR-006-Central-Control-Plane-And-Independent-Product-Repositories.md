# ADR-006 — Central Control Plane and Independent Product Repositories

- Date: 2026-11-22
- Status: Accepted
- Decision Owner: Phantom Logic
- Decision Type: Company Architecture

## 1. Context

Phantom Logic is an autonomous AI-driven software development company.

Its objective is to operate a software development organization through specialized AI agents coordinated by a central Orchestrator.

The company requires a central platform to manage:

- Agent responsibilities and collaboration.
- Product planning and requirements.
- Architecture and technical decisions.
- Work Items and development progress.
- Quality assurance and security.
- Audit records and organizational accountability.
- Product lifecycle coordination.

However, the software products developed by Phantom Logic must remain independently maintainable, testable, versioned, and deployable.

Combining company management infrastructure and all product source code in one application repository would create unnecessary coupling.

## 2. Decision

Phantom Logic will adopt a centralized company control plane with independently maintained product repositories.

The central repository will contain the company's organizational instructions, agent configuration, shared management platform, governance, and supporting infrastructure.

Each software product will have its own independent Git repository.

The Orchestrator will coordinate product development through the central control plane and delegate implementation work to agents operating against the appropriate product repository.

## 3. Central Control Plane

The central control plane is responsible for company-wide coordination and management.

Its responsibilities include:

- Orchestrator coordination.
- Specialized agent definitions and operating instructions.
- Company rules, standards, and architecture decisions.
- Product portfolio management.
- Work Item management.
- Audit management.
- Shared development capabilities.
- Organizational documentation.
- Cross-product workflows and governance.

The central control plane is not itself a customer-facing product.

Its Python application will be maintained as a structured, installable package.

## 4. Independent Product Repositories

Each product will have its own Git repository.

A product repository is responsible for its own:

- Product requirements and specifications.
- Product-specific architecture.
- User interface and design assets.
- Application source code.
- Database schema and migrations.
- Automated tests.
- Build and deployment configuration.
- Product documentation.
- Releases and version history.
- Product-specific agent instructions.

Product repositories may use different technology stacks when justified by their requirements and approved architectural decisions.

Product source code must not be placed inside the central control-plane repository.

## 5. Product Registry and Repository Association

The central control plane will eventually maintain a Product Registry.

The registry will associate each product with its identifying information and repository location.

It will provide the foundation for coordinating development across independent repositories.

Future execution tracking may associate Work Items with:

- Product ID.
- Repository URL.
- Branch name.
- Commit SHA.
- Pull request URL.
- Build or release reference.

These associations will be implemented as separately approved enhancements.

This ADR does not authorize changes to the existing Work Item data model.

## 6. Agent Organization

OpenCode will remain the primary agent execution environment.

The existing project-level OpenCode configuration will continue to define agent modes, permissions, temperatures, and other runtime settings.

Agent prompts are stored in `.opencode/agent-prompts/` and registered through the root `opencode.jsonc` configuration. The `.opencode/agents/` directory will not be used for these prompts while JSON-based registration remains in place.

Agent definitions and reusable instructions will be organized under the approved OpenCode directory structure.

The Orchestrator remains the primary coordination agent.

Specialist agents retain their defined responsibilities and must operate within the organization's authorization, audit, and human-approval requirements.

The existing agent behavior and permissions must be preserved during repository restructuring.

## 7. Repository Organization

The central repository will use the following architectural organization:

- `.github/` — GitHub templates and CI workflows.
- `.opencode/` — OpenCode runtime configuration, JSON-configured agent prompts, plugins, skills, and commands.
- `docs/` — Company, architecture, development, standards, and Work Item documentation.
- `src/phantom_logic/` — Central control-plane Python application.
- `tests/` — Automated tests for the central application.
- Root configuration — Project instructions, OpenCode configuration, dependency management, and database migration configuration.

Only directories containing actual maintained content will be introduced.

Empty placeholder directories will not be created merely to anticipate hypothetical functionality.

## 8. Data and Audit Ownership

The central control plane remains responsible for company-wide Work Item and audit management.

The existing Work Item Management implementation, database schema, migration history, and AuditWriter security behavior must be preserved.

The Orchestrator remains the sole interface to the existing AuditWriter.

Agents performing Work Item operations must report the actual actor, action, and outcome to the Orchestrator for audit handling.

Work Item Management must not independently write audit records.

Product repositories may maintain their own product-specific operational logs where appropriate, but must not replace or bypass company-wide audit requirements.

## 9. Human Oversight

The human owner retains authority over strategic, financial, security-sensitive, and irreversible decisions.

Agent autonomy is permitted within explicitly assigned responsibilities and permissions.

Actions requiring human approval must not be treated as authorized merely because an agent recommends or initiates them.

## 10. Migration Constraints

The architecture restructuring must preserve existing functionality.

The migration must:

- Preserve all existing application behavior.
- Preserve database schema and migration history.
- Preserve Work Item authorization and lifecycle rules.
- Preserve audit integrity and existing audit records.
- Preserve OpenCode agent roles, permissions, and delegation behavior.
- Preserve GitHub issue templates and pull request validation.
- Preserve uncommitted user changes.
- Update active references when files are moved.
- Avoid modifying historical audit records.
- Run the existing automated test suites after migration stages.

File moves should use Git-aware operations wherever possible.

Business logic refactoring and new functionality are outside the scope of this restructuring.

## 11. Consequences

### Benefits

- Clear separation between company management and product development.
- Independent product versioning and release cycles.
- Reduced coupling between unrelated products.
- A reusable company-wide development platform.
- Better organization of documentation, source code, and tests.
- A foundation for autonomous coordination across multiple product repositories.

### Trade-offs

- The Orchestrator will need repository-aware coordination.
- Product Registry functionality must be implemented.
- Shared agent standards and instructions must be maintained carefully.
- Cross-repository development and testing require additional coordination.

## 12. Status

Accepted.

This decision establishes the target architecture for the Phantom Logic central repository and future product repositories.
