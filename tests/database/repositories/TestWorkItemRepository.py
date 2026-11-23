
import unittest
from datetime import datetime, timezone

from phantom_logic.database.repositories.WorkItemRepository import (
    WorkItemRepository,
)
from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from sqlalchemy import delete
from dataclasses import replace
from sqlalchemy.exc import IntegrityError
from phantom_logic.database.DatabaseManager import DatabaseManager
from phantom_logic.database.models.WorkItemRecord import WorkItemRecord


class TestWorkItemRepository(unittest.TestCase):

    def test_work_item_can_be_converted_to_database_record(self):

        created_at = datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 11, 12, 45, tzinfo=timezone.utc)

        work_item = WorkItem(
            id="REQ-001",
            title="User login",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
            build_number="1.00",
            description="Implement user authentication.",
            state=WorkItemState.IN_WORK,
            priority="High",
            assigned_agent="Developer",
            created_at=created_at,
            updated_at=updated_at,
            authorized_by="ProductManager-01",
            authorized_at=created_at,
            authorization_reason="Approved for implementation.",
        )

        record = WorkItemRepository._to_record(work_item)

        self.assertEqual(record.id, work_item.id)
        self.assertEqual(record.title, work_item.title)
        self.assertEqual(record.description, work_item.description)
        self.assertEqual(record.work_item_type, "Requirement")
        self.assertEqual(record.state, "In Work")
        self.assertEqual(record.created_by, work_item.created_by)
        self.assertEqual(record.build_number, "1.00")
        self.assertEqual(record.priority, "High")
        self.assertEqual(record.assigned_agent, "Developer")
        self.assertEqual(record.created_at, created_at)
        self.assertEqual(record.updated_at, updated_at)
        self.assertEqual(record.authorized_by, "ProductManager-01")
        self.assertEqual(record.authorized_at, created_at)
        self.assertEqual(
            record.authorization_reason,
            "Approved for implementation.",
        )

    def test_code_review_state_can_be_converted_to_database_value(self):

        work_item = WorkItem(
            id="CRV-001",
            title="Review authentication implementation",
            work_item_type=WorkItemType.CODE_REVIEW_TASK,
            created_by="Developer",
            state=CodeReviewState.REVIEW,
        )

        record = WorkItemRepository._to_record(work_item)

        self.assertEqual(record.work_item_type, "Code Review Task")
        self.assertEqual(record.state, "Review")

    def test_child_records_preserve_relationships_and_collection_order(self):

        work_item = WorkItem(
            id="BUG-001",
            title="Incorrect inventory calculation",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            relationships=(
                WorkItemRelationship(
                    source_id="BUG-001",
                    target_id="REQ-001",
                    relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
                ),
                WorkItemRelationship(
                    source_id="BUG-001",
                    target_id="REQ-002",
                    relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
            acceptance_criteria=(
                "First criterion.",
                "Second criterion.",
                "Third criterion.",
            ),
            audit_references=(
                "AUDIT-001",
                "AUDIT-002",
            ),
        )

        relationship_records = (
            WorkItemRepository._to_relationship_records(work_item)
        )

        criterion_records = (
            WorkItemRepository._to_acceptance_criterion_records(work_item)
        )

        audit_records = (
            WorkItemRepository._to_audit_reference_records(work_item)
        )

        self.assertEqual(
            [item.relationship_type for item in relationship_records],
            ["Violated Requirement", "Violated Requirement"],
        )

        self.assertEqual(
            [item.position for item in relationship_records],
            [0, 1],
        )

        self.assertEqual(
            [item.criterion for item in criterion_records],
            list(work_item.acceptance_criteria),
        )

        self.assertEqual(
            [item.position for item in criterion_records],
            [0, 1, 2],
        )

        self.assertEqual(
            [item.audit_reference for item in audit_records],
            list(work_item.audit_references),
        )

        self.assertEqual(
            [item.position for item in audit_records],
            [0, 1],
        )

    def test_database_records_can_be_converted_back_to_work_item(self):

        created_at = datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 11, 12, 45, tzinfo=timezone.utc)

        original = WorkItem(
            id="BUG-001",
            title="Incorrect inventory calculation",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            build_number="1.02",
            description="Inventory totals are incorrect.",
            state=WorkItemState.BLOCKED,
            priority="High",
            assigned_agent="Developer",
            created_at=created_at,
            updated_at=updated_at,
            relationships=(
                WorkItemRelationship(
                    source_id="BUG-001",
                    target_id="REQ-001",
                    relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
                ),
                WorkItemRelationship(
                    source_id="BUG-001",
                    target_id="REQ-002",
                    relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
            acceptance_criteria=(
                "First criterion.",
                "Second criterion.",
            ),
            block_reason="Waiting for dependency.",
            blocked_return_state=WorkItemState.IN_WORK,
            audit_references=("AUDIT-001", "AUDIT-002"),
            authorized_by="ProductManager-01",
            authorized_at=created_at,
            authorization_reason="Approved for implementation.",
        )

        record = WorkItemRepository._to_record(original)

        relationship_records = (
            WorkItemRepository._to_relationship_records(original)
        )

        criterion_records = (
            WorkItemRepository._to_acceptance_criterion_records(original)
        )

        audit_records = (
            WorkItemRepository._to_audit_reference_records(original)
        )

        reconstructed = WorkItemRepository._from_records(
            record,
            relationship_records,
            criterion_records,
            audit_records,
        )

        self.assertEqual(reconstructed, original)
        self.assertIsInstance(reconstructed.state, WorkItemState)
        self.assertIsInstance(
            reconstructed.blocked_return_state,
            WorkItemState,
        )

    def test_code_review_state_is_reconstructed_correctly(self):

        original = WorkItem(
            id="CRV-001",
            title="Review authentication implementation",
            work_item_type=WorkItemType.CODE_REVIEW_TASK,
            created_by="Developer",
            state=CodeReviewState.REVIEW,
        )

        reconstructed = WorkItemRepository._from_records(
            WorkItemRepository._to_record(original),
            [],
            [],
            [],
        )

        self.assertEqual(reconstructed, original)
        self.assertIsInstance(reconstructed.state, CodeReviewState)

    def test_empty_child_collections_are_preserved(self):

        original = WorkItem(
            id="REQ-001",
            title="User login",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
        )

        reconstructed = WorkItemRepository._from_records(
            WorkItemRepository._to_record(original),
            [],
            [],
            [],
        )

        self.assertEqual(reconstructed.relationships, ())
        self.assertEqual(reconstructed.acceptance_criteria, ())
        self.assertEqual(reconstructed.audit_references, ())


    def test_relationship_source_must_match_work_item_id(self):

        work_item = WorkItem(
            id="BUG-001",
            title="Authentication failure",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            relationships=(
                WorkItemRelationship(
                    source_id="BUG-002",
                    target_id="REQ-001",
                    relationship_type=(
                        RelationshipType.VIOLATED_REQUIREMENT
                    ),
                ),
            ),
        )

        with self.assertRaises(ValueError):
            WorkItemRepository._validate_work_items({
                work_item.id: work_item,
            })

class TestWorkItemRepositoryIntegration(unittest.TestCase):

    def setUp(self):

        self.requirement = WorkItem(
            id="TEST-REQ-RETRIEVAL-001",
            title="User authentication",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
            build_number="1.00",
            description="Users must be able to authenticate.",
            acceptance_criteria=(
                "Users can log in.",
                "Invalid credentials are rejected.",
            ),
        )

        self.bug = WorkItem(
            id="TEST-BUG-RETRIEVAL-001",
            title="Authentication failure",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            build_number="1.00",
            description="Valid users cannot log in.",
            state=WorkItemState.IN_WORK,
            relationships=(
                WorkItemRelationship(
                    source_id="TEST-BUG-RETRIEVAL-001",
                    target_id="TEST-REQ-RETRIEVAL-001",
                    relationship_type=(
                        RelationshipType.VIOLATED_REQUIREMENT
                    ),
                ),
            ),
            audit_references=(
                "TEST-AUDIT-001",
                "TEST-AUDIT-002",
            ),
        )

        self.test_ids = [
            self.requirement.id,
            self.bug.id,
        ]

        session = DatabaseManager.get_session()

        try:
            session.execute(
                delete(WorkItemRecord).where(
                    WorkItemRecord.id.in_(self.test_ids)
                )
            )

            session.add_all([
                WorkItemRepository._to_record(self.requirement),
                WorkItemRepository._to_record(self.bug),
            ])

            session.flush()

            session.add_all(
                WorkItemRepository._to_relationship_records(self.bug)
            )

            session.add_all(
                WorkItemRepository._to_acceptance_criterion_records(
                    self.requirement
                )
            )

            session.add_all(
                WorkItemRepository._to_audit_reference_records(self.bug)
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def tearDown(self):

        session = DatabaseManager.get_session()

        try:
            session.execute(
                delete(WorkItemRecord).where(
                    WorkItemRecord.id.in_(self.test_ids)
                )
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def test_get_by_id_retrieves_complete_work_item(self):

        result = WorkItemRepository.get_by_id(self.bug.id)

        self.assertEqual(result, self.bug)

    def test_get_all_retrieves_complete_work_item_collection(self):

        result = WorkItemRepository.get_all()

        self.assertIn(self.requirement.id, result)
        self.assertIn(self.bug.id, result)

        self.assertEqual(result[self.requirement.id], self.requirement)
        self.assertEqual(result[self.bug.id], self.bug)

    def test_get_by_id_returns_none_for_missing_work_item(self):

        result = WorkItemRepository.get_by_id(
            "TEST-NONEXISTENT-001"
        )

        self.assertIsNone(result)

    def test_save_inserts_new_work_item(self):

        work_item = WorkItem(
            id="TEST-TASK-SAVE-001",
            title="Create authentication service",
            work_item_type=WorkItemType.DEVELOPMENT_TASK,
            created_by="ProductManager",
        )

        self.test_ids.append(work_item.id)

        WorkItemRepository.save(work_item)

        result = WorkItemRepository.get_by_id(work_item.id)

        self.assertEqual(result, work_item)

    def test_save_updates_work_item_and_child_records(self):

        updated_bug = replace(
            self.bug,
            title="Updated authentication failure",
            relationships=(),
            audit_references=("TEST-AUDIT-003",),
        )

        WorkItemRepository.save(updated_bug)

        result = WorkItemRepository.get_by_id(self.bug.id)

        self.assertEqual(result, updated_bug)
        self.assertEqual(result.relationships, ())
        self.assertEqual(
            result.audit_references,
            ("TEST-AUDIT-003",),
        )

    def test_save_all_updates_multiple_work_items(self):

        updated_requirement = replace(
            self.requirement,
            title="Updated user authentication",
            acceptance_criteria=(
                "Users can log in.",
                "Invalid credentials are rejected.",
                "Users can log out.",
            ),
        )

        updated_bug = replace(
            self.bug,
            title="Updated authentication bug",
        )

        WorkItemRepository.save_all({
            updated_requirement.id: updated_requirement,
            updated_bug.id: updated_bug,
        })

        self.assertEqual(
            WorkItemRepository.get_by_id(updated_requirement.id),
            updated_requirement,
        )

        self.assertEqual(
            WorkItemRepository.get_by_id(updated_bug.id),
            updated_bug,
        )

    def test_save_all_preserves_unsupplied_work_items(self):

        updated_bug = replace(
            self.bug,
            title="Updated bug only",
        )

        WorkItemRepository.save_all({
            updated_bug.id: updated_bug,
        })

        self.assertEqual(
            WorkItemRepository.get_by_id(updated_bug.id),
            updated_bug,
        )

        self.assertEqual(
            WorkItemRepository.get_by_id(self.requirement.id),
            self.requirement,
        )

    def test_save_all_rolls_back_failed_transaction(self):

        invalid_work_item = WorkItem(
            id="TEST-BUG-ROLLBACK-001",
            title="Bug with missing requirement",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            relationships=(
                WorkItemRelationship(
                    source_id="TEST-BUG-ROLLBACK-001",
                    target_id="TEST-MISSING-REQUIREMENT-001",
                    relationship_type=(
                        RelationshipType.VIOLATED_REQUIREMENT
                    ),
                ),
            ),
        )

        self.test_ids.append(invalid_work_item.id)

        with self.assertRaises(IntegrityError):
            WorkItemRepository.save_all({
                invalid_work_item.id: invalid_work_item,
            })

        result = WorkItemRepository.get_by_id(
            invalid_work_item.id
        )

        self.assertIsNone(result)



if __name__ == "__main__":
    unittest.main()
