# Phantom Logic — Company Architecture

## 1. Overall Structure

Phantom Logic operates through specialized AI agents coordinated by an Orchestrator.

The human owner provides product ideas, approves important decisions, and oversees the organization.

The Orchestrator manages the complete product lifecycle, from initial idea to product delivery.

## 2. Core Components

### AI Runtime

- Ollama runs local language models.
- OpenCode provides the AI agent environment.
- Cloud AI providers may be used when approved and configured.

### Orchestration

- Orchestrator coordinates agents and product workflows.
- Python may provide custom orchestration when required.
- n8n handles workflow automation and integrations.

### Specialized Agents

- Product Manager: Requirements and product planning.
- Architect: Technical design and architecture.
- Designer: UI/UX and user experience.
- Developer: Application development.
- QA: Testing and quality assurance.
- Security: Security reviews.
- DevOps: Build and deployment.

## 3. Idea-to-Product Lifecycle

Every new product must follow a defined lifecycle.

### Stage 1: Idea Intake

Owner provides a product idea or business problem to the Orchestrator.

The Orchestrator must:

- Understand the problem and intended outcome.
- Identify target users.
- Identify constraints and assumptions.
- Ask questions when essential information is missing.
- Create an initial product opportunity summary.

Deliverable: Idea Brief.

### Stage 2: Product Discovery

The Orchestrator assigns the Product Manager to:

- Research and clarify the problem.
- Identify users and use cases.
- Define product goals.
- Identify functional and non-functional requirements.
- Evaluate MVP scope.
- Define measurable success criteria.

Deliverable: Product Requirements Document (PRD).

### Stage 3: Solution Design

The Orchestrator coordinates:

- Architect: System architecture, technology choices, database, APIs, and technical risks.
- Designer: User journeys, screens, interactions, and design system.
- Security: Initial security, privacy, and data-protection assessment.

Deliverables:

- Architecture Document.
- Technical Design.
- UX/UI Specification.
- Initial Security Assessment.

### Stage 4: Product Plan and Approval

The Orchestrator consolidates the discovery and design deliverables.

It prepares:

- Final MVP scope.
- Feature breakdown.
- Development milestones.
- Task dependencies.
- Estimated resource and infrastructure requirements.
- Identified risks.
- Acceptance criteria.

The Orchestrator presents the plan to the owner.

**Approval Gate 1 — Product Approval**

Development must not begin until the owner approves the proposed product scope and plan.

Changes to approved scope that materially affect cost, schedule, architecture, or product direction must be presented for approval.

### Stage 5: Development

After approval:

- Orchestrator breaks the approved scope into development tasks.
- Developer implements features incrementally.
- Architect provides technical guidance when required.
- Designer clarifies UX/UI requirements.
- Security reviews implementation where appropriate.
- Orchestrator tracks dependencies and progress.

Each task must reference its requirements and acceptance criteria.

### Stage 6: Testing and Validation

The Orchestrator coordinates:

- QA: Functional, integration, regression, and acceptance testing.
- Security: Security and privacy validation.
- Developer: Fixes defects and implements required changes.

Failed tests and unresolved critical security issues must be addressed before release.

Deliverables:

- Test Results.
- Defect Report.
- Security Review.
- Release Readiness Assessment.

### Stage 7: Release Approval

The Orchestrator verifies that:

- Approved features are implemented.
- Acceptance criteria are satisfied.
- Required tests have passed.
- Critical security issues are resolved.
- Documentation is complete.
- Release and deployment plans are ready.

**Approval Gate 2 — Release Approval**

The owner must approve public release, production deployment, or other externally visible release actions.

### Stage 8: Deployment and Delivery

After the required approval:

- DevOps prepares and executes the deployment.
- Developer supports deployment-related fixes.
- QA verifies the deployed product.
- Orchestrator confirms delivery and reports the outcome.

Deliverables:

- Working Product.
- Deployment Documentation.
- User Documentation.
- Final Delivery Report.

### Stage 9: Maintenance and Improvement

After delivery:

- Collect feedback and identify defects.
- Evaluate enhancement requests.
- Prioritize improvements with the Product Manager.
- Follow the same approval process for material scope changes.
- Record lessons learned and update product documentation.

## 4. Approval and Autonomy Boundaries

The Orchestrator may independently:

- Coordinate agents.
- Assign and prioritize routine tasks.
- Prepare plans and recommendations.
- Approve routine, reversible implementation decisions.
- Request revisions and fixes.
- Track progress and report results.

The Orchestrator must obtain owner approval before:

- Starting development of a newly proposed product.
- Making material changes to approved scope.
- Spending money or purchasing subscriptions.
- Using paid services beyond approved budgets.
- Publishing or releasing products publicly.
- Accessing sensitive external accounts.
- Performing irreversible or destructive actions.

Approval must be explicit. Silence must never be treated as approval.

## 5. Knowledge Management

- PhantomLogic/: Company-wide mission, rules, architecture, and decisions.
- Agents/: Agent definitions and responsibilities.
- Skills/: Reusable capabilities and procedures.
- Workflows/: Repeatable business processes.
- Memory/: Persistent knowledge and lessons.
- Products/: Individual product source code and documentation.
- Infrastructure/: Shared infrastructure and configuration.

Each product must maintain its own requirements, architecture, development status, testing records, and release documentation.

## 6. Development Architecture

Preferred application stack:

- Frontend: React + TypeScript + Vite.
- Backend: Python + FastAPI.
- Database: SQLite initially.
- Charts: Recharts.
- Version control: Git.

Technology choices may vary based on product requirements and must be documented.

## 7. Design Principles

- Local-first execution where practical.
- Modular architecture.
- Minimal infrastructure.
- Reusable components.
- Secure data handling.
- Human approval for sensitive actions.
- Verifiable work and transparent reporting.
- Clear separation of responsibilities between agents.

## 8. Evolution

The architecture may evolve as Phantom Logic develops more products.

Significant architectural changes must be documented in Decisions.md.
