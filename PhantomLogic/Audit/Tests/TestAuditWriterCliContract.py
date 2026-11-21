import json
import shutil
import subprocess
import tempfile
import unittest
import uuid

from datetime import datetime
from pathlib import Path


class TestAuditWriterCliContract(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(
            prefix="phantom-orchestrator-audit-"
        )
        self.test_dir = Path(self.temp_dir.name)

        source = (
            Path(__file__).resolve().parents[1] / "AuditWriter.py"
        )

        self.writer = self.test_dir / "AuditWriter.py"
        self.log = self.test_dir / "AuditLog.md"

        shutil.copy2(source, self.writer)
        self.log.touch()
        self.log.chmod(0o600)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_entry(self, **overrides):
        timestamp = datetime.now().astimezone().strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )

        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": timestamp,
            "requesting_party": "Orchestrator",
            "responsible_agent": "Orchestrator",
            "action_requested": "Integration Test Action",
            "purpose": "Verify Orchestrator audit integration",
            "affected_resources": "Temporary test audit log",
            "approval_required": "No",
            "authorized_by": "Not Required",
            "outcome": "Successful",
            "verification": "Isolated integration test",
            "additional_notes": (
                "Temporary test; not a production audit record"
            ),
        }

        entry.update(overrides)
        return entry

    def run_writer(self, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        return subprocess.run(
            ["python3", str(self.writer)],
            input=payload,
            text=True,
            capture_output=True,
        )

    def assert_success(self, result, entry):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Audit entry appended successfully.",
            result.stdout,
        )
        self.assertIn(entry["audit_id"], result.stdout)
        self.assertIn(entry["audit_id"], self.log.read_text())

    def assert_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(
            "Audit entry appended successfully.",
            result.stdout,
        )

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
                entry = self.make_entry(outcome=outcome)
                result = self.run_writer(entry)

                self.assert_success(result, entry)
                self.assertIn(
                    f"**Outcome:** {outcome}",
                    self.log.read_text(),
                )

    def test_approval_not_required(self):
        entry = self.make_entry(
            approval_required="No",
            authorized_by="Not Required",
        )

        result = self.run_writer(entry)

        self.assert_success(result, entry)
        content = self.log.read_text()
        self.assertIn("**Approval Required:** No", content)
        self.assertIn("**Authorized By:** Not Required", content)

    def test_approval_granted(self):
        entry = self.make_entry(
            approval_required="Yes",
            authorized_by="Owner",
            outcome="Successful",
        )

        result = self.run_writer(entry)

        self.assert_success(result, entry)
        content = self.log.read_text()
        self.assertIn("**Approval Required:** Yes", content)
        self.assertIn("**Authorized By:** Owner", content)

    def test_unapproved_action_recorded_as_blocked(self):
        entry = self.make_entry(
            approval_required="Yes",
            authorized_by="Not Authorized",
            outcome="Blocked",
        )

        result = self.run_writer(entry)

        self.assert_success(result, entry)
        content = self.log.read_text()
        self.assertIn("**Authorized By:** Not Authorized", content)
        self.assertIn("**Outcome:** Blocked", content)

    def test_missing_required_field_rejected(self):
        entry = self.make_entry()
        entry.pop("purpose")

        result = self.run_writer(entry)

        self.assert_failure(result)
        self.assertEqual(self.log.read_text(), "")

    def test_invalid_outcome_rejected(self):
        entry = self.make_entry(outcome="Unknown")

        result = self.run_writer(entry)

        self.assert_failure(result)
        self.assertEqual(self.log.read_text(), "")

    def test_invalid_approval_value_rejected(self):
        entry = self.make_entry(approval_required="Pending")

        result = self.run_writer(entry)

        self.assert_failure(result)
        self.assertEqual(self.log.read_text(), "")

    def test_missing_required_fields_rejected_cli(self):
        fields = [
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
        for field in fields:
            with self.subTest(field=field):
                entry = self.make_entry()
                del entry[field]
                result = self.run_writer(entry)
                self.assert_failure(result)
                self.assertEqual(self.log.read_text(), "")
    def test_duplicate_audit_id_rejected(self):
        entry = self.make_entry()

        first = self.run_writer(entry)
        self.assert_success(first, entry)

        second = self.run_writer(entry)

        self.assert_failure(second)
        self.assertEqual(
            self.log.read_text().count(entry["audit_id"]),
            1,
        )

    def test_invalid_json_rejected(self):
        result = self.run_writer("{invalid-json")

        self.assert_failure(result)
        self.assertEqual(self.log.read_text(), "")


if __name__ == "__main__":
    unittest.main()
