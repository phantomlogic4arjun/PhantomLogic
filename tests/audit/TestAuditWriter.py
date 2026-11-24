
import io
import json
import unittest

from datetime import datetime, timezone
from unittest.mock import patch

from phantom_logic.audit import AuditWriter


class TestAuditWriter(unittest.TestCase):

    def create_entry(self):
        return {
            "audit_id": "a84f9c21-7d62-4a15-9b30-6f8e2c1d45a7",
            "timestamp": "2026-11-23T20:30:00-05:00",
            "requesting_party": "Orchestrator",
            "responsible_agent": "Developer",
            "action_requested": "Audit Writer Unit Test",
            "purpose": "Verify audit writer validation",
            "affected_resources": "AuditEventRepository",
            "approval_required": "No",
            "authorized_by": "Not Required",
            "outcome": "Successful",
            "verification": "Unit test verification",
            "additional_notes": "Automated validation test",
        }

    def test_valid_entry_accepted(self):
        entry = AuditWriter.validate_entry(self.create_entry())

        self.assertEqual(len(entry), 12)
        self.assertEqual(
            entry["audit_id"],
            "a84f9c21-7d62-4a15-9b30-6f8e2c1d45a7",
        )

    def test_timestamp_normalized_to_utc(self):
        entry = AuditWriter.validate_entry(self.create_entry())

        self.assertEqual(
            entry["timestamp"],
            datetime(2026, 11, 24, 1, 30, tzinfo=timezone.utc),
        )

    def test_utc_z_timestamp_accepted(self):
        timestamp = AuditWriter.parse_timestamp(
            "2026-11-24T01:30:00Z"
        )

        self.assertEqual(
            timestamp,
            datetime(2026, 11, 24, 1, 30, tzinfo=timezone.utc),
        )

    def test_fractional_seconds_accepted(self):
        timestamp = AuditWriter.parse_timestamp(
            "2026-11-24T01:30:00.123456+00:00"
        )

        self.assertEqual(timestamp.microsecond, 123456)

    def test_timezone_naive_timestamp_rejected(self):
        with self.assertRaises(SystemExit):
            AuditWriter.parse_timestamp(
                "2026-11-23T20:30:00"
            )

    def test_invalid_calendar_date_rejected(self):
        with self.assertRaises(SystemExit):
            AuditWriter.parse_timestamp(
                "2026-02-30T20:30:00Z"
            )

    def test_legacy_timezone_abbreviation_rejected(self):
        with self.assertRaises(SystemExit):
            AuditWriter.parse_timestamp(
                "2026-11-23 20:30:00 EST"
            )

    def test_invalid_timestamp_rejected(self):
        with self.assertRaises(SystemExit):
            AuditWriter.parse_timestamp("invalid")

    def test_missing_required_field_rejected(self):
        entry = self.create_entry()
        del entry["purpose"]

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_empty_field_rejected(self):
        entry = self.create_entry()
        entry["purpose"] = "   "

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_non_string_field_rejected(self):
        entry = self.create_entry()
        entry["purpose"] = 123

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_json_array_rejected(self):
        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry([])

    def test_invalid_uuid_rejected(self):
        entry = self.create_entry()
        entry["audit_id"] = "INVALID-UUID"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_uppercase_uuid_rejected(self):
        entry = self.create_entry()
        entry["audit_id"] = (
            "A84F9C21-7D62-4A15-9B30-6F8E2C1D45A7"
        )

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_invalid_approval_rejected(self):
        entry = self.create_entry()
        entry["approval_required"] = "Maybe"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_invalid_outcome_rejected(self):
        entry = self.create_entry()
        entry["outcome"] = "Unknown"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_all_permitted_outcomes_accepted(self):
        for outcome in AuditWriter.ALLOWED_OUTCOMES:
            with self.subTest(outcome=outcome):
                entry = self.create_entry()
                entry["outcome"] = outcome

                validated = AuditWriter.validate_entry(entry)

                self.assertEqual(validated["outcome"], outcome)

    def test_both_approval_values_accepted(self):
        for approval in AuditWriter.ALLOWED_APPROVAL:
            with self.subTest(approval=approval):
                entry = self.create_entry()
                entry["approval_required"] = approval

                validated = AuditWriter.validate_entry(entry)

                self.assertEqual(
                    validated["approval_required"],
                    approval,
                )

    def test_multiline_value_rejected(self):
        entry = self.create_entry()
        entry["purpose"] = "First line\nSecond line"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_carriage_return_rejected(self):
        entry = self.create_entry()
        entry["purpose"] = "First line\rSecond line"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_control_character_rejected(self):
        entry = self.create_entry()
        entry["purpose"] = "Invalid\x01value"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_template_placeholder_rejected(self):
        entry = self.create_entry()
        entry["purpose"] = "[Action Title]"

        with self.assertRaises(SystemExit):
            AuditWriter.validate_entry(entry)

    def test_input_at_size_limit_accepted(self):
        raw = b"x" * AuditWriter.MAX_INPUT_SIZE

        result = AuditWriter.read_input(
            io.BytesIO(raw)
        )

        self.assertEqual(len(result), AuditWriter.MAX_INPUT_SIZE)

    def test_input_above_size_limit_rejected(self):
        raw = b"x" * (AuditWriter.MAX_INPUT_SIZE + 1)

        with self.assertRaises(SystemExit):
            AuditWriter.read_input(
                io.BytesIO(raw)
            )

    def test_invalid_utf8_rejected(self):
        with self.assertRaises(SystemExit):
            AuditWriter.read_input(
                io.BytesIO(b"\xff\xfe")
            )

    def test_json_serialization_of_entry(self):
        serialized = json.dumps(self.create_entry())

        parsed = json.loads(serialized)

        self.assertEqual(
            parsed["audit_id"],
            self.create_entry()["audit_id"],
        )

    def test_persistence_failure_is_not_suppressed(self):
        entry = AuditWriter.validate_entry(self.create_entry())

        with patch.object(
            AuditWriter.AuditEventRepository,
            "insert",
            side_effect=RuntimeError("Database unavailable"),
        ):
            with self.assertRaises(SystemExit):
                AuditWriter.persist_entry(entry)


if __name__ == "__main__":
    unittest.main()
