
import unittest

from dataclasses import replace

from phantom_logic.work_items.managers.WorkItemRelationshipManager import (
    WorkItemRelationshipManager,
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
from phantom_logic.work_items.rules.PermissionRules import AgentRole


class TestWorkItemRelationshipManager(unittest.TestCase):

    def create_item(
        self,
        item_id,
        item_type,
        *,
        relationships=(),
        state=WorkItemState.PROPOSED,
    ):
        return WorkItem(
            id=item_id,
            title=f"Title {item_id}",
            work_item_type=item_type,
            created_by="ProductManager",
            state=state,
            relationships=tuple(relationships),
        )

    def create_valid_hierarchy(self):
        feature = self.create_item("FEAT-1", WorkItemType.FEATURE)
        use_case = self.create_item("UC-1", WorkItemType.USE_CASE)
        requirement = self.create_item("REQ-1", WorkItemType.REQUIREMENT)
        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )
        test_case = self.create_item("TEST-1", WorkItemType.TEST_CASE)
        code_review = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.PROPOSED,
        )

        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEAT-1", "UC-1", RelationshipType.PARENT_CHILD
                ),
                WorkItemRelationship(
                    "FEAT-1", "REVIEW-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD
                ),
                WorkItemRelationship(
                    "UC-1", "DEV-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            relationships=(
                WorkItemRelationship(
                    "REQ-1", "TEST-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        return {
            "FEAT-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "DEV-1": development_task,
            "TEST-1": test_case,
            "REVIEW-1": code_review,
        }

    def create_partial_hierarchy(self):
        """Valid existing links, but required children are not yet attached."""

        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEAT-1", "UC-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            relationships=(
                WorkItemRelationship(
                    "REQ-1", "TEST-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        return {
            "FEAT-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "DEV-1": self.create_item(
                "DEV-1",
                WorkItemType.DEVELOPMENT_TASK,
            ),
            "TEST-1": self.create_item(
                "TEST-1",
                WorkItemType.TEST_CASE,
            ),
            "REVIEW-1": self.create_item(
                "REVIEW-1",
                WorkItemType.CODE_REVIEW_TASK,
                state=CodeReviewState.PROPOSED,
            ),
        }

    def assert_success(self, result, errors):
        self.assertIsNotNone(result)
        self.assertEqual(errors, [])

    def assert_failure(self, result, errors):
        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_add_relationship_succeeds(self):
        work_items = self.create_valid_hierarchy()

        relationship = WorkItemRelationship(
            "FEAT-1",
            "SUP-1",
            RelationshipType.PARENT_CHILD,
        )

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)
        self.assertIn(relationship, result["FEAT-1"].relationships)

    def test_add_relationship_does_not_mutate_original(self):
        work_items = self.create_valid_hierarchy()
        original_feature = work_items["FEAT-1"]

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        relationship = WorkItemRelationship(
            "FEAT-1",
            "SUP-1",
            RelationshipType.PARENT_CHILD,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)
        self.assertIs(work_items["FEAT-1"], original_feature)
        self.assertNotIn(relationship, original_feature.relationships)
        self.assertIsNot(result["FEAT-1"], original_feature)

    def test_add_relationship_preserves_unmodified_items(self):
        work_items = self.create_valid_hierarchy()

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "SUP-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)
        self.assertIs(result["UC-1"], work_items["UC-1"])
        self.assertIs(result["REQ-1"], work_items["REQ-1"])

    def test_add_relationships_is_atomic(self):
        work_items = self.create_partial_hierarchy()

        development_relationship = WorkItemRelationship(
            "UC-1",
            "DEV-1",
            RelationshipType.PARENT_CHILD,
        )

        review_relationship = WorkItemRelationship(
            "FEAT-1",
            "REVIEW-1",
            RelationshipType.PARENT_CHILD,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationships(
                work_items,
                (
                    development_relationship,
                    review_relationship,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)
        self.assertIn(
            development_relationship,
            result["UC-1"].relationships,
        )
        self.assertIn(
            review_relationship,
            result["FEAT-1"].relationships,
        )

        self.assertNotIn(
            development_relationship,
            work_items["UC-1"].relationships,
        )

    def test_add_relationship_rejects_duplicate(self):
        work_items = self.create_valid_hierarchy()

        relationship = work_items["FEAT-1"].relationships[0]

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_duplicate_in_batch(self):
        work_items = self.create_valid_hierarchy()

        relationship = WorkItemRelationship(
            "FEAT-1",
            "SUP-1",
            RelationshipType.PARENT_CHILD,
        )

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationships(
                work_items,
                (relationship, relationship),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_missing_source(self):
        work_items = self.create_valid_hierarchy()

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "MISSING",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_missing_target(self):
        work_items = self.create_valid_hierarchy()

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "MISSING",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_invalid_relationship_type(self):
        work_items = self.create_valid_hierarchy()

        relationship = WorkItemRelationship(
            "FEAT-1",
            "UC-1",
            "Invalid Relationship",
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_invalid_type_combination(self):
        work_items = self.create_valid_hierarchy()

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_unauthorized_role(self):
        work_items = self.create_valid_hierarchy()

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "SUP-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.DEVELOPER,
            )
        )

        self.assert_failure(result, errors)

    def test_work_item_manager_can_manage_relationships(self):
        work_items = self.create_valid_hierarchy()

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "SUP-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.WORK_ITEM_MANAGER,
            )
        )

        self.assert_success(result, errors)

    def test_remove_relationship_succeeds_for_optional_child(self):
        work_items = self.create_valid_hierarchy()

        requirement_relationship = WorkItemRelationship(
            "BUG-1",
            "REQ-1",
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        failed_test_relationship = WorkItemRelationship(
            "BUG-1",
            "TEST-1",
            RelationshipType.FAILED_TEST_CASE,
        )

        work_items["BUG-1"] = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                requirement_relationship,
                failed_test_relationship,
            ),
        )

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                failed_test_relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)
        self.assertNotIn(
            failed_test_relationship,
            result["BUG-1"].relationships,
        )
        self.assertIn(
            requirement_relationship,
            result["BUG-1"].relationships,
        )

    def test_remove_bug_optional_link_preserves_existing_work_states(self):
        work_items = self.create_valid_hierarchy()

        requirement_relationship = WorkItemRelationship(
            "BUG-1",
            "REQ-1",
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        failed_test_relationship = WorkItemRelationship(
            "BUG-1",
            "TEST-1",
            RelationshipType.FAILED_TEST_CASE,
        )

        work_items["BUG-1"] = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                requirement_relationship,
                failed_test_relationship,
            ),
        )

        # Simulate an already-started Bug and propagated hierarchy.
        for item_id in ("BUG-1", "REQ-1", "UC-1", "FEAT-1"):
            work_items[item_id] = replace(
                work_items[item_id],
                state=WorkItemState.IN_WORK,
            )

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                failed_test_relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)

        self.assertNotIn(
            failed_test_relationship,
            result["BUG-1"].relationships,
        )
        self.assertIn(
            requirement_relationship,
            result["BUG-1"].relationships,
        )

        # Removing the optional relationship must not change work states.
        for item_id in ("BUG-1", "REQ-1", "UC-1", "FEAT-1"):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
                f"{item_id} state changed unexpectedly.",
            )

    def test_remove_relationship_does_not_mutate_original(self):
        work_items = self.create_valid_hierarchy()

        requirement_relationship = WorkItemRelationship(
            "BUG-1",
            "REQ-1",
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        failed_test_relationship = WorkItemRelationship(
            "BUG-1",
            "TEST-1",
            RelationshipType.FAILED_TEST_CASE,
        )

        work_items["BUG-1"] = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                requirement_relationship,
                failed_test_relationship,
            ),
        )

        original_bug = work_items["BUG-1"]

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                failed_test_relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)

        self.assertIs(work_items["BUG-1"], original_bug)

        self.assertIn(
            failed_test_relationship,
            original_bug.relationships,
        )

        self.assertNotIn(
            failed_test_relationship,
            result["BUG-1"].relationships,
        )

        self.assertIsNot(result["BUG-1"], original_bug)

    def test_remove_required_development_task_relationship_fails(self):
        work_items = self.create_valid_hierarchy()

        relationship = WorkItemRelationship(
            "UC-1",
            "DEV-1",
            RelationshipType.PARENT_CHILD,
        )

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_remove_required_code_review_relationship_fails(self):
        work_items = self.create_valid_hierarchy()

        relationship = WorkItemRelationship(
            "FEAT-1",
            "REVIEW-1",
            RelationshipType.PARENT_CHILD,
        )

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_remove_last_bug_requirement_link_fails(self):
        work_items = self.create_valid_hierarchy()

        bug_relationship = WorkItemRelationship(
            "BUG-1",
            "REQ-1",
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        work_items["BUG-1"] = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(bug_relationship,),
        )

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                bug_relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_remove_last_change_request_requirement_link_fails(self):
        work_items = self.create_valid_hierarchy()

        relationship = WorkItemRelationship(
            "CR-1",
            "REQ-1",
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        work_items["CR-1"] = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(relationship,),
        )

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_bug_requirement_link_succeeds(self):
        work_items = self.create_valid_hierarchy()

        work_items["BUG-1"] = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        relationship = WorkItemRelationship(
            "BUG-1",
            "REQ-1",
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)

    def test_add_change_request_requirement_link_succeeds(self):
        work_items = self.create_valid_hierarchy()

        work_items["CR-1"] = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        relationship = WorkItemRelationship(
            "CR-1",
            "REQ-1",
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                relationship,
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_success(result, errors)

    def test_bug_must_have_requirement_link_after_operation(self):
        work_items = self.create_valid_hierarchy()

        work_items["BUG-1"] = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "SUP-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_change_request_must_have_requirement_link_after_operation(self):
        work_items = self.create_valid_hierarchy()

        work_items["CR-1"] = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "SUP-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_validate_relationship_change_does_not_apply_change(self):
        work_items = self.create_valid_hierarchy()

        work_items["SUP-1"] = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        relationship = WorkItemRelationship(
            "FEAT-1",
            "SUP-1",
            RelationshipType.PARENT_CHILD,
        )

        errors = (
            WorkItemRelationshipManager.validate_relationship_change(
                work_items,
                (relationship,),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assertEqual(errors, [])
        self.assertNotIn(relationship, work_items["FEAT-1"].relationships)

    def test_validate_relationship_change_reports_invalid_change(self):
        work_items = self.create_valid_hierarchy()

        errors = (
            WorkItemRelationshipManager.validate_relationship_change(
                work_items,
                (
                    WorkItemRelationship(
                        "FEAT-1",
                        "MISSING",
                        RelationshipType.PARENT_CHILD,
                    ),
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assertTrue(errors)

    def test_empty_relationship_batch_is_rejected(self):
        work_items = self.create_valid_hierarchy()

        result, errors = (
            WorkItemRelationshipManager.add_relationships(
                work_items,
                (),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_invalid_actor_role_is_rejected(self):
        work_items = self.create_valid_hierarchy()

        result, errors = (
            WorkItemRelationshipManager.add_relationships(
                work_items,
                (
                    WorkItemRelationship(
                        "FEAT-1",
                        "UC-1",
                        RelationshipType.PARENT_CHILD,
                    ),
                ),
                "Product Manager",
            )
        )

        self.assert_failure(result, errors)

    def test_non_mapping_collection_is_rejected(self):
        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                [],
                WorkItemRelationship(
                    "FEAT-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_remove_nonexistent_relationship_fails(self):
        work_items = self.create_valid_hierarchy()

        result, errors = (
            WorkItemRelationshipManager.remove_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)

    def test_add_relationship_rejects_multiple_parents(self):
        work_items = self.create_valid_hierarchy()

        work_items["FEAT-2"] = self.create_item(
            "FEAT-2",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEAT-2",
                    "UC-2",
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "FEAT-2",
                    "REVIEW-2",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        work_items["UC-2"] = self.create_item(
            "UC-2",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-2",
                    "DEV-2",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        work_items["DEV-2"] = self.create_item(
            "DEV-2",
            WorkItemType.DEVELOPMENT_TASK,
        )

        work_items["REVIEW-2"] = self.create_item(
            "REVIEW-2",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.PROPOSED,
        )

        result, errors = (
            WorkItemRelationshipManager.add_relationship(
                work_items,
                WorkItemRelationship(
                    "FEAT-2",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
                AgentRole.PRODUCT_MANAGER,
            )
        )

        self.assert_failure(result, errors)


if __name__ == "__main__":
    unittest.main()
