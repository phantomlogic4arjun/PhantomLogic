# Phantom Logic — Windows Collaborator Setup Guide

**Purpose:** Set up a Windows computer to develop and contribute to Phantom Logic.

**Target environment:** Windows 11, native Windows applications, PowerShell.

**Repository:** https://github.com/phantomlogic4arjun/PhantomLogic

**Guiding principle:** Humans Guide. Agents Execute.

---

## 1. Overview

This guide takes a new collaborator from a clean Windows installation to a working Phantom Logic development environment.

You do not need to install Ubuntu or learn Linux commands.

You will install:

| Application | Purpose |
|---|---|
| Git for Windows | Source control and repository access |
| Python 3.12 | Run the Phantom Logic application |
| Node.js 24 | JavaScript tooling and plugin validation |
| Visual Studio Code | Edit and inspect project files |
| Docker Desktop | Run PostgreSQL locally |
| Ollama | Run the mandatory local AI model |
| OpenCode | Work with Phantom Logic agents |
| GitHub account | Collaborate on the repository |

**Important:** Docker Desktop may use its WSL2 backend internally. You do not need to install an Ubuntu distribution or use a Linux terminal.

### Hardware requirements

- Windows 11 64-bit.
- **8 GB RAM:** Supported for installation and contribution. Local-agent execution may be slow, and the computer may not have enough available memory to run the model with the required context.
- **16 GB RAM:** Recommended minimum for regular development and local-agent execution.
- **32 GB RAM:** Recommended for comfortable multitasking and larger models.
- At least 30 GB of free disk space. Additional space is needed for AI models and development tools.
- Hardware virtualization enabled.
- An NVIDIA or supported AMD GPU is helpful but not mandatory.

Local model performance depends on available RAM, GPU resources, and model size.

**Important:** Installing an AI model successfully does not guarantee that the computer can run it with a 64K context window. The actual context allocation must be verified.

## 2. Create a GitHub account

1. Visit https://github.com/signup.
2. Create your personal GitHub account.
3. Verify your email address.
4. Enable two-factor authentication.
5. Send your GitHub username to the Phantom Logic administrator.
6. Accept the repository invitation.

Repository:

https://github.com/phantomlogic4arjun/PhantomLogic

Use your own GitHub account. Never share another developer's credentials.

## 3. Install Git for Windows

1. Visit https://git-scm.com/install/windows.
2. Download Git for Windows.
3. Run the installer.
4. Use the standard installation options.
5. Open PowerShell.

Verify:

```powershell
git --version
```

Configure your Git identity:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Use the email associated with your GitHub account.

## 4. Install Python 3.12

1. Visit https://www.python.org/downloads/windows/.
2. Download the Python 3.12 Windows 64-bit installer.
3. Run the installer.
4. Enable the option to add Python to PATH if offered.
5. Complete installation.

Open a new PowerShell window.

Verify:

```powershell
py -3.12 --version
```

The project requires Python 3.11 or newer. Python 3.12 is one of the versions tested by the CI workflow.

## 5. Install Node.js 24

1. Visit https://nodejs.org/en/download.
2. Download the Windows installer for Node.js 24.
3. Run the installer using the standard options.
4. Open a new PowerShell window.

Verify:

```powershell
node --version
npm --version
```

Node.js 24 is used by the project's plugin-validation workflow.

## 6. Install Visual Studio Code

1. Visit https://code.visualstudio.com/.
2. Download Visual Studio Code for Windows.
3. Install and launch it.

Recommended extensions:

- Python
- Pylance
- GitLens

These extensions improve the development experience but are not required application dependencies.

## 7. Install Docker Desktop

Docker runs the local PostgreSQL database.

1. Visit https://www.docker.com/products/docker-desktop/.
2. Download Docker Desktop for Windows.
3. Run the installer.
4. Select the recommended WSL2-based backend if prompted.
5. Restart Windows if requested.
6. Start Docker Desktop.
7. Wait until Docker reports that it is running. 

You do not need to install an Ubuntu distribution or open a Linux terminal.

Open PowerShell and verify:

```powershell
docker --version
docker compose version
docker info
```

Docker documentation:

https://docs.docker.com/desktop/setup/install/windows-install/

## 8. Install Ollama

Ollama runs AI models locally on Windows.

A local Ollama model is mandatory for the Phantom Logic agent environment. Cloud providers may be connected as additional providers, but they do not replace the local model requirement.

### 8.1 Install Ollama

1. Visit https://ollama.com/download/windows.
2. Download the Windows installer.
3. Run the installer.
4. Start Ollama.

Verify:

```powershell
ollama --version
```

Ollama documentation:

https://docs.ollama.com/windows

### 8.2 Download the required local model

Phantom Logic uses the following baseline local model:

```text
qwen3.5:4b
```

Download it:

```powershell
ollama pull qwen3.5:4b
```

The model advertises a 256K context window and supports tool use. Its advertised maximum context is larger than the minimum required by OpenCode.

Check installed models:

```powershell
ollama list
```

Test the model:

```powershell
ollama run qwen3.5:4b
```

Ask it a question and verify that it responds.

Exit the model session when finished.

### 8.3 Configure the required context length

OpenCode requires a context length of at least 64K tokens when using Ollama.

Ollama may use a smaller default context depending on available GPU memory. Downloading a model with a 256K advertised context does not automatically mean Ollama will allocate 64K or more.

To configure the context:

1. Open the Ollama application from the Windows system tray or Start menu.
2. Open Ollama Settings.
3. Locate the context length setting.
4. Set the context length to at least **64K tokens**.
5. Save the setting.

The computer must have enough available memory to support this allocation.

**Important hardware guidance:**

- On an 8 GB computer, the required context may not fit alongside Windows, Docker, PostgreSQL, and OpenCode.
- On a 16 GB computer, local-agent execution is more practical, although performance still depends on available GPU and system memory.
- A 32 GB computer provides more room for multitasking and larger models.

Do not reduce the context below 64K to work around memory limitations.

Ollama context documentation:

https://docs.ollama.com/context-length

Ollama runs directly on Windows. It does not need Docker.

## 9. Install OpenCode

Phantom Logic currently uses the OpenCode 1 plugin architecture.

The repository dependency is `@opencode-ai/plugin` version `1.19.5`. The maintainer's current OpenCode CLI environment is also version `1.19.5`.

For a consistent collaborator setup, install that exact CLI version.

Open PowerShell:

```powershell
npm install --global opencode-ai@1.19.5
```

Verify:

```powershell
opencode --version
```

The expected version is:

```text
1.19.5
```

Check which executable Windows resolves:

```powershell
where.exe opencode
```

If another OpenCode CLI is already installed, resolve the conflicting installation before continuing.

Do not install OpenCode 2 alongside the project's OpenCode 1 CLI.

Official OpenCode information:

https://opencode.ai/docs/

**Important:** The project must remain on its approved OpenCode 1 environment until its plugin architecture has been deliberately migrated and validated. Do not independently upgrade the CLI or plugin SDK.

## 10. Clone the Phantom Logic repository

After the current development changes have been merged into `main`, open PowerShell.

Create a projects directory:

```powershell
New-Item -ItemType Directory -Force "$HOME\Projects"
Set-Location "$HOME\Projects"
```

Clone the repository:

```powershell
git clone https://github.com/phantomlogic4arjun/PhantomLogic.git
```

Enter the project:

```powershell
Set-Location .\PhantomLogic
```

Verify:

```powershell
git remote -v
git status
```

Update the main branch:

```powershell
git switch main
git pull origin main
```

If GitHub requests authentication, use your own GitHub account through Git Credential Manager or the approved authentication flow.

## 11. Set up the Python environment

Run these commands from the repository root.

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run the following command for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify:

```powershell
python --version
python -c "import phantom_logic; print('Package import successful')"
```

The project's `pyproject.toml` is the authoritative dependency definition. `requirements.txt` is retained as a compatibility entry point.

## 12. Install OpenCode project dependencies

From the repository root:

```powershell
npm ci --prefix .opencode
```

This installs the exact project dependencies recorded in the lock file.

Do not manually change or upgrade the OpenCode plugin dependencies.

## 13. Configure PostgreSQL

Phantom Logic uses PostgreSQL as its authoritative persistence layer.

The local database must follow the existing project architecture:

| Setting | Value |
|---|---|
| Database | `phantom_logic` |
| Work Item schema | `work_items` |
| Audit schema | `audit` |
| Application role | `phantom_logic_app` |
| Migration tool | Alembic |

### 13.1 Start PostgreSQL

Open Docker Desktop and make sure it is running.

In PowerShell, choose a strong password for the local PostgreSQL administrator account. Replace the example below with your own local password.

```powershell
docker run --name phantom-logic-postgres --restart unless-stopped -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD='CHANGE_THIS_LOCAL_PASSWORD' -e POSTGRES_DB=phantom_logic -p 127.0.0.1:5432:5432 -v phantom_logic_pgdata:/var/lib/postgresql -d postgres:18
```

The port is bound to `127.0.0.1` so the database is accessible from the local computer without exposing the published port to other devices on the network.

Use a password without spaces or characters that require special handling in PowerShell or `.env` files.

Wait for PostgreSQL to become ready:

```powershell
docker exec phantom-logic-postgres pg_isready -U postgres -d phantom_logic
```

Expected result:

```text
accepting connections
```

If the container already exists, do not create another one. Start the existing container:

```powershell
docker start phantom-logic-postgres
```

### 13.2 Configure database connection variables

The project's database configuration uses these environment variables:

```powershell
$env:PHANTOM_LOGIC_DB_HOST = "127.0.0.1"
$env:PHANTOM_LOGIC_DB_PORT = "5432"
$env:PHANTOM_LOGIC_DB_NAME = "phantom_logic"
$env:PHANTOM_LOGIC_DB_USER = "postgres"
$env:PHANTOM_LOGIC_DB_PASSWORD = "CHANGE_THIS_LOCAL_PASSWORD"
```

Use the same password selected when starting the PostgreSQL container.

These variables apply to the current PowerShell session.

### 13.3 Create the application role and migration schema

Choose a separate strong password for the application role:

```powershell
$env:PHANTOM_LOGIC_APP_PASSWORD = "CHANGE_THIS_APP_PASSWORD"
```

Run:

```powershell
@'
import os
import psycopg
from psycopg import sql

with psycopg.connect(
    host=os.environ["PHANTOM_LOGIC_DB_HOST"],
    port=os.environ["PHANTOM_LOGIC_DB_PORT"],
    dbname=os.environ["PHANTOM_LOGIC_DB_NAME"],
    user=os.environ["PHANTOM_LOGIC_DB_USER"],
    password=os.environ["PHANTOM_LOGIC_DB_PASSWORD"],
) as connection:
    connection.execute(
        sql.SQL(
            "CREATE ROLE phantom_logic_app LOGIN PASSWORD {}"
        ).format(
            sql.Literal(os.environ["PHANTOM_LOGIC_APP_PASSWORD"])
        )
    )

    connection.execute(
        "CREATE SCHEMA work_items AUTHORIZATION postgres"
    )

print("Application role and migration schema created.")
'@ | python -
```

This assumes a fresh local database. If the role or schema already exists, stop and inspect the existing database rather than blindly rerunning the creation commands.

### 13.4 Apply database migrations

The migrations must run as the migration-owner account.

Verify the migration-owner variables:

```powershell
$env:PHANTOM_LOGIC_DB_USER = "postgres"
$env:PHANTOM_LOGIC_DB_PASSWORD = "CHANGE_THIS_LOCAL_PASSWORD"
```

Apply migrations:

```powershell
python -m alembic upgrade head
```

Do not create application tables manually.

### 13.5 Grant application permissions

The application role must have the same restricted permissions used by the CI workflow.

Run:

```powershell
@'
import os
import psycopg

with psycopg.connect(
    host=os.environ["PHANTOM_LOGIC_DB_HOST"],
    port=os.environ["PHANTOM_LOGIC_DB_PORT"],
    dbname=os.environ["PHANTOM_LOGIC_DB_NAME"],
    user=os.environ["PHANTOM_LOGIC_DB_USER"],
    password=os.environ["PHANTOM_LOGIC_DB_PASSWORD"],
) as connection:
    connection.execute("""
        GRANT CONNECT ON DATABASE phantom_logic
        TO phantom_logic_app
    """)

    connection.execute("""
        GRANT USAGE ON SCHEMA work_items
        TO phantom_logic_app
    """)

    connection.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON TABLE
            work_items.work_items,
            work_items.work_item_relationships,
            work_items.work_item_acceptance_criteria,
            work_items.work_item_audit_references
        TO phantom_logic_app
    """)

    connection.execute("""
        GRANT USAGE ON SCHEMA audit
        TO phantom_logic_app
    """)

    connection.execute("""
        GRANT SELECT, INSERT
        ON TABLE audit.audit_events
        TO phantom_logic_app
    """)

print("Application database permissions configured.")
'@ | python -
```

The application role must not receive UPDATE or DELETE permissions on audit records.

### 13.6 Configure the application connection

The repository includes `.env.example` with the expected database settings.

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Open it:

```powershell
notepad .env
```

Configure it using your own local application-role password:

```text
PHANTOM_LOGIC_DB_HOST=127.0.0.1
PHANTOM_LOGIC_DB_PORT=5432
PHANTOM_LOGIC_DB_NAME=phantom_logic
PHANTOM_LOGIC_DB_USER=phantom_logic_app
PHANTOM_LOGIC_DB_PASSWORD=YOUR_APPLICATION_ROLE_PASSWORD
```

Use the same password you assigned to `phantom_logic_app` in Section 13.3.

The `.env` file is local configuration and must never be committed to Git.

**Administrator versus application credentials**

There are two different database identities:

- `postgres`: used for initial role/schema creation, migrations, and permission grants.
- `phantom_logic_app`: used by the application and normal test execution.

The migration commands in Sections 13.3–13.5 temporarily set PowerShell environment variables to the administrator account. These environment variables take precedence over values loaded from `.env`.

After finishing database provisioning, open a **new PowerShell window** in the repository directory. Activate the Python virtual environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Do not set the administrator database credentials in this new session.

The application should now load the `phantom_logic_app` credentials from `.env`.

Verify the configuration before running the application or tests. Do not use the administrator account for normal application execution.

Use your own local credentials. Never copy another developer's `.env` file, passwords, or API keys.

## 14. Configure OpenCode and AI models

Phantom Logic uses OpenCode to run its agent environment.

**Complete Section 14.1 before starting OpenCode.** The local Ollama model is mandatory.

Start OpenCode through Ollama from the repository root. This allows OpenCode to use the local model while loading the project's configuration and instructions.

The project configuration defines these agents:

- Orchestrator
- ProductManager
- Architect
- Designer
- Developer
- QA
- Security
- DevOps

The Orchestrator coordinates work and delegates to specialist agents.

Do not independently change agent model assignments or the shared `opencode.jsonc` configuration.

### 14.1 Configure and launch the mandatory local Ollama model

Make sure Ollama is running.

Verify that the required model is installed:

```powershell
ollama list
```

The required model is:

```text
qwen3.5:4b
```

If it is not installed:

```powershell
ollama pull qwen3.5:4b
```

Open Ollama Settings and confirm that the context length is set to at least **64K tokens**, as described in Section 8.3.

Launch OpenCode through Ollama:

```powershell
ollama launch opencode
```

Follow the model-selection prompts if they appear, and select:

```text
qwen3.5:4b
```

Do not use the `--config` option for this initial launch. That option configures OpenCode without starting an interactive session.

Once OpenCode opens, use:

```text
/models
```

Confirm that the intended Ollama model is available and selected.

After sending a model request, open another PowerShell window and verify the actual context allocation:

```powershell
ollama ps
```

Inspect the `CONTEXT` column. It must show at least `65536`.

If the context is below 65536, revisit Ollama Settings and correct the context configuration.

If the model cannot load with the required context, or the computer runs out of memory, close other applications and try again. An 8 GB computer may not have enough available memory for reliable local-agent execution. A computer with 16 GB or more RAM is recommended.

Do not reduce the context below 64K to work around memory limitations.

This setup is intended to configure the collaborator's local OpenCode session. Do not add personal model settings or credentials to the shared project configuration.

Ollama's OpenCode integration documentation:

https://docs.ollama.com/integrations/opencode

Ollama context documentation:

https://docs.ollama.com/context-length

### 14.2 Connect cloud model providers

Some assigned tasks may benefit from a cloud model in addition to the mandatory local Ollama model.

Inside OpenCode, run:

```text
/connect
```

Then:

1. Select the provider approved for the project.
2. Complete its authentication process.
3. Use your own authorized account or API key.
4. Never share credentials with another collaborator.
5. Never put API keys in Git-tracked files.

To select an available model, run:

```text
/models
```

Choose a model available through your authenticated provider.

Model availability and usage costs depend on the provider account and its access permissions.

Cloud providers are optional. The local Ollama model remains mandatory.

### 14.3 Model assignment rules

The project configuration and agent instructions govern the agent environment.

A collaborator may authenticate their own approved providers, but must not independently:

- Change the Orchestrator's assigned model.
- Change specialist agent model assignments.
- Replace the shared provider configuration.
- Modify `opencode.jsonc` without approval.

If a required model is unavailable, report the issue to the Phantom Logic administrator rather than changing the project configuration.

## 15. Verify the installation

Make sure the Python virtual environment is active and the database is running.

Run the full test suite:

```powershell
python -m unittest discover -s tests -p "Test*.py" -v
```

Some tests require a correctly provisioned PostgreSQL database.

Run the OpenCode plugin initialization test:

```powershell
node tests/plugins/TestWorkItemPlugin.mjs
```

The expected result is successful plugin initialization and Work Item tool registration.

**Important Windows validation limitation:** CI currently validates Python tests on Windows and plugin initialization on Windows. The complete native Windows Work Item plugin-to-Python execution path still requires direct validation. Do not treat successful initialization alone as proof that the entire plugin bridge works.

Report any failures to the Phantom Logic administrator.

## 16. Read project governance documentation

Before contributing, read:

1. `AGENTS.md`
2. `docs/company/Rules.md`
3. `docs/standards/PlatformIndependence.md`
4. `docs/development/DevelopmentHistory.md`

These documents define the project structure, agent responsibilities, development standards, audit requirements, and platform-independence expectations.

Important rules:

- The Orchestrator is the central coordination authority.
- Specialist agents must follow their assigned responsibilities.
- The Orchestrator is the sole approved interface to the central AuditWriter.
- Agents must not write directly to the central audit database.
- Work Item operations must follow the approved audit process.
- Failed audit submissions must not be silently ignored.
- Do not bypass governance rules to complete a task faster.
- Do not modify security rules, migrations, or architecture without approval.

## 17. Your first contribution

Once the installation is verified:

1. Update your local main branch.
2. Create a feature branch for your assigned work.
3. Read the applicable project instructions.
4. Coordinate work through the Orchestrator.
5. Make changes only within the approved scope.
6. Run relevant tests.
7. Review your changes.
8. Commit your work.
9. Push your feature branch.
10. Open a pull request.

Do not push directly to `main`.

Follow the repository's pull request template and required sections, including `Related Work Items` and `Change Sets`.

Wait for the required checks and review before merging.

## 18. Troubleshooting

### Python is not recognized

Open a new PowerShell window and try:

```powershell
py -3.12 --version
```

If this fails, repair the Python installation and enable the Python launcher.

### PowerShell blocks virtual environment activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate `.venv` again.

### Docker is not running

Start Docker Desktop and wait until the engine is running.

Verify:

```powershell
docker info
```

### PostgreSQL container already exists

Inspect it:

```powershell
docker ps -a
```

Start it:

```powershell
docker start phantom-logic-postgres
```

Do not delete the PostgreSQL volume to solve a routine startup issue. It contains local database data.

### Ollama model is unavailable

Verify Ollama:

```powershell
ollama list
```

If necessary:

```powershell
ollama pull qwen3.5:4b
```

### Ollama cannot allocate 64K context

1. Close other applications that are using significant memory.
2. Open Ollama Settings.
3. Confirm the context length is at least 64K.
4. Retry the model request.
5. Check the actual allocation using:

```powershell
ollama ps
```

If the computer cannot allocate the required context, it may not have enough available memory for local-agent execution. Use a machine with more available RAM rather than reducing the required context.

### OpenCode cannot find a provider or model

Check the current project configuration and provider connection. Confirm that Ollama is running and the required local model is installed.

Do not independently rewrite `opencode.jsonc` or agent prompt files.

### Tests fail

Capture the complete error output and report it to the administrator. Do not bypass failing tests or weaken security checks to make the suite pass.

## 19. Completion checklist

- [ ] GitHub account created and repository invitation accepted.
- [ ] Git installed and configured.
- [ ] Python 3.12 installed.
- [ ] Node.js 24 installed.
- [ ] Visual Studio Code installed.
- [ ] Docker Desktop installed and running.
- [ ] PostgreSQL container running.
- [ ] Database and application role provisioned.
- [ ] Alembic migrations applied.
- [ ] Application database permissions configured.
- [ ] Local `.env` configured with the `phantom_logic_app` credentials.
- [ ] Ollama installed.
- [ ] `qwen3.5:4b` downloaded and tested.
- [ ] Ollama context configured to at least 64K.
- [ ] Actual Ollama context verified using `ollama ps`.
- [ ] OpenCode CLI 1.19.5 installed and verified.
- [ ] Ollama connected to OpenCode and the local model selected.
- [ ] Repository cloned.
- [ ] Python virtual environment created.
- [ ] Project dependencies installed.
- [ ] OpenCode plugin dependencies installed.
- [ ] Project agents verified.
- [ ] Python tests executed.
- [ ] Work Item plugin initialization verified.
- [ ] Native Windows plugin-to-Python execution tested when the validation procedure is available.
- [ ] Governance documents read.
- [ ] Ready to create a feature branch and contribute.

---

**Phantom Logic**

*Humans Guide. Agents Execute.*