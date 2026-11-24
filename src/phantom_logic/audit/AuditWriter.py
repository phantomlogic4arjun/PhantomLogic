
#!/usr/bin/env python3

"""
Phantom Logic - Audit Writer

Purpose:
    Validate audit events and persist them to PostgreSQL.

Security:
    - Accepts input only through standard input.
    - Enforces a maximum input size.
    - Validates all required fields.
    - Rejects multiline and control-character input.
    - Rejects unfilled template placeholders.
    - Validates lowercase UUIDs.
    - Requires timezone-aware ISO 8601 timestamps.
    - Restricts approval and outcome values.
    - Uses the PostgreSQL primary key for duplicate prevention.
    - Uses the append-only AuditEventRepository for persistence.
    - Verifies successful persistence through a database read.

Usage:
    python -m phantom_logic.audit.AuditWriter

Input:
    Supply the audit JSON object through standard input.
"""

import json
import re
import sys

from datetime import datetime, timezone

from phantom_logic.database.repositories import AuditEventRepository


# ---------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------

MAX_INPUT_SIZE = 64 * 1024  # 64 KB

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

AUDIT_ID_PATTERN = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-"
    r"[a-f0-9]{4}-[a-f0-9]{12}$"
)


# ---------------------------------------------------------
# 2. Error Handling
# ---------------------------------------------------------

def fail(message):
    """
    Report an error and terminate without claiming success.
    """

    print(
        f"Audit Writer error: {message}",
        file=sys.stderr,
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

    if "\n" in value or "\r" in value:
        fail(f"Multiline input is not permitted: {field}")

    if any(ord(char) < 32 for char in value):
        fail(f"Control characters are not permitted: {field}")

    value = value.strip()

    if value in {
        "[Action Title]",
        "YYYY-MM-DD HH:MM:SS (Time Zone)",
    }:
        fail(f"Template placeholder not permitted: {field}")

    return value


def parse_timestamp(value):
    """
    Parse an ISO 8601 timestamp and normalize it to UTC.

    Accepted examples:
        2026-11-23T20:30:00-05:00
        2026-11-24T01:30:00Z
        2026-11-24T01:30:00.123456+00:00

    Timezone-naive timestamps are rejected.
    """

    try:
        normalized_value = value.replace("Z", "+00:00")
        timestamp = datetime.fromisoformat(normalized_value)

    except ValueError:
        fail(
            "Timestamp must be a valid ISO 8601 date and time "
            "with a timezone offset or Z."
        )

    if (
        timestamp.tzinfo is None
        or timestamp.utcoffset() is None
    ):
        fail(
            "Timestamp must include a timezone offset or Z."
        )

    return timestamp.astimezone(timezone.utc)


def validate_entry(data):
    """
    Validate the complete audit record.

    Returns a validated dictionary with timestamp converted
    to a timezone-aware UTC datetime.
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

    if not AUDIT_ID_PATTERN.fullmatch(entry["audit_id"]):
        fail("Audit ID must be a valid lowercase UUID.")

    entry["timestamp"] = parse_timestamp(
        entry["timestamp"]
    )

    if entry["approval_required"] not in ALLOWED_APPROVAL:
        fail("approval_required must be Yes or No.")

    if entry["outcome"] not in ALLOWED_OUTCOMES:
        fail("Invalid audit outcome.")

    return entry


# ---------------------------------------------------------
# 4. Input Reading
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


# ---------------------------------------------------------
# 5. Database Persistence
# ---------------------------------------------------------

def persist_entry(entry):
    """
    Persist and verify an audit event.

    The repository owns the database transaction.
    This function does not write directly to PostgreSQL.
    """

    try:
        AuditEventRepository.insert(entry)

    except ValueError as exc:
        fail(str(exc))

    except Exception as exc:
        fail(
            "Database persistence failed "
            f"({type(exc).__name__}): {exc}"
        )

    try:
        verified = AuditEventRepository.exists(
            entry["audit_id"]
        )

    except Exception as exc:
        fail(
            "The insert operation returned successfully, "
            "but database verification failed. "
            "The record may already have been committed. "
            f"Audit ID: {entry['audit_id']}. "
            f"Verification error: {exc}"
        )

    if not verified:
        fail(
            "Database verification failed. "
            f"Audit ID: {entry['audit_id']}"
        )

    print("Audit event persisted successfully.")
    print(f"Audit ID: {entry['audit_id']}")
    print("Destination: PostgreSQL audit.audit_events")


# ---------------------------------------------------------
# 6. Main Execution
# ---------------------------------------------------------

def main():
    """
    Read bounded JSON from standard input, validate it,
    and persist the audit event.
    """

    raw_input = read_input(sys.stdin.buffer)

    try:
        data = json.loads(raw_input)

    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON input: {exc}")

    entry = validate_entry(data)

    persist_entry(entry)


# ---------------------------------------------------------
# 7. Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
