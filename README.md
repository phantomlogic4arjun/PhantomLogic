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

The repository contains Phantom Logic's central control plane, company documentation, agent configuration, and shared platform code.

```text
Autonomous Lab/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── .opencode/
│   ├── agent-prompts/
│   ├── plugins/
│   ├── package.json
│   └── package-lock.json
├── docs/
│   ├── architecture/
│   │   ├── decisions/
│   │   └── system/
│   ├── company/
│   ├── development/
│   ├── standards/
│   └── work-items/
├── src/
│   └── phantom_logic/
│       ├── audit/
│       ├── database/
│       │   ├── migrations/
│       │   │   └── versions/
│       │   ├── models/
│       │   └── repositories/
│       └── work_items/
│           ├── interfaces/
│           ├── managers/
│           ├── models/
│           ├── rules/
│           └── services/
├── tests/
│   ├── audit/
│   ├── database/
│   └── work_items/
├── .env.example
├── .gitignore
├── AGENTS.md
├── alembic.ini
├── opencode.jsonc
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Folder Responsibilities

**AGENTS.md**

Contains repository-wide instructions for AI agents, including repository boundaries, authoritative documentation, change management, security requirements, Work Item coordination, audit responsibilities, and human approval requirements.

**.github/**

Contains GitHub repository configuration, issue templates, and automated workflows. Continuous Integration installs the Python project and runs the automated test suite.

**.opencode/**

Contains OpenCode-specific configuration and resources:

- `agent-prompts/` — Detailed operating instructions for the Orchestrator and specialist agents.
- `plugins/` — Custom OpenCode plugins, including the Work Item integration.
- `package.json` and `package-lock.json` — Dependencies for OpenCode plugins and supporting tooling.

**docs/**

Contains the company's maintained documentation:

- `company/` — Company identity, mission, and organizational rules.
- `architecture/` — System architecture and architecture decision records.
- `development/` — Development history and project evolution.
- `standards/` — Coding, code review, and platform-independence standards.
- `work-items/` — Work Item management documentation, implementation references, and state transition rules.

**src/phantom_logic/**

Contains the shared Python implementation of the Phantom Logic control plane.

- `audit/` — Central audit writer and audit functionality.
- `database/` — Database configuration, SQLAlchemy models, repositories, and Alembic migrations.
- `work_items/` — Work Item interfaces, managers, models, business rules, and services.

**tests/**

Contains the automated Python test suite, organized to reflect the application modules:

- `audit/` — Audit writer and audit contract tests.
- `database/` — Database repository tests.
- `work_items/` — Work Item model, interface, manager, rule, service, and integration tests.

### Root Configuration Files

- `AGENTS.md` — Repository-wide instructions for AI agents.
- `opencode.jsonc` — Registers the Orchestrator and specialist agents, their operating modes, permissions, and prompt paths.
- `pyproject.toml` — Defines the Python project, runtime dependencies, build configuration, and package settings. This is the authoritative Python dependency configuration.
- `requirements.txt` — Provides a compatibility entry point for pip-based installation workflows. Project dependencies are defined in `pyproject.toml`.
- `.env.example` — Provides the names of environment variables required for local database configuration without including credentials.
- `.gitignore` — Excludes local environments, secrets, caches, and generated files.
- `alembic.ini` — Configures database migration tooling.
- `README.md` — Introduces Phantom Logic, its architecture, development setup, and operating principles.

## 5. Technology Stack

Phantom Logic follows a local-first approach wherever practical, with cloud services used when they provide meaningful improvements.

### Central Control Plane

| Component | Technology |
|---|---|
| AI Agent Runtime | OpenCode |
| Local AI Models | Ollama |
| Cloud AI Models | External AI provider APIs |
| Control Plane | Python |
| Database | PostgreSQL |
| Database Access | SQLAlchemy |
| Database Migrations | Alembic |
| Plugin Runtime | OpenCode plugins, TypeScript, and Bun |
| Version Control | Git and GitHub |
| Workflow Automation | n8n |

### Product Development Technologies

Individual products may use technologies appropriate to their requirements and approved architecture. Potential technologies include React, TypeScript, Vite, FastAPI, and other suitable frameworks and platforms.

### Development Platforms

Phantom Logic is being developed toward platform independence.

- **macOS** — Current development environment and validated baseline for the existing Python test workflow.
- **Linux** — Target platform undergoing progressive compatibility implementation and validation.
- **Windows** — Target platform undergoing progressive compatibility implementation and validation. WSL2 may be used as an intermediate development environment; it does not establish native Windows support.

A platform must not be described as fully supported until its required runtime, installation, database, integration, and automated testing requirements have been validated.

Technology selections for individual products may differ based on approved architectural decisions.

## 6. Development Setup

This section describes how to prepare a local development environment.

### Prerequisites

- Python 3.11 or later.
- Git.
- PostgreSQL.
- OpenCode and Bun for agent-runtime and plugin development.

Install the required tools using the official installation instructions for your operating system.

### Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

Replace `<repository-url>` with the actual Git repository URL.

### macOS and Linux

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project and its dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

### Windows PowerShell

Create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project and its dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell prevents virtual environment activation, follow the appropriate Python and PowerShell guidance for your machine rather than changing system-wide security settings without authorization.

### Database Configuration

Phantom Logic uses PostgreSQL as its central database.

Create a local environment configuration file from the example:

**macOS and Linux**

```bash
cp .env.example .env
```

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

Update `.env` with the connection details for the local PostgreSQL instance.

The example configuration identifies the required settings:

- `PHANTOM_LOGIC_DB_HOST`
- `PHANTOM_LOGIC_DB_PORT`
- `PHANTOM_LOGIC_DB_NAME`
- `PHANTOM_LOGIC_DB_USER`
- `PHANTOM_LOGIC_DB_PASSWORD`

The PostgreSQL database, schemas, roles, permissions, and migrations must be prepared according to the project's database architecture and migration instructions before running database-dependent operations.

Never commit `.env` or expose database credentials in source code, logs, or documentation.

## 7. Running Tests

Run the automated test suite from the repository root after activating the virtual environment and installing the project.

```bash
python -m unittest discover -s tests -p 'Test*.py' -v
```

Tests that interact with PostgreSQL require a correctly configured and accessible database.

Use the same test command across supported platforms. Platform-specific setup or integration requirements must be documented in the relevant development and platform-independence documentation.

## 8. Software Development Lifecycle

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

## 9. Autonomy and Human Oversight

Phantom Logic is designed to operate autonomously while maintaining appropriate human control.

Agents may independently perform routine, reversible tasks within their assigned responsibilities.

Human approval is required for actions such as:

- Spending money or purchasing subscriptions.
- Public product releases and deployments.
- Accessing sensitive external accounts.
- Deleting important data.
- Making irreversible business or technical changes.

Agents must never claim that work is completed, tested, or verified without supporting evidence.

## 10. First Product

The first planned product is the **Personal Finance Tracker**.

The initial objective is to develop a local-first personal finance application with capabilities including:

- Income and expense tracking.
- Transaction categorization.
- Budget management.
- Monthly financial summaries.
- Charts and reports.
- CSV transaction imports.

The product will serve as the initial end-to-end test of Phantom Logic's autonomous software development organization.

## 11. Platform Independence

Platform independence is a core engineering objective for Phantom Logic.

The project aims to maintain one codebase and one governance model across macOS, Linux, and Windows, avoiding unnecessary operating-system-specific implementations.

Platform compatibility must be implemented and validated progressively. Development on one operating system does not automatically establish support on another.

All development and review work involving platform compatibility must follow:

`docs/standards/PlatformIndependence.md`

## 12. Guiding Principles

Phantom Logic operates according to the following principles:

- Autonomy with accountability.
- Clear responsibilities and separation of concerns.
- Human oversight for critical decisions.
- Local-first development wherever practical.
- Security and privacy by design.
- Simple, maintainable, and reusable solutions.
- Evidence-based testing and quality assurance.
- Controlled operational costs.
- Platform independence through deliberate engineering and validation.
- Documented decisions and continuous improvement.

---

**Phantom Logic — An autonomous AI-driven software development company.**
