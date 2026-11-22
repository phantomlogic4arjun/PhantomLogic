
import unittest

from PhantomLogic.WorkItems.Manager.WorkItemManager import WorkItemManager
from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from PhantomLogic.WorkItems.Models.WorkItemState import WorkItemState
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.PermissionRules import AgentRole

from PhantomLogic.WorkItems.Models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)


class TestWorkItemManager(unittest.TestCase):

    def setUp(self):
        self.manager = WorkItemManager()

    @staticmethod
    def create_item(
        item_id="ITEM-1",
        item_type=WorkItemType.FEATURE,
        state=WorkItemState.PROPOSED,
        relationships=(),
    ):
        return WorkItem(
            id=item_id,
            title=f"Test {item_id}",
            work_item_type=item_type,
            created_by="Product Manager",
            state=state,
            relationships=relationships,
            acceptance_criteria=("Acceptance criterion",),
        )

    # --------------------------------------------------------------
    # Registration
    # --------------------------------------------------------------

    def test_register_work_item_succeeds(self):
        item = self.create_item()

        result, errors = self.manager.register_work_item(
            {},
            item,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertIn("ITEM-1", result)
        self.assertIs(result["ITEM-1"], item)

    def test_register_work_item_rejects_unauthorized_role(self):
        item = self.create_item()

        result, errors = self.manager.register_work_item(
            {},
            item,
            AgentRole.DEVELOPER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_register_bug_requires_qa(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )
        requirements, errors = self.manager.register_work_item(
            {},
            requirement,
            AgentRole.PRODUCT_MANAGER,
        )
        self.assertEqual(errors, [])

        relationship = WorkItemRelationship(
            "BUG-1",
            "REQ-1",
            RelationshipType.VIOLATED_REQUIREMENT,
        )
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(relationship,),
        )

        result, errors = self.manager.register_work_item(
            requirements,
            bug,
            AgentRole.QA,
        )

        self.assertEqual(errors, [])
        self.assertIn("BUG-1", result)

    def test_register_bug_rejects_missing_requirement_link(self):
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        result, errors = self.manager.register_work_item(
            {},
            bug,
            AgentRole.QA,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_register_test_case_accepts_qa(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )
        requirement_items, errors = self.manager.register_work_item(
            {},
            requirement,
            AgentRole.PRODUCT_MANAGER,
        )
        self.assertEqual(errors, [])

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        result, errors = self.manager.register_work_item(
            requirement_items,
            test_case,
            AgentRole.QA,
        )

        self.assertEqual(errors, [])
        self.assertIn("TEST-1", result)

    def test_register_work_item_rejects_duplicate_id(self):
        existing = self.create_item()
        new_item = self.create_item()

        result, errors = self.manager.register_work_item(
            {"ITEM-1": existing},
            new_item,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_register_work_items_is_atomic(self):
        first = self.create_item("ITEM-1")
        second = self.create_item("ITEM-1")
        original = {}

        result, errors = self.manager.register_work_items(
            original,
            (first, second),
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(original, {})

    def test_register_work_items_supports_batch_references(self):
        relationship = WorkItemRelationship(
            "FEATURE-1",
            "UC-1",
            RelationshipType.PARENT_CHILD,
        )

        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(relationship,),
        )
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        result, errors = self.manager.register_work_items(
            {},
            (use_case, feature),
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertEqual(set(result), {"FEATURE-1", "UC-1"})

    def test_register_work_items_returns_new_mapping(self):
        existing = self.create_item("EXISTING")
        original = {"EXISTING": existing}
        addition = self.create_item("NEW")

        result, errors = self.manager.register_work_item(
            original,
            addition,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNot(result, original)
        self.assertEqual(set(original), {"EXISTING"})
        self.assertEqual(set(result), {"EXISTING", "NEW"})
        self.assertIs(original["EXISTING"], existing)

    # --------------------------------------------------------------
    # Retrieval and validation
    # --------------------------------------------------------------

    def test_get_work_item_returns_existing_item(self):
        item = self.create_item()
        result = self.manager.get_work_item({"ITEM-1": item}, "ITEM-1")

        self.assertIs(result, item)

    def test_get_work_item_returns_none_for_missing_item(self):
        self.assertIsNone(self.manager.get_work_item({}, "MISSING"))

    def test_validate_collection_accepts_valid_items(self):
        item = self.create_item()

        errors = self.manager.validate_collection({"ITEM-1": item})

        self.assertEqual(errors, [])

    def test_validate_collection_rejects_mismatched_key(self):
        item = self.create_item()

        errors = self.manager.validate_collection({"WRONG-ID": item})

        self.assertTrue(errors)

    def test_validate_hierarchy_rejects_incomplete_hierarchy(self):
        feature = self.create_item()

        errors = self.manager.validate_hierarchy(
            {"ITEM-1": feature}
        )

        self.assertTrue(errors)

    # --------------------------------------------------------------
    # Relationship delegation
    # --------------------------------------------------------------

    def test_add_relationship_delegates_to_relationship_manager(self):
        feature = self.create_item("FEATURE-1")

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        code_review = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.PROPOSED,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        # Feature owns its child relationships.
        feature = replace_for_test(
            feature,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "REVIEW-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        # Use Case owns its Development Task relationship.
        use_case = replace_for_test(
            use_case,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "DEV-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        relationship = WorkItemRelationship(
            "FEATURE-1",
            "UC-1",
            RelationshipType.PARENT_CHILD,
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": code_review,
            "DEV-1": development_task,
        }

        result, errors = self.manager.add_relationship(
            work_items,
            relationship,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIn(
            relationship,
            result["FEATURE-1"].relationships,
        )

        # Original collection and objects remain unchanged.
        self.assertNotIn(
            relationship,
            work_items["FEATURE-1"].relationships,
        )
        self.assertEqual(
            len(work_items["FEATURE-1"].relationships),
            1,
        )

    def test_remove_relationship_delegates_to_relationship_manager(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )
        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        relationship = WorkItemRelationship(
            "TEST-1",
            "REQ-1",
            RelationshipType.PARENT_CHILD,
        )
        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
            relationships=(relationship,),
        )

        work_items = {
            "REQ-1": requirement,
            "TEST-1": test_case,
        }

        result, errors = self.manager.remove_relationship(
            work_items,
            relationship,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    # --------------------------------------------------------------
    # State transitions
    # --------------------------------------------------------------

    def test_product_manager_can_authorize_proposed_work(self):
        item = self.create_item()

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )

        self.assertEqual(errors, [])
        self.assertEqual(result["ITEM-1"].state, WorkItemState.IN_WORK)
        self.assertEqual(item.state, WorkItemState.PROPOSED)

    def test_developer_cannot_start_proposed_work(self):
        item = self.create_item()

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.IN_WORK,
            AgentRole.DEVELOPER,
            work_authorized=True,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(item.state, WorkItemState.PROPOSED)

    def test_blocking_preserves_previous_state(self):
        item = self.create_item(
            state=WorkItemState.IN_WORK,
        )

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.BLOCKED,
            AgentRole.DEVELOPER,
            reason="Waiting for a dependency",
        )

        self.assertEqual(errors, [])
        blocked = result["ITEM-1"]

        self.assertEqual(blocked.state, WorkItemState.BLOCKED)
        self.assertEqual(
            blocked.blocked_return_state,
            WorkItemState.IN_WORK,
        )
        self.assertEqual(
            blocked.block_reason,
            "Waiting for a dependency",
        )
        self.assertEqual(item.state, WorkItemState.IN_WORK)

    def test_unblocking_restores_previous_state(self):
        item = self.create_item(
            state=WorkItemState.BLOCKED,
        )
        item = replace_for_test(
            item,
            blocked_return_state=WorkItemState.IN_WORK,
            block_reason="Waiting for a dependency",
        )

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            reason="Dependency resolved",
        )

        self.assertEqual(errors, [])
        restored = result["ITEM-1"]

        self.assertEqual(restored.state, WorkItemState.IN_WORK)
        self.assertIsNone(restored.blocked_return_state)
        self.assertIsNone(restored.block_reason)
        self.assertEqual(item.state, WorkItemState.BLOCKED)

    def test_blocking_requires_a_reason(self):
        item = self.create_item(
            state=WorkItemState.IN_WORK,
        )

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.BLOCKED,
            AgentRole.DEVELOPER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_invalid_transition_does_not_mutate_original(self):
        item = self.create_item()

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.RESOLVED,
            AgentRole.QA,
            verification_passed=True,
            completion_criteria_met=True,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(item.state, WorkItemState.PROPOSED)

    def test_transition_rejects_missing_item(self):
        result, errors = self.manager.transition_state(
            {},
            "MISSING",
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_transition_rejects_invalid_actor(self):
        item = self.create_item()

        result, errors = self.manager.transition_state(
            {"ITEM-1": item},
            "ITEM-1",
            WorkItemState.IN_WORK,
            "Product Manager",
            work_authorized=True,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    # --------------------------------------------------------------
    # Readiness and submission
    # --------------------------------------------------------------

    def test_check_readiness_rejects_missing_item(self):
        errors = self.manager.check_readiness(
            {},
            "MISSING",
            AgentRole.DEVELOPER,
        )

        self.assertTrue(errors)

    def test_check_readiness_rejects_incomplete_implementation(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_WORK,
        )

        errors = self.manager.check_readiness(
            {"DEV-1": item},
            "DEV-1",
            AgentRole.DEVELOPER,
        )

        self.assertTrue(errors)

    def test_submit_for_test_rejects_failed_readiness(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_WORK,
        )

        result, errors = self.manager.submit_for_test(
            {"DEV-1": item},
            "DEV-1",
            AgentRole.DEVELOPER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(item.state, WorkItemState.IN_WORK)

    # --------------------------------------------------------------
    # Resolution
    # --------------------------------------------------------------

    def test_check_resolution_rejects_missing_item(self):
        errors = self.manager.check_resolution(
            {},
            "MISSING",
            AgentRole.QA,
        )

        self.assertTrue(errors)

    def test_resolution_requires_successful_verification(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        errors = self.manager.check_resolution(
            {"DEV-1": item},
            "DEV-1",
            AgentRole.QA,
        )

        self.assertTrue(errors)

    def test_resolve_work_item_does_not_mutate_on_failure(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        result, errors = self.manager.resolve_work_item(
            {"DEV-1": item},
            "DEV-1",
            AgentRole.QA,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(item.state, WorkItemState.IN_TEST)


def replace_for_test(item, **changes):
    from dataclasses import replace
    return replace(item, **changes)


if __name__ == "__main__":
    unittest.main()
