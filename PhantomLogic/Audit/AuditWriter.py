
#!/usr/bin/env python3
"""
Phantom Logic - Audit Writer

Purpose:
    Append validated audit records to the central AuditLog.md.

Security:
    - Uses a fixed audit-log destination.
    - Opens the log in append mode.
    - Never intentionally overwrites or deletes existing records.
    - Validates required fields and permitted values.
    - Rejects multiline field values.
    - Validates existing writer-generated records before appending.
    - Rejects duplicate Audit IDs.
    - Uses file locking to reduce concurrent-write conflicts.
    - Flushes and synchronizes writes to disk.

Usage:
    python3 PhantomLogic/Audit/AuditWriter.py < audit_entry.json
"""

import fcntl
import json
import os
import re
import stat
import sys

from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------

# The destination is fixed relative to this Python file.
# The caller cannot supply an alternative destination.

AUDIT_FILE = Path(__file__).resolve().parent / "AuditLog.md"
MAX_INPUT_SIZE = 64 * 1024  # 64 KB

# Required audit-entry fields.

REQUIRED_FIELDS = [
    "audit_id",
    "timestamp",
    "requesting_party",
    "responsible_agent",
    "action_requested",
    "purpose",
    "affected_resources",
    "approval_required",
    "authorized_by",
    "outcome",
    "verification",
    "additional_notes",
]


# Permitted values.

ALLOWED_APPROVAL = {
    "Yes",
    "No",
}

ALLOWED_OUTCOMES = {
    "Successful",
    "Failed",
    "Partially Completed",
    "Cancelled",
    "Blocked",
}


# Expected timestamp format:
# YYYY-MM-DD HH:MM:SS TIMEZONE

TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2} "
    r"\d{2}:\d{2}:\d{2} "
    r"[A-Za-z0-9_+-]+$"
)

AUDIT_ID_PATTERN = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-"
    r"[a-f0-9]{4}-[a-f0-9]{12}$"
)


# ---------------------------------------------------------
# 2. Error Handling
# ---------------------------------------------------------

def fail(message):
    """
    Report an error and terminate without writing an entry.
    """

    print(
        f"Audit Writer error: {message}",
        file=sys.stderr
    )

    sys.exit(1)


# ---------------------------------------------------------
# 3. Input Validation
# ---------------------------------------------------------

def clean_value(value, field):
    """
    Validate a field and reject multiline or invalid input.
    """

    if not isinstance(value, str) or not value.strip():
        fail(f"Missing or invalid field: {field}")

    # Reject newline and carriage-return characters.
    if "\n" in value or "\r" in value:
        fail(f"Multiline input is not permitted: {field}")

    # Reject other control characters.
    if any(ord(char) < 32 for char in value):
        fail(f"Control characters are not permitted: {field}")

    value = value.strip()

    # Reject unfilled template placeholders.
    if value in {
        "[Action Title]",
        "YYYY-MM-DD HH:MM:SS (Time Zone)",
    }:
        fail(f"Template placeholder not permitted: {field}")

    return value


def validate_entry(data):
    """
    Validate the complete audit record.
    """

    if not isinstance(data, dict):
        fail("Input must be a JSON object.")

    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if field not in data
    ]

    if missing_fields:
        fail(
            "Missing fields: "
            + ", ".join(missing_fields)
        )

    entry = {
        field: clean_value(data[field], field)
        for field in REQUIRED_FIELDS
    }

    # Validate timestamp format.
    if not TIMESTAMP_PATTERN.fullmatch(
        entry["timestamp"]
    ):
        fail(
            "Timestamp must use "
            "YYYY-MM-DD HH:MM:SS TIMEZONE format."
        )

    # Validate that the calendar date and clock time are real.
    try:
        datetime.strptime(
            entry["timestamp"][:19],
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        fail(
            "Timestamp contains an invalid date or time."
        )

    if not AUDIT_ID_PATTERN.fullmatch(entry["audit_id"]):
        fail("Audit ID must be a valid lowercase UUID.")

    # Validate approval status.
    if entry["approval_required"] not in ALLOWED_APPROVAL:
        fail(
            "approval_required must be Yes or No."
        )

    # Validate action outcome.
    if entry["outcome"] not in ALLOWED_OUTCOMES:
        fail("Invalid audit outcome.")

    return entry


# ---------------------------------------------------------
# 3A. Existing Audit Log Validation
# ---------------------------------------------------------

def validate_existing_records(existing_content):
    """
    Validate writer-generated records already in the audit log.

    Legacy records without Audit IDs are accepted unchanged.
    Records containing Audit IDs must satisfy the current schema.
    Audit IDs must be unique throughout the log.
    """

    try:
        content = existing_content.decode("utf-8")
    except UnicodeDecodeError:
        fail("Existing audit log contains invalid UTF-8.")

    # Each Markdown separator marks the beginning of a new section.
    sections = re.split(
        r"(?m)^\s*---\s*$",
        content
    )

    field_labels = {
        "audit_id": "Audit ID",
        "timestamp": "Timestamp",
        "requesting_party": "Requesting Party",
        "responsible_agent": "Responsible Agent",
        "action_requested": "Action Requested",
        "purpose": "Purpose",
        "affected_resources": "Affected Resources",
        "approval_required": "Approval Required",
        "authorized_by": "Authorized By",
        "outcome": "Outcome",
        "verification": "Verification",
        "additional_notes": "Additional Notes",
    }

    existing_ids = set()

    for section in sections:
        lines = section.splitlines()

        # Find Audit ID fields in this section.
        audit_id_lines = [
            line
            for line in lines
            if re.match(
                r"^\s*-\s+\*\*Audit ID:\*\*",
                line
            )
        ]

        # Reject malformed attempts to specify an Audit ID.
        if not audit_id_lines:
            if any("Audit ID" in line for line in lines):
                fail(
                    "Malformed Audit ID field "
                    "in existing audit log."
                )

            # Legacy record or template without an Audit ID.
            continue

        if len(audit_id_lines) != 1:
            fail(
                "Multiple Audit ID fields found "
                "in an existing record."
            )

        record = {}

        for line in lines:
            match = re.match(
                r"^\s*-\s+\*\*([^*]+):\*\*\s*(.*)$",
                line
            )

            if not match:
                continue

            label = match.group(1)
            value = match.group(2)

            for field, expected_label in field_labels.items():
                if label == expected_label:
                    if field in record:
                        fail(
                            f"Duplicate field in existing record: "
                            f"{expected_label}"
                        )

                    record[field] = value
                    break

        # Reuse the same validation rules as incoming records.
        validated_record = validate_entry(record)

        audit_id = validated_record["audit_id"]

        if audit_id in existing_ids:
            fail(
                f"Duplicate Audit ID in existing log: {audit_id}"
            )

        existing_ids.add(audit_id)

    return existing_ids


# ---------------------------------------------------------
# 4. Audit Entry Formatting
# ---------------------------------------------------------

def format_entry(entry):
    """
    Convert validated input into the standard Markdown format.
    """

    title = entry["action_requested"]

    return (
        f"\n---\n"
        f"### {title}\n\n"
        f"- **Audit ID:** {entry['audit_id']}\n"
        f"- **Timestamp:** {entry['timestamp']}\n"
        f"- **Requesting Party:** {entry['requesting_party']}\n"
        f"- **Responsible Agent:** {entry['responsible_agent']}\n"
        f"- **Action Requested:** {entry['action_requested']}\n"
        f"- **Purpose:** {entry['purpose']}\n"
        f"- **Affected Resources:** {entry['affected_resources']}\n"
        f"- **Approval Required:** {entry['approval_required']}\n"
        f"- **Authorized By:** {entry['authorized_by']}\n"
        f"- **Outcome:** {entry['outcome']}\n"
        f"- **Verification:** {entry['verification']}\n"
        f"- **Additional Notes:** {entry['additional_notes']}\n"
    )


# ---------------------------------------------------------
# 5. Write All Bytes
# ---------------------------------------------------------

def write_all(file, data):
    """
    Write all bytes, handling short writes.
    """

    remaining = memoryview(data)

    while remaining:
        bytes_written = file.write(remaining)

        if bytes_written is None or bytes_written <= 0:
            raise OSError(
                "Unable to complete audit record write."
            )

        remaining = remaining[bytes_written:]


# ---------------------------------------------------------
# 6. Append Audit Entry
# ---------------------------------------------------------


def append_entry(entry):
    """
    Validate and append a record to the fixed audit log.

    Security:
        - Rejects a symbolic link used as the parent directory.
        - Opens the audit file relative to the verified directory.
        - Rejects a symbolic link used as the audit file itself.
        - Uses file locking to protect concurrent writes.
    """

    # Never trust callers to validate the entry beforehand.
    entry = validate_entry(entry)

    # Fail closed if the required filesystem protections
    # are unavailable on this platform.
    required_flags = (
        hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_DIRECTORY")
        and os.open in os.supports_dir_fd
    )

    if not required_flags:
        fail(
            "Required filesystem security features "
            "are not supported on this platform."
        )

    directory_fd = -1
    fd = -1

    try:
        # Open the parent directory without following a symlink.
        directory_flags = (
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
        )

        directory_fd = os.open(
            AUDIT_FILE.parent,
            directory_flags
        )

        # Open the audit file relative to the verified directory.
        # O_NOFOLLOW also rejects a symlink at the final component.
        file_flags = (
            os.O_RDWR
            | os.O_APPEND
            | os.O_NOFOLLOW
        )

        fd = os.open(
            AUDIT_FILE.name,
            file_flags,
            dir_fd=directory_fd
        )

    except OSError as exc:
        fail(f"Cannot securely open audit log: {exc}")

    try:
        file_info = os.fstat(fd)

        # Only allow regular files.
        if not stat.S_ISREG(file_info.st_mode):
            fail("Audit destination is not a regular file.")

        # Reject files with group or other permissions.
        if stat.S_IMODE(file_info.st_mode) & 0o077:
            fail(
                "Audit log permissions are too permissive. "
                "Required permissions: 600 or stricter."
            )

        with os.fdopen(fd, "r+b") as audit:
            fd = -1

            # Lock before inspecting existing records.
            fcntl.flock(
                audit.fileno(),
                fcntl.LOCK_EX
            )

            try:
                # Read existing audit records.
                audit.seek(0)
                existing_content = audit.read()

                # Validate all existing writer-generated records.
                existing_ids = validate_existing_records(
                    existing_content
                )

                # Reject an incoming ID already present in the log.
                if entry["audit_id"] in existing_ids:
                    fail(
                        f"Duplicate Audit ID: {entry['audit_id']}"
                    )

                # Append the new record.
                audit.seek(0, os.SEEK_END)

                new_record = format_entry(entry).encode("utf-8")

                write_all(audit, new_record)

                audit.flush()
                os.fsync(audit.fileno())

                # Verify that the Audit ID was written successfully.
                audit.seek(0)

                verification_line = (
                    f"- **Audit ID:** {entry['audit_id']}\n"
                ).encode("utf-8")

                if verification_line not in audit.read():
                    raise OSError(
                        f"Post-write verification failed for "
                        f"Audit ID: {entry['audit_id']}"
                    )

            finally:
                fcntl.flock(
                    audit.fileno(),
                    fcntl.LOCK_UN
                )

    finally:
        if fd != -1:
            os.close(fd)

        if directory_fd != -1:
            os.close(directory_fd)

    print("Audit entry appended successfully.")
    print(f"Audit ID: {entry['audit_id']}")
    print(f"Destination: {AUDIT_FILE}")


# ---------------------------------------------------------
# 7. Main Execution
# ---------------------------------------------------------

def read_input(stream):
    """
    Read JSON input with a strict maximum size.
    """

    raw_input = stream.read(MAX_INPUT_SIZE + 1)

    if len(raw_input) > MAX_INPUT_SIZE:
        fail(
            f"Input exceeds the maximum permitted size "
            f"of {MAX_INPUT_SIZE} bytes."
        )

    try:
        return raw_input.decode("utf-8")

    except UnicodeDecodeError:
        fail("Input must contain valid UTF-8.")


def main():
    """
    Read bounded JSON from standard input, validate it,
    and append the audit record.
    """

    raw_input = read_input(sys.stdin.buffer)

    try:
        data = json.loads(raw_input)

    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON input: {exc}")

    append_entry(data)


# ---------------------------------------------------------
# 8. Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
