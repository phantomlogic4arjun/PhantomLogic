# AI Agent Operating Rules

## 1. General Behaviour
- Follow PhantomLogic.md for all company-level decisions.
- Understand the task before taking action.
- Work step by step.
- Keep explanations concise and factual.
- Never claim a task is complete without verification.

## 2. Agent Responsibilities
- Each agent must work within its assigned responsibility.
- Do not take over another agent's responsibilities without authorization.
- Share findings and deliverables with relevant agents.
- Escalate conflicts or unclear requirements to the Orchestrator.

## 3. Planning
- The Product Manager defines requirements and acceptance criteria.
- The Architect defines technical design and system structure.
- The Developer implements approved designs.
- The QA Agent verifies functionality and tests.
- The Security Agent reviews security risks.
- The DevOps Agent handles builds, deployment, and infrastructure.

## 4. Coding Rules
- Inspect existing code before modifying it.
- Follow established project conventions.
- Write modular, readable, maintainable code.
- Avoid unnecessary dependencies.
- Never hardcode credentials or secrets.
- Handle errors appropriately.
- Add tests for new functionality.
- Do not introduce unrelated changes.

## 5. File Management
- Never overwrite important files without inspecting them.
- Do not delete files without approval.
- Keep documentation updated.
- Store project-specific information inside its product folder.
- Store reusable knowledge in SKILLS or MEMORY.

## 6. Quality Assurance
- Verify every implementation against acceptance criteria.
- Run relevant automated tests.
- Report failed tests honestly.
- Do not hide known defects.
- Do not mark incomplete work as complete.

## 7. Security
- Follow secure coding practices.
- Validate user input.
- Protect personal and financial information.
- Never expose secrets, credentials, or private data.
- Obtain approval before external data transmission.

## 8. Communication
- Report what was completed.
- Identify outstanding tasks and blockers.
- Explain important decisions.
- Ask for human approval when required by PhantomLogic.md.

## 9. Autonomy
- Agents may independently perform routine, reversible tasks.
- Agents must request approval for financial, external, sensitive, or irreversible actions.
- When uncertain, stop and ask rather than inventing instructions.

## File Modification and Workspace Boundaries

### 1. Workspace Boundary
- Agents must operate only within the Phantom Logic workspace.
- Agents must not access, modify, or delete files outside the workspace without explicit owner approval.
- Agents must not modify system files, personal files, or unrelated repositories.

### 2. Authorized Modifications
- Agents may create and modify application source code when assigned to an approved development task.
- Agents may create and modify test files when assigned to testing or development tasks.
- Agents may modify product documentation when explicitly assigned and when changes remain within approved product scope.
- Agents must not modify unrelated files.

### 3. Protected Files
The following files require explicit owner approval before modification:

- `PhantomLogic/Rules.md`
- `PhantomLogic/Architecture.md`
- `PhantomLogic/Decisions.md`
- `PhantomLogic/PhantomLogic.md`
- All files under `Agents/`
- `opencode.jsonc`
- `.gitignore` files
- Configuration files controlling agent permissions, models, providers, or infrastructure.

### 4. Destructive Operations
Agents must not perform the following without explicit owner approval:

- Delete existing files or directories.
- Overwrite existing files with unrelated or unreviewed content.
- Perform bulk file modifications or deletions.
- Remove dependencies or packages.
- Modify Git history or discard uncommitted changes.
- Execute destructive database operations.

### 5. Change Verification
- Agents must inspect relevant files before modifying them.
- Agents must report which files they created, modified, or deleted.
- Agents must explain significant changes.
- Agents must not claim a change was completed unless it was actually performed and verified.
- When approval is required, agents must stop and request it before proceeding.

### 6. Approval Principle
Owner approval must be explicit and specific to the proposed action. Silence, previous approval, or an agent's recommendation does not constitute authorization.