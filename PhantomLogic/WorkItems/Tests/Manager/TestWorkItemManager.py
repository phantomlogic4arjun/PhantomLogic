
import unittest

from PhantomLogic.WorkItems.Manager.WorkItemManager import WorkItemManager
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
from PhantomLogic.WorkItems.Rules.PermissionRules import AgentRole

from PhantomLogic.WorkItems.Models.WorkItemState import (
    CodeReviewState,
    ReviewResult,
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
    # Authorized Bug propagation
    # --------------------------------------------------------------

    def test_authorized_bug_reopens_affected_hierarchy(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                WorkItemRelationship(
                    "BUG-1",
                    "REQ-1",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        feature = replace_for_test(
            feature,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = replace_for_test(
            use_case,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "BUG-1": bug,
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved to fix the reported defect.",
        )

        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        for item_id in (
            "BUG-1",
            "REQ-1",
            "UC-1",
            "FEATURE-1",
        ):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )

        for item_id, original in work_items.items():
            self.assertEqual(
                original.state,
                WorkItemState.PROPOSED,
            )


    def test_authorized_work_with_events_returns_propagation_events(self):
        feature = self.create_item("FEATURE-1", WorkItemType.FEATURE)
        use_case = self.create_item("UC-1", WorkItemType.USE_CASE)
        requirement = self.create_item("REQ-1", WorkItemType.REQUIREMENT)
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                WorkItemRelationship(
                    "BUG-1",
                    "REQ-1",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        feature = replace_for_test(
            feature,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        use_case = replace_for_test(
            use_case,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "BUG-1": bug,
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved to fix the reported defect.",
        )
        self.assertEqual(errors, [])

        result, errors, events = self.manager.start_authorized_work_with_events(
            authorized_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), 4)

        event_by_id = {
            event["work_item_id"]: event
            for event in events
        }

        for item_id in ("BUG-1", "REQ-1", "UC-1", "FEATURE-1"):
            self.assertIn(item_id, event_by_id)
            self.assertEqual(
                event_by_id[item_id]["event_type"],
                "AUTHORIZED_WORK_PROPAGATED",
            )
            self.assertEqual(
                event_by_id[item_id]["previous_state"],
                WorkItemState.PROPOSED.value,
            )
            self.assertEqual(
                event_by_id[item_id]["new_state"],
                WorkItemState.IN_WORK.value,
            )
            self.assertEqual(
                event_by_id[item_id]["source_work_item_id"],
                "BUG-1",
            )

    def test_authorized_work_with_events_returns_no_events_on_failure(self):
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                WorkItemRelationship(
                    "BUG-1",
                    "MISSING-REQ",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        work_items = {"BUG-1": bug}

        result, errors, events = self.manager.start_authorized_work_with_events(
            work_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())


    def test_unauthorized_bug_cannot_propagate(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            relationships=(
                WorkItemRelationship(
                    "BUG-1",
                    "REQ-1",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "BUG-1": bug,
        }

        result, errors = self.manager.start_authorized_work(
            work_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

        for item in work_items.values():
            self.assertEqual(
                item.state,
                WorkItemState.PROPOSED,
            )

    # --------------------------------------------------------------
    # Authorized Change Request propagation
    # --------------------------------------------------------------

    def test_authorized_change_request_reopens_affected_hierarchy(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(
                WorkItemRelationship(
                    "CR-1",
                    "REQ-1",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "CR-1": change_request,
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved change to the requirement.",
        )

        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        for item_id in (
            "CR-1",
            "REQ-1",
            "UC-1",
            "FEATURE-1",
        ):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )

        for item in work_items.values():
            self.assertEqual(
                item.state,
                WorkItemState.PROPOSED,
            )

    def test_change_request_reopens_multiple_requirements(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "UC-1",
                    "REQ-2",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement_1 = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        requirement_2 = self.create_item(
            "REQ-2",
            WorkItemType.REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(
                WorkItemRelationship(
                    "CR-1",
                    "REQ-1",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
                WorkItemRelationship(
                    "CR-1",
                    "REQ-2",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement_1,
            "REQ-2": requirement_2,
            "CR-1": change_request,
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved change affecting two requirements.",
        )

        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        for item_id in (
            "CR-1",
            "REQ-1",
            "REQ-2",
            "UC-1",
            "FEATURE-1",
        ):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )

    def test_unauthorized_change_request_cannot_propagate(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(
                WorkItemRelationship(
                    "CR-1",
                    "REQ-1",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "CR-1": change_request,
        }

        result, errors = self.manager.start_authorized_work(
            work_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

        for item in work_items.values():
            self.assertEqual(
                item.state,
                WorkItemState.PROPOSED,
            )

    def test_authorized_change_request_preserves_blocked_requirement(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        requirement = replace_for_test(
            requirement,
            state=WorkItemState.BLOCKED,
            blocked_return_state=WorkItemState.IN_TEST,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(
                WorkItemRelationship(
                    "CR-1",
                    "REQ-1",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "CR-1": change_request,
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved change affecting blocked requirement.",
        )

        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        self.assertEqual(
            result["REQ-1"].state,
            WorkItemState.BLOCKED,
        )

        self.assertEqual(
            result["REQ-1"].blocked_return_state,
            WorkItemState.IN_WORK,
        )

        self.assertEqual(
            result["UC-1"].state,
            WorkItemState.IN_WORK,
        )

        self.assertEqual(
            result["FEATURE-1"].state,
            WorkItemState.IN_WORK,
        )

        # Unblocking must restore the state assigned by propagation.
        unblocked_items, errors = self.manager.transition_state(
            result,
            "REQ-1",
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            reason="Dependency resolved",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(unblocked_items)

        unblocked_requirement = unblocked_items["REQ-1"]

        self.assertEqual(
            unblocked_requirement.state,
            WorkItemState.IN_WORK,
        )
        self.assertIsNone(
            unblocked_requirement.blocked_return_state,
        )
        self.assertIsNone(
            unblocked_requirement.block_reason,
        )

        self.assertEqual(
            requirement.state,
            WorkItemState.BLOCKED,
        )
        self.assertEqual(
            requirement.blocked_return_state,
            WorkItemState.IN_TEST,
        )

    def test_authorized_change_request_reopens_resolved_hierarchy(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.RESOLVED,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.RESOLVED,
            relationships=(
                WorkItemRelationship(
                    "UC-1",
                    "REQ-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            state=WorkItemState.RESOLVED,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(
                WorkItemRelationship(
                    "CR-1",
                    "REQ-1",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement,
            "CR-1": change_request,
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved change to previously resolved work.",
        )

        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        for item_id in (
            "CR-1",
            "REQ-1",
            "UC-1",
            "FEATURE-1",
        ):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )

        # Original resolved items must remain unchanged.
        for item_id in (
            "FEATURE-1",
            "UC-1",
            "REQ-1",
        ):
            self.assertEqual(
                work_items[item_id].state,
                WorkItemState.RESOLVED,
            )

    # --------------------------------------------------------------
    # State transitions
    # --------------------------------------------------------------

    def test_complete_code_review_lifecycle(self):
        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.PROPOSED,
        )

        work_items = {
            "REVIEW-1": review_task,
        }        

        # 1. Reviewer starts the Code Review Task.
        work_items, errors = self.manager.transition_state(
            work_items,
            "REVIEW-1",
            CodeReviewState.IN_WORK,
            AgentRole.REVIEWER,
        )

        self.assertEqual(errors, [])

        # 2. Reviewer begins the review.
        work_items, errors = self.manager.transition_state(
            work_items,
            "REVIEW-1",
            CodeReviewState.REVIEW,
            AgentRole.REVIEWER,
        )

        self.assertEqual(errors, [])

        # 3. Reviewer requests changes.
        work_items, errors = self.manager.transition_state(
            work_items,
            "REVIEW-1",
            CodeReviewState.IN_WORK,
            AgentRole.REVIEWER,
            reason="Changes required before approval.",
        )

        self.assertEqual(errors, [])

        # 4. Developer addresses the requested changes.
        # Reviewer sends the updated work back into review.
        work_items, errors = self.manager.transition_state(
            work_items,
            "REVIEW-1",
            CodeReviewState.REVIEW,
            AgentRole.REVIEWER,
        )

        self.assertEqual(errors, [])

        # 5. Verify that the Developer cannot approve their own work.
        result, errors = self.manager.transition_state(
            work_items,
            "REVIEW-1",
            CodeReviewState.RESOLVED,
            AgentRole.REVIEWER,
            review_approved=True,
            actor_id="DEV-1",
            related_developer_id="DEV-1",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(
            work_items["REVIEW-1"].state,
            CodeReviewState.REVIEW,
        )

        # 6. Independent Reviewer approves and resolves the task.
        work_items, errors = self.manager.transition_state(
            work_items,
            "REVIEW-1",
            CodeReviewState.RESOLVED,
            AgentRole.REVIEWER,
            review_approved=True,
            actor_id="REVIEWER-1",
            related_developer_id="DEV-1",
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            work_items["REVIEW-1"].state,
            CodeReviewState.RESOLVED,
        )

    def test_product_manager_can_authorize_proposed_work(self):
        item = self.create_item()

        work_items = {"ITEM-1": item}

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "ITEM-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved for development.",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(authorized_items)

        result, errors = self.manager.transition_state(
            authorized_items,
            "ITEM-1",
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            result["ITEM-1"].state,
            WorkItemState.IN_WORK,
        )

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

    def test_development_task_completes_full_lifecycle(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        work_items = {"DEV-1": item}

        # 1. Product Manager authorizes the task.
        work_items, errors = self.manager.authorize_work(
            work_items,
            "DEV-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved development work.",
        )

        self.assertEqual(errors, [])

        # 2. Product Manager starts the authorized task.
        work_items, errors = self.manager.transition_state(
            work_items,
            "DEV-1",
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            work_items["DEV-1"].state,
            WorkItemState.IN_WORK,
        )

        # 3. Developer completes implementation and submits for testing.
        work_items, errors = self.manager.submit_for_test(
            work_items,
            "DEV-1",
            AgentRole.DEVELOPER,
            implementation_complete=True,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
            security_gate_passed=True,
            ci_gate_passed=True,
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            work_items["DEV-1"].state,
            WorkItemState.IN_TEST,
        )

        # 4. QA verifies and resolves the task.
        work_items, errors = self.manager.resolve_work_item(
            work_items,
            "DEV-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            reason="QA verification passed.",
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            work_items["DEV-1"].state,
            WorkItemState.RESOLVED,
        )

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
    

    def test_requirement_cannot_submit_without_test_case(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            state=WorkItemState.IN_WORK,
        )
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "UC-1", "DEV-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        dev_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        work_items = {
            "REQ-1": requirement,
            "UC-1": use_case,
            "DEV-1": dev_task,
        }

        result, errors = self.manager.submit_for_test(
            work_items,
            "REQ-1",
            AgentRole.WORK_ITEM_MANAGER,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(requirement.state, WorkItemState.IN_WORK)

    def test_requirement_completes_readiness_submission(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            state=WorkItemState.IN_WORK,
            relationships=(
                WorkItemRelationship(
                    "REQ-1", "TEST-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "UC-1", "DEV-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        dev_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )
        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        work_items = {
            "REQ-1": requirement,
            "UC-1": use_case,
            "DEV-1": dev_task,
            "TEST-1": test_case,
        }

        result, errors = self.manager.submit_for_test(
            work_items,
            "REQ-1",
            AgentRole.WORK_ITEM_MANAGER,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
        )

        self.assertEqual(errors, [])
        self.assertEqual(result["REQ-1"].state, WorkItemState.IN_TEST)

    def test_use_case_cannot_submit_with_unready_requirement(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.IN_WORK,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "UC-1", "DEV-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            state=WorkItemState.IN_WORK,
        )
        dev_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        work_items = {
            "UC-1": use_case,
            "REQ-1": requirement,
            "DEV-1": dev_task,
        }

        result, errors = self.manager.submit_for_test(
            work_items,
            "UC-1",
            AgentRole.WORK_ITEM_MANAGER,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(use_case.state, WorkItemState.IN_WORK)

    def test_use_case_completes_readiness_submission(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.IN_WORK,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "UC-1", "DEV-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            state=WorkItemState.IN_TEST,
        )
        dev_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        work_items = {
            "UC-1": use_case,
            "REQ-1": requirement,
            "DEV-1": dev_task,
        }

        result, errors = self.manager.submit_for_test(
            work_items,
            "UC-1",
            AgentRole.WORK_ITEM_MANAGER,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
        )

        self.assertEqual(errors, [])
        self.assertEqual(result["UC-1"].state, WorkItemState.IN_TEST)

    def test_feature_cannot_submit_without_approved_code_review(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.IN_WORK,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1", RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "FEATURE-1", "REVIEW-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.IN_TEST,
        )
        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.RESOLVED,
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": review_task,
        }

        result, errors = self.manager.submit_for_test(
            work_items,
            "FEATURE-1",
            AgentRole.WORK_ITEM_MANAGER,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
            security_gate_passed=True,
            ci_gate_passed=True,
            review_results={
                "REVIEW-1": ReviewResult.PENDING,
            },
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(feature.state, WorkItemState.IN_WORK)

    def test_feature_completes_readiness_submission(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.IN_WORK,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1", RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "FEATURE-1", "REVIEW-1", RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.IN_TEST,
        )
        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.RESOLVED,
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": review_task,
        }

        result, errors = self.manager.submit_for_test(
            work_items,
            "FEATURE-1",
            AgentRole.WORK_ITEM_MANAGER,
            changes_in_main=True,
            main_build_available=True,
            review_gates_satisfied=True,
            security_gate_passed=True,
            ci_gate_passed=True,
            review_results={
                "REVIEW-1": ReviewResult.APPROVED,
            },
        )

        self.assertEqual(errors, [])
        self.assertEqual(result["FEATURE-1"].state, WorkItemState.IN_TEST)


    # --------------------------------------------------------------
    # Resolution
    # --------------------------------------------------------------


    def test_feature_cannot_resolve_before_code_review_is_approved(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.IN_TEST,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "FEATURE-1", "REVIEW-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.RESOLVED,
        )

        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.RESOLVED,
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": review_task,
        }

        result, errors = self.manager.resolve_work_item(
            work_items,
            "FEATURE-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            security_gate_passed=True,
            ci_gate_passed=True,
            review_results={
                "REVIEW-1": ReviewResult.PENDING,
            },
            reason="Feature verification passed.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertTrue(
            any("Approved review result" in error for error in errors)
        )
        self.assertEqual(
            feature.state,
            WorkItemState.IN_TEST,
        )

    def test_feature_cannot_resolve_with_incomplete_use_case(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.IN_TEST,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "FEATURE-1", "REVIEW-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.IN_WORK,
        )

        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.RESOLVED,
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": review_task,
        }

        result, errors = self.manager.resolve_work_item(
            work_items,
            "FEATURE-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            security_gate_passed=True,
            ci_gate_passed=True,
            review_results={
                "REVIEW-1": ReviewResult.APPROVED,
            },
            reason="Feature verification passed.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertTrue(
            any("UC-1" in error and "Resolved" in error for error in errors)
        )
        self.assertEqual(
            feature.state,
            WorkItemState.IN_TEST,
        )

    def test_feature_completes_full_resolution_lifecycle(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.IN_TEST,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1",
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    "FEATURE-1", "REVIEW-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            state=WorkItemState.RESOLVED,
        )

        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.RESOLVED,
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": review_task,
        }

        result, errors = self.manager.resolve_work_item(
            work_items,
            "FEATURE-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            security_gate_passed=True,
            ci_gate_passed=True,
            review_results={
                "REVIEW-1": ReviewResult.APPROVED,
            },
            reason="Feature verification passed.",
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            result["FEATURE-1"].state,
            WorkItemState.RESOLVED,
        )
        self.assertEqual(
            feature.state,
            WorkItemState.IN_TEST,
        )
    
    def test_epic_cannot_resolve_without_features(self):
        epic = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
            state=WorkItemState.IN_TEST,
        )

        result, errors = self.manager.resolve_work_item(
            {"EPIC-1": epic},
            "EPIC-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            reason="Epic verification passed.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertTrue(
            any("at least one Feature" in error for error in errors)
        )
        self.assertEqual(epic.state, WorkItemState.IN_TEST)

    def test_epic_cannot_resolve_with_unresolved_feature(self):
        epic = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
            state=WorkItemState.IN_TEST,
            relationships=(
                WorkItemRelationship(
                    "EPIC-1",
                    "FEATURE-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.IN_WORK,
        )

        work_items = {
            "EPIC-1": epic,
            "FEATURE-1": feature,
        }

        result, errors = self.manager.resolve_work_item(
            work_items,
            "EPIC-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            reason="Epic verification passed.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertTrue(
            any(
                "FEATURE-1" in error and "Resolved" in error
                for error in errors
            )
        )
        self.assertEqual(epic.state, WorkItemState.IN_TEST)

    def test_epic_completes_full_resolution_lifecycle(self):
        epic = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
            state=WorkItemState.IN_TEST,
            relationships=(
                WorkItemRelationship(
                    "EPIC-1",
                    "FEATURE-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            state=WorkItemState.RESOLVED,
        )

        work_items = {
            "EPIC-1": epic,
            "FEATURE-1": feature,
        }

        result, errors = self.manager.resolve_work_item(
            work_items,
            "EPIC-1",
            AgentRole.QA,
            verification_passed=True,
            acceptance_criteria_met=True,
            reason="Epic verification passed.",
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            result["EPIC-1"].state,
            WorkItemState.RESOLVED,
        )
        self.assertEqual(
            epic.state,
            WorkItemState.IN_TEST,
        )


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
