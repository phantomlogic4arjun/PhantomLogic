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
docker run --name phantom-logic-postgres --restart unless-stopped -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD='CHANGE_THIS_LOCAL_PASSWORD' -e POSTGRES_DB=phantom_logic -p 5432:5432 -v phantom_logic_pgdata:/var/lib/postgresql -d postgres:18
```

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
$env:PHANTOM_LOGIC_DB_HOST = "localhost"
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

The migrations must run as the migration