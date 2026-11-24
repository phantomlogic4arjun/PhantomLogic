# Platform Independence Standard

## 1. Purpose

This standard establishes the platform independence requirements for Phantom Logic's source code, development environment, tooling, automated testing, and operational workflows.

Phantom Logic is intended to support development and operation across multiple operating systems without maintaining separate platform-specific implementations of its core functionality.

Platform independence must be considered during architecture, implementation, code review, testing, and deployment.

The objective is to ensure that developers and authorized AI agents can work with the same repository, application architecture, and development workflows regardless of their operating system.

## 2. Scope

This standard applies to:

- The Phantom Logic central control plane.
- Python application code and supporting packages.
- OpenCode configuration, plugins, and agent integrations.
- Database configuration and migration tooling.
- Automated tests and development utilities.
- Build, validation, and CI workflows.
- Developer setup instructions and technical documentation.
- Future shared platform components and internal tools.

Independent software products maintained in separate repositories should establish their own platform support requirements while following the applicable principles of this standard.

## 3. Supported Platform Strategy

### 3.1 Target Operating Systems

Phantom Logic targets the following operating systems:

| Operating System | Target Support |
|---|---|
| macOS | Supported target |
| Linux | Supported target |
| Windows | Supported target |

The objective is to maintain one shared codebase across all three operating systems.

Platform-specific implementations must not be introduced when a portable implementation can reasonably satisfy the same requirement.

### 3.2 Support and Validation Status

A platform must not be described as fully supported solely because the source code appears compatible.

Platform support must be established through documented validation.

The following distinctions apply:

- **Target:** The platform is part of Phantom Logic's intended support scope.
- **Implemented:** The required compatibility measures have been implemented.
- **Validated:** Automated tests and applicable integration checks have passed on the platform.
- **Supported:** The platform has passed the required validation and its setup and operational procedures are documented.

The current validation status of each platform must be based on actual test evidence.

### 3.3 Native and Compatibility Environments

Native operating-system support and compatibility environments must be distinguished.

Examples include:

- Native Windows.
- Windows Subsystem for Linux (WSL2).
- Native macOS.
- Native Linux distributions.

Successful execution under WSL2 does not establish native Windows compatibility.

Compatibility environments may be used for development, but they must not replace native platform validation when native support is required.

### 3.4 Current Platform Validation Status

Platform validation status must reflect completed and documented validation evidence, not intended support or configured automation.

The current project status is:

| Platform | Development Environment | Application Validation | OpenCode Plugin Validation |
|---|---|---|---|
| macOS | Development environment available | Local test suite validated | Initial plugin module loading and tool registration validated |
| Linux | CI environment configured | GitHub Actions validation pending | Pending |
| Windows | CI environment configured | Native Windows CI validation pending | Native Windows validation pending |

The following rules apply:

- A configured CI workflow does not establish successful platform validation.
- Local simulation does not replace validation in the target operating system's native environment.
- OpenCode plugin validation must be tracked separately from Python application validation.
- Validation status must be updated when new test evidence becomes available.
- A platform must not be described as fully supported until all required application, runtime, and operational validation has been completed.

## 4. Cross-Platform Development Principles

### 4.1 One Codebase

The same application source code must be used across supported operating systems.

Separate operating-system-specific copies of application modules must not be maintained.

Conditional platform behavior is permitted only when an operating-system difference genuinely requires it.

Such behavior must be isolated, documented, and tested.

### 4.2 Platform-Neutral APIs

Developers and agents must prefer standard, cross-platform APIs.

Examples include:

- Python `pathlib` for filesystem paths.
- Python `os.environ` for environment variables.
- Python `subprocess` for process execution.
- Python `sys.executable` when invoking the active Python interpreter.
- Python standard libraries for filesystem and process operations.
- Runtime-supported path utilities for TypeScript and JavaScript.

Platform-specific APIs must not be used without a documented technical justification.

### 4.3 Filesystem Paths

Filesystem paths must not assume a particular operating system's path separator or directory structure.

Requirements:

- Use `pathlib.Path` for Python filesystem operations.
- Use appropriate path utilities in TypeScript and JavaScript.
- Resolve paths relative to known project locations or explicitly configured directories.
- Avoid hardcoded user home directories, drive letters, and operating-system-specific installation paths.
- Do not hardcode a platform-specific virtual-environment executable path. Resolve the appropriate executable using platform-aware logic or an explicitly configured interpreter.
- Preserve correct handling of spaces and non-ASCII characters in paths.

Repository-relative paths should be preferred where appropriate.

### 4.4 Case Sensitivity

File and directory references must use the exact casing of their tracked repository names.

Developers and agents must not rely on case-insensitive filesystem behavior.

This requirement is important because macOS and Windows filesystems may commonly be configured as case-insensitive, while Linux filesystems are commonly case-sensitive.

### 4.5 Line Endings and Text Encoding

Text files must use consistent encoding and line-ending conventions.

- UTF-8 must be the default text encoding.
- Git line-ending normalization must be configured through `.gitattributes`.
- Source files must not contain unintended mixed line endings.
- Generated files must use explicitly appropriate encoding where interoperability matters.
- Binary files must not be subjected to text line-ending conversion.

## 5. Python Environment and Dependency Management

### 5.1 Python Version

The Python version requirement declared in `pyproject.toml` is authoritative.

CI must validate the minimum supported Python version and additional supported versions selected by the project.

Developer environments must use a Python version satisfying the declared requirement.

### 5.2 Virtual Environments

Developers must use isolated Python virtual environments for project dependencies.

The conventional project environment directory is:

`.venv/`

Virtual-environment executable paths differ by operating system.

Developers and agents must not assume that the Python executable is always located under `.venv/bin/`.

Application integrations must resolve the appropriate interpreter for the active platform.

The project must not commit virtual-environment contents.

### 5.3 Dependency Management

`pyproject.toml` should remain the authoritative source for Python project metadata and runtime dependencies.

Additional dependency files may be maintained when a documented workflow requires them.

Duplicated dependency declarations must not be allowed to drift.

Dependencies must be selected with consideration for supported operating systems and Python versions.

New dependencies must be evaluated for:

- Operating-system compatibility.
- Python-version compatibility.
- Maintenance and security status.
- Installation requirements.
- Native binary or system-library dependencies.

### 5.4 Package Installation

The Python project must be installable using standard Python packaging tools.

Development instructions must document installation into the active virtual environment.

Where editable installation is required for development, the documented procedure must use the project's package configuration rather than relying on an operating-system-specific import path.

## 6. Command Execution and Shell Independence

### 6.1 Portable Commands

Development and operational instructions must prefer commands that work across supported shells.

Python modules should be invoked using:

`python -m package.module`

Python tests should be invoked using the active environment's Python interpreter.

Instructions must not assume that macOS/Linux shell syntax is available in Windows PowerShell.

### 6.2 Environment Variables

Environment variables must be configured using methods appropriate to the execution environment.

Documentation must provide platform-appropriate examples when the syntax differs between shells.

Application code must access environment variables through standard runtime APIs rather than shell-specific mechanisms.

### 6.3 Shell Scripts

Shell scripts must declare their intended shell and execution environment.

A script written specifically for Bash must not be represented as universally executable on Windows.

When a workflow needs to operate across multiple operating systems, prefer:

- Python utilities for shared application operations.
- Runtime-neutral tooling.
- Explicit platform-specific CI steps where necessary.

Do not create unnecessary shell-script variants when one portable implementation is practical.

### 6.4 Process Execution

Process execution must:

- Use argument arrays rather than constructing shell command strings whenever possible.
- Avoid unnecessary shell invocation.
- Handle spaces and special characters in paths correctly.
- Check process exit codes.
- Capture and handle standard output and standard error appropriately.
- Apply reasonable timeouts where applicable.
- Avoid assumptions about executable names and installation locations.

## 7. Database and Persistence Portability

### 7.1 Database Architecture

Platform independence must not be achieved by weakening or replacing the approved database architecture.

The central control plane must retain its approved PostgreSQL, SQLAlchemy, and Alembic architecture unless a separately reviewed architecture decision authorizes a change.

Operating-system differences must be handled through configuration and supported database tooling rather than separate database implementations.

### 7.2 Database Configuration

Database connection settings must be supplied through environment-based configuration or approved configuration mechanisms.

Requirements:

- Do not hardcode local database installation paths.
- Do not hardcode developer-specific database hosts or credentials.
- Keep secrets outside source control.
- Use portable connection configuration.
- Document database installation and service startup requirements for supported operating systems.

### 7.3 Migrations

Alembic migrations must use portable paths and database operations.

Migration scripts must not depend on a developer's operating system, home directory, or local database installation layout.

The same migration history must be used across supported platforms.

### 7.4 Database Validation

Database integration tests must validate the actual database behavior required by the application.

Unit-test success alone does not establish database compatibility.

CI must document which operating systems execute database integration tests and which execute only unit or non-database tests.

## 8. OpenCode and Runtime Integration

### 8.1 Runtime Compatibility

OpenCode plugins and supporting integrations must use runtime-supported APIs and portable filesystem and process handling.

Platform compatibility must account for:

- Runtime installation and availability.
- Python interpreter discovery.
- Node.js or Bun dependencies, where applicable.
- Filesystem paths.
- Process execution.
- Environment-variable propagation.
- Standard input and output handling.

### 8.2 Interpreter Resolution

Plugins that invoke Python must not hardcode a platform-specific virtual-environment executable path.

They must resolve the appropriate interpreter using an explicitly defined, portable mechanism.

If interpreter resolution fails, the integration must return a clear, actionable error.

### 8.3 Plugin Dependencies

Plugin dependencies must be declared and installed through the appropriate package-management configuration.

Dependency installation and execution must not assume a macOS-only or Linux-only environment.

### 8.4 Runtime Validation

OpenCode integration compatibility must be tested separately from Python application compatibility.

A passing Python test suite does not establish that OpenCode plugins operate correctly on a particular operating system.

## 9. Testing Requirements

### 9.1 Cross-Platform Testing

The CI strategy must progressively validate the application on:

- Ubuntu/Linux.
- macOS.
- Windows.

The CI matrix must cover the supported Python versions selected by the project.

### 9.2 Test Categories

Tests should be categorized according to their dependencies:

- Unit tests.
- Component and service tests.
- Database integration tests.
- CLI contract tests.
- Runtime and plugin integration tests.
- End-to-end tests, when available.

The CI pipeline must make it clear which categories execute on each operating system.

### 9.3 Platform-Specific Tests

Where platform-specific behavior is unavoidable, tests must verify the relevant behavior on each affected platform.

Tests must not silently skip required compatibility checks.

Any platform-specific test exclusion must be documented with its technical reason.

### 9.4 Validation Evidence

Platform compatibility claims must be supported by recorded CI results or documented manual validation.

A platform must not be marked validated when its required tests have not executed successfully.

## 10. CI and Automation

CI workflows must be designed to support the project's declared platform targets.

Requirements:

- Use a platform matrix where appropriate.
- Keep setup and dependency installation reproducible.
- Avoid unnecessary shell-specific command assumptions.
- Separate platform-independent checks from platform-specific integration checks.
- Preserve consistent test and validation expectations.
- Report failures with enough information to identify the affected platform and environment.

CI should serve as the primary continuous verification mechanism for platform independence.

## 11. Security and Operational Consistency

Platform independence must not weaken security.

All platforms must preserve the same applicable:

- Authentication and authorization requirements.
- Secret-management practices.
- Database permissions.
- Audit requirements.
- Human approval controls.
- File-access restrictions.
- Error-handling expectations.

Operating-system differences must not be used to bypass established governance or security controls.

Credentials and environment files must remain excluded from source control on every platform.

## 12. Documentation Requirements

Developer documentation must describe:

- Supported operating systems and their validation status.
- Required Python and runtime versions.
- Environment creation and activation.
- Dependency installation.
- Environment-variable configuration.
- PostgreSQL installation and configuration.
- Database migration execution.
- Test execution.
- OpenCode setup and plugin requirements.
- Known platform-specific limitations.

Commands must be identified by their intended shell when they are not portable.

Documentation must be updated when implementation or supported-platform requirements change.

## 13. Code Review Requirements

Reviewers must evaluate platform independence for changes involving:

- Filesystem access.
- Process execution.
- Environment variables.
- Runtime and executable discovery.
- Dependencies.
- Database connectivity.
- Shell scripts.
- CI workflows.
- Plugin integrations.
- File naming and casing.

Reviewers must identify platform-specific assumptions even when the implementation works on the developer's machine.

Platform compatibility must be considered alongside correctness, security, maintainability, and test coverage.

## 14. Prohibited Practices

Unless an approved technical exception exists, developers and agents must not:

- Hardcode developer-specific filesystem paths.
- Assume a single operating-system path separator.
- Hardcode `.venv/bin/python` or another platform-specific interpreter location.
- Assume Unix shell syntax works in PowerShell.
- Depend on case-insensitive filesystem behavior.
- Introduce separate copies of shared application logic for different operating systems.
- Use operating-system-specific commands when portable alternatives are practical.
- Claim cross-platform support without validation evidence.
- Weaken security or governance to accommodate a platform.
- Introduce unnecessary dependencies or architectural complexity solely for portability.

## 15. Exceptions

Platform-specific behavior may be necessary when:

- A required runtime capability differs between operating systems.
- An operating-system integration has no practical portable alternative.
- A third-party dependency imposes platform-specific requirements.
- A security or performance requirement justifies a specialized implementation.

Exceptions must:

1. State the technical reason.
2. Identify the affected platforms.
3. Document the expected behavior.
4. Include appropriate tests.
5. Identify any resulting support limitations.
6. Receive the required architecture or technical approval.

Exceptions must remain as narrow as reasonably possible.

## 16. Implementation and Adoption

Platform independence must be introduced progressively.

The adoption process should prioritize:

1. Establishing supported-platform and runtime requirements.
2. Correcting confirmed platform-specific assumptions.
3. Standardizing environment setup and developer commands.
4. Updating documentation.
5. Expanding automated CI coverage.
6. Validating native operating-system execution.
7. Recording remaining limitations and compatibility exceptions.

Existing functionality, database architecture, security controls, and governance requirements must be preserved.

Platform-independence work must not become an excuse for unrelated refactoring or architectural changes.

## 17. Compliance

All developers and AI agents working on Phantom Logic must follow this standard.

The standard must be considered alongside:

- `CodingStandards.md`
- `CodeReviewGuidelines.md`
- `AGENTS.md`
- `docs/company/Rules.md`
- Applicable architecture decisions.

Changes that affect platform compatibility must be reviewed and validated according to the requirements established here.

The Platform Independence Standard may be revised as Phantom Logic's supported environments, architecture, and operational requirements evolve.