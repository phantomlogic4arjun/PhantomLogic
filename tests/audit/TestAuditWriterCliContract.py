
import json
import os
import subprocess
import sys
import unittest
import uuid

from datetime import datetime, timezone
from pathlib import Path

from phantom_logic.database.DatabaseManager import DatabaseManager
from phantom_logic.database.repositories import AuditEventRepository


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class TestAuditWriterCliContract(unittest.TestCase):

    def create_entry(self, **overrides):
        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requesting_party": "Orchestrator",
            "responsible_agent": "Orchestrator",
            "action_requested": "CLI Integration Test",
            "purpose": "Verify CLI audit persistence",
            "affected_resources": "audit.audit_events",
            "approval_required": "No",
            "authorized_by": "Not Required",
            "outcome": "Successful",
            "verification": "CLI integration test",
            "additional_notes": (
                "Permanent CLI integration test record"
            ),
        }

        entry.update(overrides)

        return entry

    def create_subprocess_environment(self):
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        return environment

    def run_writer(self, payload):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "phantom_logic.audit.AuditWriter",
            ],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=REPOSITORY_ROOT,
            env=self.create_subprocess_environment(),
            timeout=15,
        )

    def assert_success(self, result, entry):
        self.assertEqual(
            result.returncode,
            0,
            result.stderr,
        )

        self.assertIn(
            "Audit event persisted successfully.",
            result.stdout,
        )

        self.assertIn(
            entry["audit_id"],
            result.stdout,
        )

        self.assertTrue(
            AuditEventRepository.exists(entry["audit_id"])
        )

    def assert_failure(self, result):
        self.assertNotEqual(result.returncode, 0)

        self.assertNotIn(
            "Audit event persisted successfully.",
            result.stdout,
        )

    def test_successful_cli_persistence(self):
        entry = self.create_entry()

        result = self.run_writer(entry)

        self.assert_success(result, entry)

    def test_all_permitted_outcomes(self):
        outcomes = [
            "Successful",
            "Failed",
            "Partially Completed",
            "Cancelled",
            "Blocked",
        ]

        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                entry = self.create_entry(outcome=outcome)

                result = self.run_writer(entry)

                self.assert_success(result, entry)

    def test_both_approval_values(self):
        for approval in ["Yes", "No"]:
            with self.subTest(approval=approval):
                entry = self.create_entry(
                    approval_required=approval
                )

                result = self.run_writer(entry)

                self.assert_success(result, entry)

    def test_invalid_json_rejected(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "phantom_logic.audit.AuditWriter",
            ],
            input="{invalid json}",
            text=True,
            capture_output=True,
            cwd=REPOSITORY_ROOT,
            env=self.create_subprocess_environment(),
            timeout=15,
        )

        self.assert_failure(result)

    def test_missing_field_rejected(self):
        entry = self.create_entry()
        del entry["purpose"]

        result = self.run_writer(entry)

        self.assert_failure(result)

    def test_invalid_timestamp_rejected(self):
        entry = self.create_entry(
            timestamp="2026-11-23T20:30:00"
        )

        result = self.run_writer(entry)

        self.assert_failure(result)

    def test_invalid_outcome_rejected(self):
        entry = self.create_entry(
            outcome="Unknown"
        )

        result = self.run_writer(entry)

        self.assert_failure(result)

    def test_duplicate_audit_id_rejected(self):
        entry = self.create_entry()

        first_result = self.run_writer(entry)

        self.assert_success(first_result, entry)

        second_result = self.run_writer(entry)

        self.assert_failure(second_result)

        self.assertIn(
            "Duplicate Audit ID",
            second_result.stderr,
        )

        self.assertTrue(
            AuditEventRepository.exists(entry["audit_id"])
        )

    def test_invalid_utf8_rejected(self):
        environment = self.create_subprocess_environment()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "phantom_logic.audit.AuditWriter",
            ],
            input=b"\xff\xfe",
            capture_output=True,
            cwd=REPOSITORY_ROOT,
            env=environment,
            timeout=15,
        )

        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
