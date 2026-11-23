
import unittest
from dataclasses import FrozenInstanceError

from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)


class TestWorkItemRelationship(unittest.TestCase):

    def test_relationship_can_be_created(self):
        relationship = WorkItemRelationship(
            source_id="UC-001",
            target_id="REQ-001",
            relationship_type=RelationshipType.PARENT_CHILD,
        )

        self.assertEqual(relationship.source_id, "UC-001")
        self.assertEqual(relationship.target_id, "REQ-001")
        self.assertEqual(
            relationship.relationship_type,
            RelationshipType.PARENT_CHILD,
        )

    def test_relationship_is_immutable(self):
        relationship = WorkItemRelationship(
            source_id="CR-001",
            target_id="REQ-001",
            relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
        )

        with self.assertRaises(FrozenInstanceError):
            relationship.source_id = "CR-002"

    def test_change_request_affected_requirement_relationship(self):
        relationship = WorkItemRelationship(
            source_id="CR-001",
            target_id="REQ-001",
            relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assertEqual(relationship.source_id, "CR-001")
        self.assertEqual(relationship.target_id, "REQ-001")

    def test_bug_violated_requirement_relationship(self):
        relationship = WorkItemRelationship(
            source_id="BUG-001",
            target_id="REQ-001",
            relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assertEqual(relationship.source_id, "BUG-001")
        self.assertEqual(relationship.target_id, "REQ-001")

    def test_bug_failed_test_case_relationship(self):
        relationship = WorkItemRelationship(
            source_id="BUG-001",
            target_id="TEST-001",
            relationship_type=RelationshipType.FAILED_TEST_CASE,
        )

        self.assertEqual(relationship.source_id, "BUG-001")
        self.assertEqual(relationship.target_id, "TEST-001")

    def test_all_relationship_types_are_defined(self):
        expected_types = {
            "Parent Child",
            "Affected Requirement",
            "Violated Requirement",
            "Failed Test Case",
        }

        actual_types = {item.value for item in RelationshipType}

        self.assertEqual(actual_types, expected_types)

    def test_relationship_types_are_string_enums(self):
        self.assertEqual(
            RelationshipType.AFFECTED_REQUIREMENT,
            "Affected Requirement",
        )


if __name__ == "__main__":
    unittest.main()
