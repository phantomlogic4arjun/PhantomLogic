

import unittest

from phantom_logic.work_items.managers.WorkItemValidator import WorkItemValidator
from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.RelationshipRules import RelationshipRules


class TestWorkItemValidator(unittest.TestCase):

    def setUp(self):
        self.work_item = WorkItem(
            id="FEAT-001",
            title="Inventory Management",
            work_item_type=WorkItemType.FEATURE,
            created_by="ProductManager",
        )

        self.target_work_item = WorkItem(
            id="UC-001",
            title="Manage Inventory",
            work_item_type=WorkItemType.USE_CASE,
            created_by="ProductManager",
        )

    def create_relationship(
        self,
        source_id="FEAT-001",
        target_id="UC-001",
        relationship_type=RelationshipType.PARENT_CHILD,
    ):
        return WorkItemRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )

    # Identity validation

    def test_valid_work_item_identity(self):
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertEqual(errors, [])

    def test_empty_work_item_id_is_rejected(self):
        self.work_item.id = ""
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item ID cannot be empty.", errors)

    def test_whitespace_work_item_id_is_rejected(self):
        self.work_item.id = "   "
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item ID cannot be empty.", errors)

    def test_non_string_work_item_id_is_rejected(self):
        self.work_item.id = 123
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item ID cannot be empty.", errors)

    def test_empty_work_item_title_is_rejected(self):
        self.work_item.title = ""
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item title cannot be empty.", errors)

    def test_whitespace_work_item_title_is_rejected(self):
        self.work_item.title = "   "
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item title cannot be empty.", errors)

    def test_non_string_work_item_title_is_rejected(self):
        self.work_item.title = 123
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item title cannot be empty.", errors)

    def test_invalid_work_item_type_is_rejected(self):
        self.work_item.work_item_type = "Feature"
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item type is invalid.", errors)

    def test_empty_creator_is_rejected(self):
        self.work_item.created_by = ""
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item creator cannot be empty.", errors)

    def test_whitespace_creator_is_rejected(self):
        self.work_item.created_by = "   "
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item creator cannot be empty.", errors)

    def test_non_string_creator_is_rejected(self):
        self.work_item.created_by = 123
        errors = WorkItemValidator.validate_identity(self.work_item)
        self.assertIn("Work item creator cannot be empty.", errors)

    def test_non_work_item_instance_is_rejected(self):
        errors = WorkItemValidator.validate_identity("Not a work item")
        self.assertEqual(
            errors,
            ["Work item must be a WorkItem instance."],
        )

    # Relationship reference validation

    def test_work_item_without_relationships_is_valid(self):
        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            {"FEAT-001": self.work_item},
        )
        self.assertEqual(errors, [])

    def test_valid_relationship_references(self):
        self.work_item.relationships = (
            self.create_relationship(),
        )

        work_items = {
            "FEAT-001": self.work_item,
            "UC-001": self.target_work_item,
        }

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            work_items,
        )

        self.assertEqual(errors, [])

    def test_relationship_with_incorrect_source_is_rejected(self):
        self.work_item.relationships = (
            self.create_relationship(source_id="FEAT-999"),
        )

        work_items = {
            "FEAT-001": self.work_item,
            "UC-001": self.target_work_item,
        }

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            work_items,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("does not match owning work item", errors[0])

    def test_relationship_with_missing_target_is_rejected(self):
        self.work_item.relationships = (
            self.create_relationship(target_id="UC-999"),
        )

        work_items = {
            "FEAT-001": self.work_item,
        }

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            work_items,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("does not exist", errors[0])

    def test_self_referencing_relationship_is_rejected(self):
        self.work_item.relationships = (
            self.create_relationship(
                target_id="FEAT-001",
            ),
        )

        work_items = {
            "FEAT-001": self.work_item,
        }

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            work_items,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("cannot reference itself", errors[0])

    def test_duplicate_relationship_is_rejected(self):
        relationship = self.create_relationship()

        self.work_item.relationships = (
            relationship,
            relationship,
        )

        work_items = {
            "FEAT-001": self.work_item,
            "UC-001": self.target_work_item,
        }

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            work_items,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Duplicate relationship", errors[0])

    def test_multiple_relationship_errors_are_reported(self):
        self.work_item.relationships = (
            self.create_relationship(
                source_id="FEAT-999",
                target_id="UC-999",
            ),
        )

        work_items = {
            "FEAT-001": self.work_item,
        }

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            work_items,
        )

        self.assertEqual(len(errors), 2)
        self.assertTrue(
            any("does not match owning work item" in error for error in errors)
        )
        self.assertTrue(
            any("does not exist" in error for error in errors)
        )

    def test_invalid_relationship_object_is_rejected(self):
        self.work_item.relationships = ("invalid",)

        errors = WorkItemValidator.validate_relationship_references(
            self.work_item,
            {"FEAT-001": self.work_item},
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("invalid relationship object", errors[0])

    def test_non_work_item_instance_is_rejected_for_references(self):
        errors = WorkItemValidator.validate_relationship_references(
            "Not a work item",
            {},
        )

        self.assertEqual(
            errors,
            ["Work item must be a WorkItem instance."],
        )

    # Relationship type validation

    def test_all_allowed_relationship_types_are_valid(self):
        self.assertEqual(len(RelationshipRules.ALLOWED_RELATIONSHIPS), 10)

        for index, (
            source_type,
            relationship_type,
            target_type,
        ) in enumerate(RelationshipRules.ALLOWED_RELATIONSHIPS):

            source = WorkItem(
                id=f"SOURCE-{index}",
                title="Source",
                work_item_type=source_type,
                created_by="ProductManager",
                relationships=(
                    WorkItemRelationship(
                        source_id=f"SOURCE-{index}",
                        target_id=f"TARGET-{index}",
                        relationship_type=relationship_type,
                    ),
                ),
            )

            target = WorkItem(
                id=f"TARGET-{index}",
                title="Target",
                work_item_type=target_type,
                created_by="ProductManager",
            )

            errors = WorkItemValidator.validate_relationship_types(
                source,
                {
                    source.id: source,
                    target.id: target,
                },
            )

            with self.subTest(
                source_type=source_type,
                relationship_type=relationship_type,
                target_type=target_type,
            ):
                self.assertEqual(errors, [])

    def test_invalid_relationship_type_is_rejected(self):
        self.work_item.relationships = (
            self.create_relationship(
                relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
            ),
        )

        work_items = {
            "FEAT-001": self.work_item,
            "UC-001": self.target_work_item,
        }

        errors = WorkItemValidator.validate_relationship_types(
            self.work_item,
            work_items,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("is not permitted", errors[0])

    def test_invalid_target_type_is_rejected(self):
        bug = WorkItem(
            id="BUG-001",
            title="Inventory calculation defect",
            work_item_type=WorkItemType.BUG,
            created_by="QA",
            relationships=(
                WorkItemRelationship(
                    source_id="BUG-001",
                    target_id="FEAT-001",
                    relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "BUG-001": bug,
            "FEAT-001": self.work_item,
        }

        errors = WorkItemValidator.validate_relationship_types(
            bug,
            work_items,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("is not permitted", errors[0])

    def test_missing_relationship_target_is_skipped_by_type_validation(self):
        self.work_item.relationships = (
            self.create_relationship(target_id="UC-999"),
        )

        errors = WorkItemValidator.validate_relationship_types(
            self.work_item,
            {"FEAT-001": self.work_item},
        )

        self.assertEqual(errors, [])

    def test_invalid_source_work_item_type_is_rejected(self):
        self.work_item.work_item_type = "Feature"

        errors = WorkItemValidator.validate_relationship_types(
            self.work_item,
            {"FEAT-001": self.work_item},
        )

        self.assertEqual(
            errors,
            ["Work item type is invalid; relationship types cannot be validated."],
        )

    def test_invalid_target_work_item_type_is_rejected(self):
        self.work_item.relationships = (
            self.create_relationship(),
        )

        self.target_work_item.work_item_type = "Use Case"

        errors = WorkItemValidator.validate_relationship_types(
            self.work_item,
            {
                "FEAT-001": self.work_item,
                "UC-001": self.target_work_item,
            },
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("has an invalid work item type", errors[0])

    def test_invalid_relationship_object_is_rejected_by_type_validation(self):
        self.work_item.relationships = ("invalid",)

        errors = WorkItemValidator.validate_relationship_types(
            self.work_item,
            {"FEAT-001": self.work_item},
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("invalid relationship object", errors[0])

    def test_non_work_item_instance_is_rejected_for_type_validation(self):
        errors = WorkItemValidator.validate_relationship_types(
            "Not a work item",
            {},
        )

        self.assertEqual(
            errors,
            ["Work item must be a WorkItem instance."],
        )


if __name__ == "__main__":
    unittest.main()
