
import unittest
import uuid

from datetime import datetime, timezone

from sqlalchemy import text

from phantom_logic.database.DatabaseManager import DatabaseManager
from phantom_logic.database.DatabaseConfig import DatabaseConfig
from phantom_logic.database.repositories import AuditEventRepository


class TestAuditEventRepository(unittest.TestCase):

    def create_entry(self, audit_id=None):
        if audit_id is None:
            audit_id = str(uuid.uuid4())

        return {
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc),
            "requesting_party": "RepositoryIntegrationTest",
            "responsible_agent": "AuditEventRepository",
            "action_requested": "Insert test audit event",
            "purpose": "Verify PostgreSQL audit persistence",
            "affected_resources": "audit.audit_events",
            "approval_required": "No",
            "authorized_by": "Not Required",
            "outcome": "Successful",
            "verification": "Repository integration test",
            "additional_notes": (
                "Permanent integration test record"
            ),
        }

    def test_database_connection_uses_application_role(self):
        session = DatabaseManager.get_session()

        try:
            current_user = session.scalar(
                text("SELECT current_user")
            )

            current_database = session.scalar(
                text("SELECT current_database()")
            )

            self.assertEqual(
                current_user,
                "phantom_logic_app",
            )

            self.assertEqual(
                current_database,
                DatabaseConfig.get_database_url().database,
            )

        finally:
            session.close()

    def test_insert_and_retrieve_audit_event(self):
        entry = self.create_entry()

        AuditEventRepository.insert(entry)

        self.assertTrue(
            AuditEventRepository.exists(entry["audit_id"])
        )

    def test_nonexistent_audit_event_returns_false(self):
        audit_id = str(uuid.uuid4())

        self.assertFalse(
            AuditEventRepository.exists(audit_id)
        )

    def test_duplicate_audit_id_is_rejected(self):
        entry = self.create_entry()

        AuditEventRepository.insert(entry)

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate Audit ID",
        ):
            AuditEventRepository.insert(entry)

        self.assertTrue(
            AuditEventRepository.exists(entry["audit_id"])
        )

    def test_invalid_outcome_is_rejected_by_database(self):
        entry = self.create_entry()
        entry["outcome"] = "Invalid Outcome"

        with self.assertRaises(RuntimeError):
            AuditEventRepository.insert(entry)

        self.assertFalse(
            AuditEventRepository.exists(entry["audit_id"])
        )

    def test_application_role_has_required_permissions(self):
        session = DatabaseManager.get_session()

        try:
            privileges = session.execute(
                text("""
                    SELECT
                        has_schema_privilege(
                            current_user,
                            'audit',
                            'USAGE'
                        ) AS schema_usage,

                        has_schema_privilege(
                            current_user,
                            'audit',
                            'CREATE'
                        ) AS schema_create,

                        has_table_privilege(
                            current_user,
                            'audit.audit_events',
                            'SELECT'
                        ) AS can_select,

                        has_table_privilege(
                            current_user,
                            'audit.audit_events',
                            'INSERT'
                        ) AS can_insert,

                        has_table_privilege(
                            current_user,
                            'audit.audit_events',
                            'UPDATE'
                        ) AS can_update,

                        has_table_privilege(
                            current_user,
                            'audit.audit_events',
                            'DELETE'
                        ) AS can_delete,

                        has_table_privilege(
                            current_user,
                            'audit.audit_events',
                            'TRUNCATE'
                        ) AS can_truncate
                """)
            ).mappings().one()

            self.assertTrue(privileges["schema_usage"])
            self.assertFalse(privileges["schema_create"])

            self.assertTrue(privileges["can_select"])
            self.assertTrue(privileges["can_insert"])

            self.assertFalse(privileges["can_update"])
            self.assertFalse(privileges["can_delete"])
            self.assertFalse(privileges["can_truncate"])

        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
