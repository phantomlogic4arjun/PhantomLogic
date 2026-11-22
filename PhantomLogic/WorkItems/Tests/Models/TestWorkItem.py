
import unittest

from datetime import timezone

from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from PhantomLogic.WorkItems.Models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType


class TestWorkItem(unittest.TestCase):

    def test_work_item_can_be_created(self):
        item = WorkItem(
            id="FEAT-001",
            title="User Authentication",
            work_item_type=WorkItemType.FEATURE,
            created_by="ProductManager",
        )

        self.assertEqual(item.id, "FEAT-001")
        self.assertEqual(item.title, "User Authentication")
        self.assertEqual(item.work_item_type, WorkItemType.FEATURE)
        self.assertEqual(item.created_by, "ProductManager")

    def test_work_item_can_store_build_number(self):
        item = WorkItem(
            id="REQ-001",
            title="User login",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
            build_number="1.00",
        )

        self.assertEqual(item.build_number, "1.00")

    def test_work_item_can_store_later_build_number(self):
        item = WorkItem(
            id="REQ-002",
            title="Password reset",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
            build_number="1.01",
        )

        self.assertEqual(item.build_number, "1.01")

    def test_build_number_defaults_to_none(self):
        item = WorkItem(
            id="REQ-003",
            title="User registration",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
        )

        self.assertIsNone(item.build_number)

    def test_default_values_are_set(self):
        item = WorkItem(
            id="REQ-001",
            title="User login",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
        )

        self.assertEqual(item.description, "")
        self.assertEqual(item.state, WorkItemState.PROPOSED)
        self.assertIsNone(item.priority)
        self.assertIsNone(item.assigned_agent)
        self.assertEqual(item.relationships, ())
        self.assertEqual(item.acceptance_criteria, ())
        self.assertEqual(item.audit_references, ())

        self.assertIsNone(item.authorized_by)
        self.assertIsNone(item.authorized_at)
        self.assertIsNone(item.authorization_reason)
        self.assertIsNone(item.build_number)

    def test_timestamps_are_timezone_aware(self):
        item = WorkItem(
            id="UC-001",
            title="Login workflow",
            work_item_type=WorkItemType.USE_CASE,
            created_by="ProductManager",
        )

        self.assertIsNotNone(item.created_at.tzinfo)
        self.assertIsNotNone(item.updated_at.tzinfo)

        self.assertEqual(
            item.created_at.utcoffset().total_seconds(),
            0,
        )
        self.assertEqual(
            item.updated_at.utcoffset().total_seconds(),
            0,
        )

        self.assertEqual(item.created_at.tzinfo, timezone.utc)
        self.assertEqual(item.updated_at.tzinfo, timezone.utc)

    def test_work_item_can_store_relationships(self):
        relationship = WorkItemRelationship(
            source_id="REQ-001",
            target_id="UC-001",
            relationship_type=RelationshipType.PARENT_CHILD,
        )

        item = WorkItem(
            id="REQ-001",
            title="User login",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
            relationships=(relationship,),
        )

        self.assertEqual(len(item.relationships), 1)
        self.assertEqual(item.relationships[0], relationship)

    def test_work_item_can_store_acceptance_criteria(self):
        criteria = (
            "User can enter a username.",
            "User can enter a password.",
            "Invalid credentials are rejected.",
        )

        item = WorkItem(
            id="REQ-001",
            title="User login",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
            acceptance_criteria=criteria,
        )

        self.assertEqual(item.acceptance_criteria, criteria)

    def test_code_review_state_is_supported(self):
        item = WorkItem(
            id="CRV-001",
            title="Feature code review",
            work_item_type=WorkItemType.CODE_REVIEW_TASK,
            created_by="ProductManager",
            state=CodeReviewState.REVIEW,
        )

        self.assertEqual(item.state, CodeReviewState.REVIEW)

    def test_default_collections_are_immutable_tuples(self):
        first = WorkItem(
            id="REQ-001",
            title="Requirement one",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
        )

        second = WorkItem(
            id="REQ-002",
            title="Requirement two",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="ProductManager",
        )

        for item in (first, second):
            self.assertIsInstance(item.relationships, tuple)
            self.assertIsInstance(item.acceptance_criteria, tuple)
            self.assertIsInstance(item.audit_references, tuple)

        with self.assertRaises(AttributeError):
            first.relationships.append("REL-001")

        with self.assertRaises(AttributeError):
            first.acceptance_criteria.append("Criterion")

        with self.assertRaises(AttributeError):
            first.audit_references.append("AUDIT-001")

    # ---------------------------------------------------------
    # Authorization evidence
    # ---------------------------------------------------------

    def test_work_item_can_store_authorization_evidence(self):
        authorized_at = datetime_for_test()

        item = WorkItem(
            id="BUG-001",
            title="Incorrect inventory calculation",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            authorized_by="ProductManager-01",
            authorized_at=authorized_at,
            authorization_reason="Approved for implementation.",
        )

        self.assertEqual(item.authorized_by, "ProductManager-01")
        self.assertEqual(item.authorized_at, authorized_at)
        self.assertEqual(
            item.authorization_reason,
            "Approved for implementation.",
        )

    def test_authorization_evidence_defaults_to_unset(self):
        item = WorkItem(
            id="CR-001",
            title="Inventory enhancement",
            work_item_type=WorkItemType.CHANGE_REQUEST,
            created_by="ProductManager",
        )

        self.assertIsNone(item.authorized_by)
        self.assertIsNone(item.authorized_at)
        self.assertIsNone(item.authorization_reason)

    def test_authorization_timestamp_is_timezone_aware(self):
        authorized_at = datetime_for_test()

        item = WorkItem(
            id="BUG-001",
            title="Test bug",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            authorized_by="ProductManager-01",
            authorized_at=authorized_at,
            authorization_reason="Approved.",
        )

        self.assertIsNotNone(item.authorized_at.tzinfo)
        self.assertEqual(
            item.authorized_at.utcoffset().total_seconds(),
            0,
        )


def datetime_for_test():
    from datetime import datetime

    return datetime(2026, 11, 21, 20, 0, tzinfo=timezone.utc)


if __name__ == "__main__":
    unittest.main()
