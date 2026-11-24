# Agentic Engineering — Everyday Technical Terminology

A quick reference for understanding the terminology used when building, configuring, and working with AI agents.

## 1. Agents and instructions

**Agent**  
An AI-powered worker designed to perform tasks, make decisions, and use tools to achieve an objective.

**Subagent**  
A specialized agent created or delegated a task by another agent. For example, a development agent might delegate code review to a QA agent.

**Orchestrator**  
The central coordinator responsible for assigning work, managing agents, tracking progress, and coordinating results.

**System Prompt**  
The primary set of instructions defining how an AI model should behave.

**Agent Instructions**  
Instructions that define an agent's role, responsibilities, boundaries, and expected behavior.

**Rules**  
Mandatory guidelines that agents must follow when performing work. These can cover coding standards, security, architecture, and project governance.

**AGENTS.md**  
A commonly used instruction file that provides coding agents with project-specific guidance, conventions, and working instructions.

**Context**  
The information currently available to an agent, including instructions, conversation history, files, and tool results.

**Context Window**  
The maximum amount of information a model can process in a single interaction.

**Tokens**  
The small units of text that language models process. Model context limits and usage costs are often measured in tokens.

**Context Compaction**  
The process of summarizing or reducing conversation context when it becomes too large, while retaining important information.

## 2. Agent capabilities and reusable components

**Skill**  
A reusable package of instructions, knowledge, and sometimes supporting resources that teaches an agent how to perform a particular task. For example, a database migration skill can guide an agent through safely creating and validating migrations.

**Tool**  
An executable capability an agent can use to interact with something outside the language model, such as a terminal, database, API, or file system.

**Function Calling**  
A mechanism that allows an AI model to request execution of a predefined function using structured arguments.

**MCP (Model Context Protocol)**  
A standard that allows AI applications to connect with external tools, services, and data sources through a common protocol.

**MCP Server**  
A service that exposes tools, resources, or other capabilities through the MCP protocol.

**MCP Client**  
The application or agent that connects to an MCP server and uses the capabilities it exposes.

**Plugin**  
An extension that adds functionality to an AI development environment. Depending on the platform, plugins can provide tools, commands, event handlers, or integrations.

**Command**  
A predefined instruction or action that a user or agent can invoke. Commands often provide shortcuts for recurring workflows.

**Slash Command**  
A command invoked using a forward slash, such as `/review`, `/test`, or `/commit`.

**Hook**  
A function or script triggered automatically when a particular event occurs. For example, a hook can run validation before an agent finishes a task.

**Workflow**  
A sequence of connected tasks and operations designed to accomplish a particular objective.

**Template**  
A reusable structure for generating files, instructions, prompts, or other artifacts.

## 3. How agents execute work

**Task Decomposition**  
Breaking a large objective into smaller tasks that are easier to assign, execute, and verify.

**Planning**  
Determining the steps required to accomplish an objective before executing them.

**Execution Loop**  
The repeated cycle of observing, reasoning, selecting an action, executing it, and evaluating the result.

**Delegation**  
Assigning a task to another agent or execution process.

**Handoff**  
Transferring responsibility, context, and task information from one agent to another.

**Tool Call**  
An actual request made by an agent to execute a tool.

**Tool Result**  
The output returned after a tool executes.

**Autonomous Execution**  
Allowing an agent to perform a sequence of tasks without requiring approval at every step.

**Human-in-the-Loop (HITL)**  
A process in which a human reviews or approves specific actions before the agent proceeds.

**Retry**  
Attempting an operation again after a failure or unsuccessful result.

**Fallback**  
An alternative approach used when the primary model, tool, or operation fails.

**State**  
The current condition of an agent or task, including its status, progress, and relevant information.

**Shared State**  
Information accessible to multiple agents so they can coordinate their work.

## 4. AI model terminology

**LLM (Large Language Model)**  
An AI model trained to understand and generate language. Examples include GPT, Claude, and Gemini.

**Model Provider**  
The organization or service providing access to an AI model.

**Inference**  
The process of using a trained model to generate an output from an input.

**Temperature**  
A model setting that influences the randomness of generated responses. Lower values generally produce more predictable outputs.

**Model Routing**  
Selecting which model should handle a particular task based on capability, cost, speed, or other requirements.

**Structured Output**  
An AI response constrained to a defined format, such as JSON.

**JSON Schema**  
A specification describing the expected structure, data types, and validation rules for JSON data.

**Embedding**  
A numerical representation of information that captures aspects of its meaning.

**Vector Database**  
A database designed to store and search embeddings using similarity.

**RAG (Retrieval-Augmented Generation)**  
A technique in which an AI retrieves relevant external information and uses it to generate a response.

**Fine-Tuning**  
Further training an existing model on specialized data to influence its behavior or capabilities.

## 5. Coding and software engineering terminology

**Repository (Repo)**  
The project directory and its version-controlled history, usually managed using Git.

**Version Control**  
A system for tracking changes to source code and other project files.

**Git Branch**  
An independent line of development used to work on changes without directly modifying another branch.

**Commit**  
A recorded snapshot of changes in a Git repository.

**Pull Request (PR)**  
A proposal to merge changes from one branch into another, usually after review.

**Merge**  
Combining changes from different branches.

**Merge Conflict**  
A situation where Git cannot automatically reconcile competing changes.

**Dependency**  
An external package or library that a project needs to function.

**Package Manager**  
A tool used to install, update, and manage software dependencies. Examples include npm, pip, and NuGet.

**Environment Variable**  
A configuration value supplied to an application through its execution environment rather than hardcoded into the source.

**Virtual Environment**  
An isolated Python environment that keeps project dependencies separate from other Python installations.

**Configuration**  
Settings that control how an application or agent operates.

**Refactoring**  
Improving the internal structure of code without intentionally changing its external behavior.

**Technical Debt**  
The future maintenance cost created by shortcuts, compromises, or design decisions.

**Regression**  
A situation where a previously working feature stops working after a change.

**Unit Test**  
A test that verifies a small, isolated piece of functionality.

**Integration Test**  
A test that verifies that multiple components work correctly together.

**End-to-End (E2E) Test**  
A test that validates a complete workflow from beginning to end.

**CI/CD**  
Continuous Integration and Continuous Delivery/Deployment. Automated processes for building, testing, and delivering software changes.

**Pipeline**  
A sequence of automated steps, such as installing dependencies, running tests, and building an application.

## 6. Reliability, security, and governance

**Guardrails**  
Rules and restrictions that prevent agents from taking unauthorized or unintended actions.

**Permissions**  
The specific actions an agent is allowed to perform.

**Least Privilege**  
Giving an agent only the permissions it needs to perform its assigned responsibilities.

**Sandbox**  
An isolated environment where code or agent actions can be executed with limited access to the surrounding system.

**Approval Gate**  
A checkpoint where a human or another authorized component must approve an action before execution continues.

**Validation**  
Checking whether an input, operation, or result meets defined requirements.

**Verification**  
Confirming that a task was completed correctly and produced the expected outcome.

**Audit Trail**  
A record of who performed an action, what happened, and the resulting outcome.

**Observability**  
The ability to understand system behavior through logs, metrics, traces, and other diagnostic information.

**Logging**  
Recording events and information about application or agent execution.

**Trace**  
A record of the steps taken during an execution, often including model calls, tool calls, and their results.

**Idempotency**  
A property that ensures repeating an operation does not create unintended additional effects.

**Error Handling**  
The mechanisms used to detect, report, and recover from failures.

**Evaluation (Evals)**  
A systematic way of measuring an agent's performance, accuracy, and reliability.

## 7. Common terms in agentic development environments

These are especially useful when working with AI coding assistants and agent frameworks.

| Term | Meaning |
|---|---|
| CLI | Command-Line Interface; interacting with software through terminal commands |
| IDE | Integrated Development Environment; software used to write and manage code |
| REPL | Read-Eval-Print Loop; an interactive environment for executing code |
| TUI | Text User Interface; a terminal-based interactive interface |
| SDK | Software Development Kit; tools and libraries for integrating with a platform |
| API | Application Programming Interface; a way for software systems to communicate |
| Webhook | An HTTP callback triggered by an event |
| Event-driven | An architecture where actions are triggered by events |
| Async | Asynchronous execution that allows other work to proceed while an operation is pending |
| Queue | A mechanism for holding tasks until they can be processed |
| Worker | A process that picks up and executes assigned tasks |
| Scheduler | A component that determines when tasks should run |
| Rate Limit | A restriction on how frequently a service can be called |
| Timeout | The maximum time allowed for an operation before it is stopped |
| Cache | Temporarily stored information used to avoid repeated work |
| Persistence | Retaining data beyond the lifetime of a process or session |

---

## A simple mental model

When working with an agentic system, think of the components this way:

- **Agent:** Who does the work?
- **Orchestrator:** Who coordinates the work?
- **Instructions and Rules:** What must the agent follow?
- **Skills:** How does the agent know how to perform specialized work?
- **Tools:** What can the agent use?
- **MCP:** How can external capabilities be connected?
- **Hooks:** What should happen automatically when an event occurs?
- **Memory and Context:** What information can the agent use?
- **Workflow:** What sequence of activities should happen?
- **Guardrails and Permissions:** What is the agent allowed to do?
- **Evaluation and Audit:** How do we know the work was done correctly and responsibly?

The important thing is not to memorize every term. Start by understanding how these pieces fit together. Once you build or work with a multi-agent system, the terminology will become much more intuitive.