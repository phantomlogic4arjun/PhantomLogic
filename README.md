# Phantom Logic

## 1. About Phantom Logic

**Phantom Logic is an autonomous AI-driven software development company.**

The objective is to build and operate a software development organization powered by specialized AI agents that collaborate to plan, design, develop, test, secure, and deliver software products.

Instead of relying on a single AI assistant to perform every task, Phantom Logic follows an organizational model in which each AI agent has a defined role, responsibilities, and operating instructions.

A human owner provides strategic direction, approves important decisions, and oversees the organization. AI agents handle routine activities and coordinate their work with one another.

## 2. Vision and Mission

### Vision

Build a self-operating software company capable of independently developing, maintaining, and delivering useful software products with minimal human intervention.

### Mission

- Build specialized AI agents that function as members of a software development organization.
- Establish clear responsibilities, workflows, and communication between agents.
- Automate the software development lifecycle.
- Develop practical, high-quality software products.
- Minimize operational costs through local AI models and carefully selected cloud AI services.
- Maintain human oversight for financial commitments, sensitive operations, and irreversible decisions.

## 3. Organizational Structure

Phantom Logic operates through a central Orchestrator supported by seven specialized agents.

| Agent | Primary Responsibility |
|---|---|
| Orchestrator | Coordinates agents, manages projects, and oversees delivery. |
| Product Manager | Defines product requirements, user stories, priorities, and acceptance criteria. |
| Architect | Designs application architecture, databases, APIs, and technical solutions. |
| Designer | Defines UI/UX, wireframes, layouts, and design guidelines. |
| Developer | Implements application functionality and maintains code quality. |
| QA Engineer | Plans and executes tests and verifies product quality. |
| Security Engineer | Reviews application security and identifies vulnerabilities. |
| DevOps Engineer | Manages development environments, builds, deployments, and infrastructure. |

### Agent Operating Model

- The Orchestrator is the primary coordination agent.
- Specialist agents operate as subagents.
- Each agent follows its own detailed instructions.
- Agents collaborate through delegated tasks and documented deliverables.
- The Orchestrator reviews specialist outputs and coordinates the overall workflow.
- The human owner retains authority over important business and operational decisions.

## 4. Repository Structure

The repository is organized to separate company governance, agent responsibilities, products, infrastructure, and reusable knowledge.

```text
Autonomous Lab/
│
├── README.md
│
├── Agents/
│   ├── Orchestrator/
│   ├── Product Manager/
│   ├── Architect/
│   ├── Designer/
│   ├── Developer/
│   ├── QA/
│   ├── Security/
│   └── Devops/
│
├── PhantomLogic/
│   ├── PhantomLogic.md
│   ├── Rules.md
│   ├── Architecture.md
│   └── Decisions.md
│
├── Products/
│   └── Personal Finance Tracker/
│
├── Infrastructure/
│
├── Memory/
│
├── Skills/
│
├── Workflows/
│
├── .opencode/
│
├── opencode.jsonc
│
└── .gitignore
```

### Folder Responsibilities

**Agents/**

Contains detailed role definitions and operating instructions for all AI agents. Each agent has its own responsibilities, workflow, collaboration rules, and definition of done.

**PhantomLogic/**

Contains the company's central documentation and governance:

- `PhantomLogic.md` — Company identity, mission, principles, technology preferences, and definition of done.
- `Rules.md` — Organization-wide rules governing agent behavior, permissions, collaboration, and safety.
- `Architecture.md` — Overall organizational and technical architecture.
- `Decisions.md` — Record of significant decisions and their rationale.

**Products/**

Contains individual software product projects developed by Phantom Logic. Each product maintains its own requirements, architecture, design, source code, tests, and documentation as appropriate.

**Infrastructure/**

Contains infrastructure-related configurations, environment setup, build tools, deployment resources, and supporting technical components.

**Memory/**

Provides persistent organizational and project knowledge that can be reused by agents across tasks and projects.

**Skills/**

Contains reusable capabilities, procedures, and specialized instructions that can be used by agents when performing particular tasks.

**Workflows/**

Contains automated workflows that coordinate processes, agents, and supporting tools.

**.opencode/**

Contains OpenCode-specific project configuration and supporting resources.

**opencode.jsonc**

The project-level OpenCode configuration. Registers the primary Orchestrator and all specialist agents, including their operating modes and references to their detailed instruction files.

## 5. Technology Stack

Phantom Logic follows a local-first approach wherever practical, with cloud services used when they provide meaningful improvements.

| Component | Technology |
|---|---|
| AI Agent Runtime | OpenCode |
| Local AI Models | Ollama |
| Cloud AI Models | External AI provider APIs |
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | SQLite initially |
| Version Control | Git and GitHub |
| Workflow Automation | n8n |
| Development Environment | macOS, Visual Studio Code |

Technology selections for individual products may differ based on approved architectural decisions.

## 6. Software Development Lifecycle

Phantom Logic follows an Orchestrator-led development process.

1. **Idea and Discovery** — Understand the business problem and intended users.
2. **Requirements** — Product Manager defines the PRD, features, priorities, and acceptance criteria.
3. **Architecture** — Architect defines the technical design, database, APIs, and implementation guidelines.
4. **UI/UX Design** — Designer prepares user journeys, wireframes, and interface specifications.
5. **Development** — Developer implements the approved requirements and architecture.
6. **Quality Assurance** — QA validates functionality, tests edge cases, and reports defects.
7. **Security Review** — Security evaluates vulnerabilities, data protection, and application security.
8. **DevOps and Delivery** — DevOps prepares the environment, build, deployment, and operational documentation.
9. **Final Review** — Orchestrator reviews deliverables and reports the outcome to the human owner.

Not every task requires every specialist. The Orchestrator determines which agents are necessary based on the task.

## 7. Autonomy and Human Oversight

Phantom Logic is designed to operate autonomously while maintaining appropriate human control.

Agents may independently perform routine, reversible tasks within their assigned responsibilities.

Human approval is required for actions such as:

- Spending money or purchasing subscriptions.
- Public product releases and deployments.
- Accessing sensitive external accounts.
- Deleting important data.
- Making irreversible business or technical changes.

Agents must never claim that work is completed, tested, or verified without supporting evidence.

## 8. First Product

The first planned product is the **Personal Finance Tracker**.

The initial objective is to develop a local-first personal finance application with capabilities including:

- Income and expense tracking.
- Transaction categorization.
- Budget management.
- Monthly financial summaries.
- Charts and reports.
- CSV transaction imports.

The product will serve as the initial end-to-end test of Phantom Logic's autonomous software development organization.

## 9. Guiding Principles

Phantom Logic operates according to the following principles:

- Autonomy with accountability.
- Clear responsibilities and separation of concerns.
- Human oversight for critical decisions.
- Local-first development wherever practical.
- Security and privacy by design.
- Simple, maintainable, and reusable solutions.
- Evidence-based testing and quality assurance.
- Controlled operational costs.
- Documented decisions and continuous improvement.

---

**Phantom Logic — An autonomous AI-driven software development company.**