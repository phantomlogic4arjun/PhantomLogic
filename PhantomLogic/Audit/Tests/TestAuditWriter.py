
#!/usr/bin/env python3
"""
Phantom Logic - Audit Writer Tests

Purpose:
    Automated tests for AuditWriter.py.

Testing approach:
    - Uses Python's built-in unittest framework.
    - Uses temporary directories and isolated audit logs.
    - Never modifies the production AuditLog.md.
    - Tests both individual functions and command-line execution.
    - Tests concurrent writer processes.
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path


# ---------------------------------------------------------
# 1. Test Configuration
# ---------------------------------------------------------

AUDIT_WRITER_PATH = (
    Path(__file__).resolve().parent.parent
    / "AuditWriter.py"
)


# ---------------------------------------------------------
# 2. Test Class
# ---------------------------------------------------------


class TestAuditWriter(unittest.TestCase):

    # -----------------------------------------------------
    # 1. Test Setup and Teardown
    # -----------------------------------------------------

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "audit_writer",
            AUDIT_WRITER_PATH
        )

        cls.writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.writer)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

        self.audit_file = self.test_dir / "AuditLog.md"

        self.audit_file.write_text(
            "# Temporary Audit Log\n",
            encoding="utf-8"
        )

        os.chmod(self.audit_file, 0o600)

        self.writer.AUDIT_FILE = self.audit_file

        self.cli_writer = self.test_dir / "AuditWriter.py"

        shutil.copy2(
            AUDIT_WRITER_PATH,
            self.cli_writer
        )

    def tearDown(self):
        self.writer.AUDIT_FILE = (
            AUDIT_WRITER_PATH.parent / "AuditLog.md"
        )

        self.temp_dir.cleanup()

    # -----------------------------------------------------
    # 2. Reusable Test Data and Helpers
    # -----------------------------------------------------

    def create_entry(self, audit_id=None):

        if audit_id is None:
            audit_id = (
                "a84f9c21-7d62-4a15-9b30-6f8e2c1d45a7"
            )

        return {
            "audit_id": audit_id,
            "timestamp": "2026-11-20 23:30:00 EST",
            "requesting_party": "Orchestrator",
            "responsible_agent": "Developer",
            "action_requested": "Audit Writer Unit Test",
            "purpose": "Verify audit writer functionality",
            "affected_resources": "Temporary test audit log",
            "approval_required": "No",
            "authorized_by": "N/A - approval not required",
            "outcome": "Successful",
            "verification": "Unit test verification",
            "additional_notes": "Isolated automated test"
        }

    def run_cli(self, entry=None, raw_input=None):

        if raw_input is None:
            raw_input = json.dumps(entry)

        return subprocess.run(
            [sys.executable, str(self.cli_writer)],
            input=raw_input,
            capture_output=True,
            text=True,
            timeout=10
        )

    def assert_log_unchanged_after_rejection(
        self,
        entry,
        expected_error=None
    ):

        original_content = self.audit_file.read_bytes()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        self.assertEqual(
            self.audit_file.read_bytes(),
            original_content
        )

    # -----------------------------------------------------
    # 3. Successful Operations
    # -----------------------------------------------------

    def test_valid_entry_appends_successfully(self):

        entry = self.create_entry()

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        contents = self.audit_file.read_text()

        self.assertIn(entry["audit_id"], contents)

        self.assertEqual(
            contents.count(entry["audit_id"]),
            1
        )

    def test_secure_file_permissions_accepted(self):

        entry = self.create_entry()

        os.chmod(self.audit_file, 0o600)

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        self.assertIn(
            entry["audit_id"],
            self.audit_file.read_text()
        )

    def test_command_line_execution_succeeds(self):

        entry = self.create_entry()

        result = self.run_cli(entry=entry)

        self.assertEqual(result.returncode, 0)

        self.assertIn(
            "Audit entry appended successfully.",
            result.stdout
        )

        self.assertIn(
            entry["audit_id"],
            self.audit_file.read_text()
        )

    def test_empty_audit_log_accepts_entry(self):

        self.audit_file.write_text("", encoding="utf-8")
        os.chmod(self.audit_file, 0o600)

        entry = self.create_entry()

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        contents = self.audit_file.read_text()

        self.assertIn(entry["audit_id"], contents)
        self.assertEqual(contents.count(entry["audit_id"]), 1)

    def test_log_without_trailing_newline_accepts_entry(self):

        original_content = "# Existing Audit Log"

        self.audit_file.write_text(
            original_content,
            encoding="utf-8"
        )

        entry = self.create_entry()

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        contents = self.audit_file.read_text()

        self.assertIn(
            original_content + "\n---\n",
            contents
        )

        self.assertIn(entry["audit_id"], contents)

    def test_unicode_content_preserved(self):

        entry = self.create_entry()

        entry["requesting_party"] = "Orchestrator – José"
        entry["purpose"] = "Verify Unicode: café, naïve, 東京"
        entry["additional_notes"] = "Unicode test – ✓"

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        contents = self.audit_file.read_text(
            encoding="utf-8"
        )

        self.assertIn("José", contents)
        self.assertIn("café", contents)
        self.assertIn("東京", contents)
        self.assertIn("✓", contents)

    # -----------------------------------------------------
    # 4. Input Validation
    # -----------------------------------------------------

    def test_missing_required_field_rejected(self):

        entry = self.create_entry()
        del entry["purpose"]

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_empty_field_rejected(self):

        entry = self.create_entry()
        entry["purpose"] = ""

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_non_string_field_rejected(self):

        entry = self.create_entry()
        entry["purpose"] = 12345

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_json_rejected(self):

        result = self.run_cli(
            raw_input="{ invalid json }"
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            "Invalid JSON input",
            result.stderr
        )

        self.assertEqual(
            self.audit_file.read_text(),
            "# Temporary Audit Log\n"
        )

    def test_json_array_rejected(self):

        result = self.run_cli(
            raw_input='["invalid", "audit", "record"]'
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            "Input must be a JSON object.",
            result.stderr
        )

        self.assertEqual(
            self.audit_file.read_text(),
            "# Temporary Audit Log\n"
        )

    def test_invalid_utf8_input_rejected(self):

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.read_input(
                    io.BytesIO(b"\xff\xfe\xfa")
                )

    def test_invalid_outcome_rejected(self):

        entry = self.create_entry()
        entry["outcome"] = "Approved"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_approval_status_rejected(self):

        entry = self.create_entry()
        entry["approval_required"] = "Maybe"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_multiline_input_rejected(self):

        entry = self.create_entry()

        entry["purpose"] = (
            "Valid purpose\n"
            "Injected audit entry"
        )

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_control_characters_rejected(self):

        entry = self.create_entry()
        entry["purpose"] = "Invalid\x01value"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_template_placeholder_rejected(self):

        entry = self.create_entry()
        entry["action_requested"] = "[Action Title]"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_audit_id_rejected(self):

        entry = self.create_entry()
        entry["audit_id"] = "not-a-valid-uuid"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_timestamp_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "20-11-2026 23:30"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_direct_append_with_invalid_entry_rejected(self):

        entry = self.create_entry()
        entry["outcome"] = "Unknown"

        self.assert_log_unchanged_after_rejection(entry)

    def test_direct_append_with_missing_field_rejected(self):

        entry = self.create_entry()
        del entry["purpose"]

        self.assert_log_unchanged_after_rejection(entry)

    def test_existing_log_preserved_after_failed_append(self):

        original_content = (
            "# Existing Audit Log\n"
            "### Previous Audit Entry\n"
            "- **Audit ID:** "
            "99999999-9999-4999-8999-999999999999\n"
        )

        self.audit_file.write_text(
            original_content,
            encoding="utf-8"
        )

        entry = self.create_entry()
        entry["outcome"] = "Invalid Outcome"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

        self.assertEqual(
            self.audit_file.read_text(),
            original_content
        )

    def test_invalid_input_does_not_modify_log(self):

        original_content = self.audit_file.read_text()

        result = self.run_cli(
            raw_input='{"audit_id": "invalid"}'
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertEqual(
            self.audit_file.read_text(),
            original_content
        )

    # -----------------------------------------------------
    # 5. Timestamp Validation
    # -----------------------------------------------------

    def test_impossible_calendar_date_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "2026-19-45 12:30:00 UTC"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_day_for_month_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "2026-02-30 12:30:00 UTC"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_hour_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "2026-11-20 25:30:00 UTC"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_minute_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "2026-11-20 12:75:00 UTC"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_invalid_second_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "2026-11-20 12:30:75 UTC"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    def test_leap_year_date_accepted(self):

        entry = self.create_entry()
        entry["timestamp"] = "2024-02-29 12:30:00 UTC"

        validated = self.writer.validate_entry(entry)

        self.assertEqual(
            validated["timestamp"],
            "2024-02-29 12:30:00 UTC"
        )

    def test_non_leap_year_february_29_rejected(self):

        entry = self.create_entry()
        entry["timestamp"] = "2025-02-29 12:30:00 UTC"

        with self.assertRaises(SystemExit):
            self.writer.validate_entry(entry)

    # -----------------------------------------------------
    # 6. Duplicate Detection
    # -----------------------------------------------------

    def test_duplicate_audit_id_rejected(self):

        entry = self.create_entry()

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        contents = self.audit_file.read_text()

        self.assertEqual(
            contents.count(entry["audit_id"]),
            1
        )

    def test_duplicate_existing_audit_id_rejected(self):

        entry = self.create_entry()

        audit_id_line = (
            f"- **Audit ID:** {entry['audit_id']}\n"
        )

        self.audit_file.write_text(
            "# Audit Log\n"
            + audit_id_line
            + audit_id_line,
            encoding="utf-8"
        )

        incoming_entry = self.create_entry(
            "b95f0d32-8e73-4b16-a240-7c9d1e5f6382"
        )

        self.assert_log_unchanged_after_rejection(
            incoming_entry
        )

    def test_duplicate_ids_already_in_existing_log_rejected(self):

        entry = self.create_entry()

        valid_record = self.writer.format_entry(entry)

        self.audit_file.write_text(
            "# Audit Log\n"
            + valid_record
            + valid_record,
            encoding="utf-8"
        )

        incoming_entry = self.create_entry(
            "b95f0d32-8e73-4b16-a240-7c9d1e5f6382"
        )

        self.assert_log_unchanged_after_rejection(
            incoming_entry
        )

    # -----------------------------------------------------
    # 7. Filesystem Security
    # -----------------------------------------------------

    def test_symlink_destination_rejected(self):

        protected_file = self.test_dir / "ProtectedLog.md"

        protected_file.write_text(
            "Protected contents\n",
            encoding="utf-8"
        )

        os.chmod(protected_file, 0o600)

        self.audit_file.unlink()
        self.audit_file.symlink_to(protected_file)

        entry = self.create_entry()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        self.assertEqual(
            protected_file.read_text(),
            "Protected contents\n"
        )

    def test_parent_directory_symlink_rejected(self):

        real_directory = self.test_dir / "RealAudit"
        linked_directory = self.test_dir / "LinkedAudit"

        real_directory.mkdir()

        protected_file = real_directory / "AuditLog.md"

        protected_file.write_text(
            "# Protected Audit Log\n",
            encoding="utf-8"
        )

        os.chmod(protected_file, 0o600)

        linked_directory.symlink_to(
            real_directory,
            target_is_directory=True
        )

        self.writer.AUDIT_FILE = (
            linked_directory / "AuditLog.md"
        )

        entry = self.create_entry()

        original_content = protected_file.read_bytes()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        self.assertEqual(
            protected_file.read_bytes(),
            original_content
        )

    def test_directory_destination_rejected(self):

        self.audit_file.unlink()
        self.audit_file.mkdir()

        entry = self.create_entry()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        self.assertEqual(
            list(self.audit_file.iterdir()),
            []
        )

    def test_fifo_destination_rejected(self):

        self.audit_file.unlink()
        os.mkfifo(self.audit_file)

        entry = self.create_entry()

        result = self.run_cli(entry=entry)

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            "Audit destination is not a regular file.",
            result.stderr
        )

    def test_insecure_file_permissions_rejected(self):

        entry = self.create_entry()

        os.chmod(self.audit_file, 0o644)

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        self.assertNotIn(
            entry["audit_id"],
            self.audit_file.read_text()
        )

    def test_missing_audit_log_rejected(self):

        self.audit_file.unlink()

        entry = self.create_entry()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.append_entry(entry)

        self.assertFalse(self.audit_file.exists())

    # -----------------------------------------------------
    # 8. Existing Audit Log Integrity
    # -----------------------------------------------------

    def test_legacy_records_without_audit_ids_accepted(self):

        legacy_log = (
            "# Audit Log\n"
            "### Historical Action\n"
            "- **Timestamp:** 2026-11-20 22:21:27 EST\n"
            "- **Outcome:** Successful\n"
        )

        self.audit_file.write_text(
            legacy_log,
            encoding="utf-8"
        )

        entry = self.create_entry()

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        contents = self.audit_file.read_text(
            encoding="utf-8"
        )

        self.assertIn(legacy_log, contents)
        self.assertIn(entry["audit_id"], contents)

    def test_malformed_existing_audit_id_rejected(self):

        self.audit_file.write_text(
            "# Audit Log\n"
            "### Existing Record\n"
            "- **Audit ID:** invalid-id\n",
            encoding="utf-8"
        )

        entry = self.create_entry()

        self.assert_log_unchanged_after_rejection(entry)

    def test_existing_writer_record_missing_field_rejected(self):

        entry = self.create_entry()

        valid_record = self.writer.format_entry(entry)

        corrupted_record = valid_record.replace(
            f"- **Purpose:** {entry['purpose']}\n",
            ""
        )

        self.audit_file.write_text(
            "# Audit Log\n" + corrupted_record,
            encoding="utf-8"
        )

        incoming_entry = self.create_entry(
            "b95f0d32-8e73-4b16-a240-7c9d1e5f6382"
        )

        self.assert_log_unchanged_after_rejection(
            incoming_entry
        )

    def test_existing_writer_record_invalid_outcome_rejected(self):

        entry = self.create_entry()

        valid_record = self.writer.format_entry(entry)

        corrupted_record = valid_record.replace(
            f"- **Outcome:** {entry['outcome']}\n",
            "- **Outcome:** Unknown\n"
        )

        self.audit_file.write_text(
            "# Audit Log\n" + corrupted_record,
            encoding="utf-8"
        )

        incoming_entry = self.create_entry(
            "b95f0d32-8e73-4b16-a240-7c9d1e5f6382"
        )

        self.assert_log_unchanged_after_rejection(
            incoming_entry
        )

    def test_existing_writer_record_invalid_timestamp_rejected(self):

        entry = self.create_entry()

        valid_record = self.writer.format_entry(entry)

        corrupted_record = valid_record.replace(
            f"- **Timestamp:** {entry['timestamp']}\n",
            "- **Timestamp:** 2026-19-45 25:75:90 UTC\n"
        )

        self.audit_file.write_text(
            "# Audit Log\n" + corrupted_record,
            encoding="utf-8"
        )

        incoming_entry = self.create_entry(
            "b95f0d32-8e73-4b16-a240-7c9d1e5f6382"
        )

        self.assert_log_unchanged_after_rejection(
            incoming_entry
        )

    def test_corrupted_existing_log_rejected(self):

        self.audit_file.write_bytes(
            b"# Audit Log\n"
            b"\xff\xfe\xfa"
        )

        entry = self.create_entry()

        self.assert_log_unchanged_after_rejection(entry)

    # -----------------------------------------------------
    # 9. Input Size Protection
    # -----------------------------------------------------

    def test_input_at_size_limit_accepted(self):

        exact_size_input = (
            b"A" * self.writer.MAX_INPUT_SIZE
        )

        result = self.writer.read_input(
            io.BytesIO(exact_size_input)
        )

        self.assertEqual(
            len(result.encode("utf-8")),
            self.writer.MAX_INPUT_SIZE
        )

    def test_input_above_size_limit_rejected(self):

        oversized_input = (
            b"A" * (self.writer.MAX_INPUT_SIZE + 1)
        )

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.writer.read_input(
                    io.BytesIO(oversized_input)
                )

    def test_oversized_cli_input_rejected(self):

        oversized_entry = self.create_entry()

        oversized_entry["additional_notes"] = (
            "A" * (64 * 1024)
        )

        original_content = self.audit_file.read_bytes()

        result = subprocess.run(
            [sys.executable, str(self.cli_writer)],
            input=json.dumps(oversized_entry).encode("utf-8"),
            capture_output=True,
            timeout=10
        )

        self.assertNotEqual(result.returncode, 0)

        self.assertIn(
            b"maximum permitted size",
            result.stderr
        )

        self.assertEqual(
            self.audit_file.read_bytes(),
            original_content
        )

    # -----------------------------------------------------
    # 10. Partial Write Handling
    # -----------------------------------------------------

    def test_partial_writes_handled(self):

        class ShortWriter:

            def __init__(self, max_bytes):
                self.max_bytes = max_bytes
                self.output = bytearray()

            def write(self, data):
                chunk = data[:self.max_bytes]
                self.output.extend(chunk)
                return len(chunk)

        original_data = b"Phantom Logic Audit Writer Test"

        fake_file = ShortWriter(max_bytes=5)

        self.writer.write_all(
            fake_file,
            original_data
        )

        self.assertEqual(
            bytes(fake_file.output),
            original_data
        )

    def test_zero_byte_write_rejected(self):

        class ZeroWriter:

            def write(self, data):
                return 0

        with self.assertRaises(OSError):
            self.writer.write_all(
                ZeroWriter(),
                b"Test data"
            )

    # -----------------------------------------------------
    # 11. Post-Write Verification
    # -----------------------------------------------------

    def test_post_write_verification_succeeds(self):

        entry = self.create_entry()

        with contextlib.redirect_stdout(io.StringIO()):
            self.writer.append_entry(entry)

        contents = self.audit_file.read_text()

        self.assertIn(
            entry["audit_id"],
            contents
        )

    def test_post_write_verification_failure_detected(self):

        entry = self.create_entry()

        original_formatter = self.writer.format_entry

        try:
            self.writer.format_entry = lambda entry: (
                "\n---\n"
                "### Incomplete Test Record\n"
            )

            with self.assertRaises(OSError):
                self.writer.append_entry(entry)

        finally:
            self.writer.format_entry = original_formatter

        contents = self.audit_file.read_text()

        self.assertNotIn(
            entry["audit_id"],
            contents
        )

        self.assertIn(
            "Incomplete Test Record",
            contents
        )

    # -----------------------------------------------------
    # 12. Concurrent Writes
    # -----------------------------------------------------

    def test_concurrent_writes_preserve_records(self):

        entry_one = self.create_entry(
            "11111111-1111-4111-8111-111111111111"
        )

        entry_two = self.create_entry(
            "22222222-2222-4222-8222-222222222222"
        )

        json_one = self.test_dir / "entry1.json"
        json_two = self.test_dir / "entry2.json"

        json_one.write_text(json.dumps(entry_one))
        json_two.write_text(json.dumps(entry_two))

        with json_one.open("r") as input_one, \
             json_two.open("r") as input_two:

            process_one = subprocess.Popen(
                [sys.executable, str(self.cli_writer)],
                stdin=input_one,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            process_two = subprocess.Popen(
                [sys.executable, str(self.cli_writer)],
                stdin=input_two,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout_one, stderr_one = process_one.communicate(
                timeout=10
            )

            stdout_two, stderr_two = process_two.communicate(
                timeout=10
            )

        self.assertEqual(process_one.returncode, 0, stderr_one)
        self.assertEqual(process_two.returncode, 0, stderr_two)

        contents = self.audit_file.read_text()

        self.assertEqual(
            contents.count(entry_one["audit_id"]),
            1
        )

        self.assertEqual(
            contents.count(entry_two["audit_id"]),
            1
        )

        self.assertIn(
            "Audit entry appended successfully.",
            stdout_one
        )

        self.assertIn(
            "Audit entry appended successfully.",
            stdout_two
        )

    def test_concurrent_duplicate_audit_ids_rejected(self):

        entry = self.create_entry(
            "33333333-3333-4333-8333-333333333333"
        )

        json_file = self.test_dir / "duplicate_entry.json"

        json_file.write_text(json.dumps(entry))

        with json_file.open("r") as input_one, \
             json_file.open("r") as input_two:

            process_one = subprocess.Popen(
                [sys.executable, str(self.cli_writer)],
                stdin=input_one,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            process_two = subprocess.Popen(
                [sys.executable, str(self.cli_writer)],
                stdin=input_two,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout_one, stderr_one = process_one.communicate(
                timeout=10
            )

            stdout_two, stderr_two = process_two.communicate(
                timeout=10
            )

        return_codes = sorted([
            process_one.returncode,
            process_two.returncode
        ])

        self.assertEqual(return_codes, [0, 1])

        combined_stdout = stdout_one + stdout_two
        combined_stderr = stderr_one + stderr_two

        self.assertEqual(
            combined_stdout.count(
                "Audit entry appended successfully."
            ),
            1
        )

        self.assertEqual(
            combined_stderr.count("Duplicate Audit ID"),
            1
        )

        contents = self.audit_file.read_text()

        self.assertEqual(
            contents.count(entry["audit_id"]),
            1
        )


# ---------------------------------------------------------
# 13. Test Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
