# Company Architecture

## 1. Overall Structure

Autonomous Software Labs operates through specialized AI agents coordinated by an Orchestrator.

## 2. Core Components

### AI Runtime
- Ollama runs local language models.
- OpenCode provides the coding agent environment.

### Orchestration
- Orchestrator coordinates agents and workflows.
- Python will provide custom orchestration when required.
- n8n handles workflow automation and integrations.

### Specialized Agents
- Product Manager: Requirements and product planning.
- Architect: Technical design and architecture.
- Designer: UI/UX and user experience.
- Developer: Application development.
- QA: Testing and quality assurance.
- Security: Security reviews.
- DevOps: Build and deployment.

## 3. Development Architecture

Preferred application stack:

- Frontend: React + TypeScript + Vite.
- Backend: Python + FastAPI.
- Database: SQLite initially.
- Charts: Recharts.
- Version control: Git.

## 4. Knowledge Management

- COMPANY: Organization-wide instructions.
- AGENTS: Agent definitions and responsibilities.
- SKILLS: Reusable capabilities and procedures.
- WORKFLOWS: Repeatable business processes.
- MEMORY: Persistent knowledge and lessons.
- PRODUCTS: Individual product source code and documentation.
- INFRASTRUCTURE: Shared infrastructure and configuration.

## 5. Design Principles

- Local-first execution.
- Modular architecture.
- Minimal infrastructure.
- Reusable components.
- Secure data handling.
- Human approval for sensitive actions.

## 6. Evolution

The architecture may evolve as the company develops more products. Significant changes must be documented in DECISIONS.md.