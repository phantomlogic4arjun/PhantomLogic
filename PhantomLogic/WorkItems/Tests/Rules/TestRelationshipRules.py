import unittest

from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.RelationshipRules import RelationshipRules


class TestRelationshipRules(unittest.TestCase):

    def test_all_allowed_relationships_are_valid(self):
        for relationship in RelationshipRules.ALLOWED_RELATIONSHIPS:
            source_type, relationship_type, target_type = relationship

            with self.subTest(
                source=source_type,
                relationship=relationship_type,
                target=target_type,
            ):
                self.assertTrue(
                    RelationshipRules.is_valid_relationship(
                        source_type,
                        relationship_type,
                        target_type,
                    )
                )

    def test_invalid_hierarchy_relationship_is_rejected(self):
        self.assertFalse(
            RelationshipRules.is_valid_relationship(
                WorkItemType.BUG,
                RelationshipType.PARENT_CHILD,
                WorkItemType.FEATURE,
            )
        )

    def test_invalid_parent_child_direction_is_rejected(self):
        self.assertFalse(
            RelationshipRules.is_valid_relationship(
                WorkItemType.REQUIREMENT,
                RelationshipType.PARENT_CHILD,
                WorkItemType.USE_CASE,
            )
        )

    def test_invalid_affected_requirement_relationship_is_rejected(self):
        self.assertFalse(
            RelationshipRules.is_valid_relationship(
                WorkItemType.BUG,
                RelationshipType.AFFECTED_REQUIREMENT,
                WorkItemType.REQUIREMENT,
            )
        )

    def test_invalid_violated_requirement_relationship_is_rejected(self):
        self.assertFalse(
            RelationshipRules.is_valid_relationship(
                WorkItemType.CHANGE_REQUEST,
                RelationshipType.VIOLATED_REQUIREMENT,
                WorkItemType.REQUIREMENT,
            )
        )

    def test_invalid_failed_test_case_relationship_is_rejected(self):
        self.assertFalse(
            RelationshipRules.is_valid_relationship(
                WorkItemType.CHANGE_REQUEST,
                RelationshipType.FAILED_TEST_CASE,
                WorkItemType.TEST_CASE,
            )
        )

    def test_unlisted_relationship_is_rejected(self):
        self.assertFalse(
            RelationshipRules.is_valid_relationship(
                WorkItemType.EPIC,
                RelationshipType.PARENT_CHILD,
                WorkItemType.USE_CASE,
            )
        )


if __name__ == "__main__":
    unittest.main()
