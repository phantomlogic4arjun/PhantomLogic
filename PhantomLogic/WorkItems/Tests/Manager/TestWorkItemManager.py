
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
from dataclasses import replace


class TestWorkItemManager(unittest.TestCase):

    def setUp(self):
        self.manager = WorkItemManager()

    @staticmethod
    def create_item(
        item_id="ITEM-1",
        item_type=WorkItemType.FEATURE,
        state=WorkItemState.PROPOSED,
        relationships=(),
        build_number=None,
    ):
        return WorkItem(
            id=item_id,
            title=f"Test {item_id}",
            work_item_type=item_type,
            created_by="Product Manager",
            state=state,
            relationships=relationships,
            acceptance_criteria=("Acceptance criterion",),
            build_number=build_number,
        )
    def create_requirement_with_test_case(
        self,
        requirement_build="1.00",
        test_case_build="1.00",
        test_case_ids=("TEST-1",),
    ):
        relationships = tuple(
            WorkItemRelationship(
                source_id="REQ-1",
                target_id=test_case_id,
                relationship_type=RelationshipType.PARENT_CHILD,
            )
            for test_case_id in test_case_ids
        )

        requirement = self.create_item(
            item_id="REQ-1",
            item_type=WorkItemType.REQUIREMENT,
            build_number=requirement_build,
            relationships=relationships,
        )

        test_cases = {
            test_case_id: self.create_item(
                item_id=test_case_id,
                item_type=WorkItemType.TEST_CASE,
                build_number=test_case_build,
            )
            for test_case_id in test_case_ids
        }

        work_items = {
            "REQ-1": requirement,
            **test_cases,
        }

        return work_items


    def test_update_build_number_updates_requirement_and_test_case(self):
        work_items = self.create_requirement_with_test_case()

        result, errors = self.manager.update_build_number(
            work_items,
            "REQ-1",
            "1.01",
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertEqual(result["REQ-1"].build_number, "1.01")
        self.assertEqual(result["TEST-1"].build_number, "1.01")

        # Both Work Items receive the same update timestamp.
        self.assertIsNotNone(result["REQ-1"].updated_at)
        self.assertEqual(
            result["REQ-1"].updated_at,
            result["TEST-1"].updated_at,
        )

        # Original collection remains unchanged.
        self.assertEqual(work_items["REQ-1"].build_number, "1.00")
        self.assertEqual(work_items["TEST-1"].build_number, "1.00")

    def test_update_build_number_rejects_unauthorized_role(self):
        work_items = self.create_requirement_with_test_case()

        result, errors = self.manager.update_build_number(
            work_items,
            "REQ-1",
            "1.01",
            AgentRole.DEVELOPER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_update_build_number_rejects_direct_test_case_update(self):
        work_items = self.create_requirement_with_test_case()

        result, errors = self.manager.update_build_number(
            work_items,
            "TEST-1",
            "1.01",
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_update_build_number_requires_exactly_one_test_case(self):
        work_items = self.create_requirement_with_test_case(
            test_case_ids=(),
        )

        result, errors = self.manager.update_build_number(
            work_items,
            "REQ-1",
            "1.01",
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_update_build_number_rejects_multiple_test_cases(self):
        work_items = self.create_requirement_with_test_case(
            test_case_ids=("TEST-1", "TEST-2"),
        )

        result, errors = self.manager.update_build_number(
            work_items,
            "REQ-1",
            "1.01",
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
    def test_update_build_number_rejects_test_case_shared_by_two_requirements(self):
        shared_test_case = self.create_item(
            item_id="TEST-1",
            item_type=WorkItemType.TEST_CASE,
            build_number="1.00",
        )

        requirement_1 = self.create_item(
            item_id="REQ-1",
            item_type=WorkItemType.REQUIREMENT,
            build_number="1.00",
            relationships=(
                WorkItemRelationship(
                    source_id="REQ-1",
                    target_id="TEST-1",
                    relationship_type=RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement_2 = self.create_item(
            item_id="REQ-2",
            item_type=WorkItemType.REQUIREMENT,
            build_number="1.00",
            relationships=(
                WorkItemRelationship(
                    source_id="REQ-2",
                    target_id="TEST-1",
                    relationship_type=RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        work_items = {
            "REQ-1": requirement_1,
            "REQ-2": requirement_2,
            "TEST-1": shared_test_case,
        }

        updated_items, errors = WorkItemManager.update_build_number(
            work_items,
            "REQ-1",
            "1.01",
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(updated_items)
        self.assertTrue(errors)

        self.assertEqual(work_items["REQ-1"].build_number, "1.00")
        self.assertEqual(work_items["REQ-2"].build_number, "1.00")
        self.assertEqual(work_items["TEST-1"].build_number, "1.00")

    def test_update_build_number_with_events_succeeds(self):
        work_items = self.create_requirement_with_test_case()

        result, errors, events = (
            self.manager.update_build_number_with_events(
                work_items,
                "REQ-1",
                "1.01",
                AgentRole.PRODUCT_MANAGER,
                actor_id="PM-1",
            )
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(events), 1)

        event = events[0]

        self.assertEqual(
            event["event_type"],
            "WORK_ITEM_BUILD_NUMBER_UPDATED",
        )
        self.assertEqual(event["work_item_id"], "REQ-1")
        self.assertEqual(event["related_work_item_id"], "TEST-1")
        self.assertEqual(event["previous_build_number"], "1.00")
        self.assertEqual(event["new_build_number"], "1.01")

        self.assertEqual(
            event["actor_role"],
            AgentRole.PRODUCT_MANAGER.value,
        )
        self.assertEqual(event["actor_id"], "PM-1")
        self.assertEqual(event["outcome"], "Successful")

        # Audit event timestamp matches the actual Work Item update.
        self.assertEqual(
            event["occurred_at"],
            result["REQ-1"].updated_at.isoformat(),
        )

        self.assertEqual(result["REQ-1"].build_number, "1.01")
        self.assertEqual(result["TEST-1"].build_number, "1.01")

        # Both Work Items share the same timestamp.
        self.assertEqual(
            result["REQ-1"].updated_at,
            result["TEST-1"].updated_at,
        )

    def test_update_build_number_with_events_requires_actor_identity(self):
        work_items = self.create_requirement_with_test_case()

        result, errors, events = (
            self.manager.update_build_number_with_events(
                work_items,
                "REQ-1",
                "1.01",
                AgentRole.PRODUCT_MANAGER,
                actor_id=" ",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

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


    def test_register_change_request_with_events_succeeds(self):
        requirement = self.create_item(
            item_id="REQ-1",
            item_type=WorkItemType.REQUIREMENT,
        )

        relationship = WorkItemRelationship(
            source_id="CR-1",
            target_id="REQ-1",
            relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
        )

        change_request = self.create_item(
            item_id="CR-1",
            item_type=WorkItemType.CHANGE_REQUEST,
            relationships=(relationship,),
        )

        result, errors, events = (
            self.manager.register_work_item_with_events(
                {"REQ-1": requirement},
                change_request,
                AgentRole.PRODUCT_MANAGER,
                actor_id="Product Manager",
            )
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertIn("CR-1", result)
        self.assertEqual(len(events), 1)

        event = events[0]

        self.assertEqual(event["event_type"], "WORK_ITEM_CREATED")
        self.assertEqual(event["work_item_id"], "CR-1")
        self.assertEqual(
            event["work_item_type"],
            WorkItemType.CHANGE_REQUEST.value,
        )
        self.assertEqual(
            event["actor_role"],
            AgentRole.PRODUCT_MANAGER.value,
        )
        self.assertEqual(event["actor_id"], "Product Manager")
        self.assertEqual(event["outcome"], "Successful")

    def test_register_change_request_with_events_rejects_unauthorized_role(self):
        item = self.create_item(
            item_id="CR-2",
            item_type=WorkItemType.CHANGE_REQUEST,
        )

        result, errors, events = (
            self.manager.register_work_item_with_events(
                {},
                item,
                AgentRole.DEVELOPER,
                actor_id="Developer",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

    def test_register_change_request_with_events_requires_actor_identity(self):
        item = self.create_item(
            item_id="CR-3",
            item_type=WorkItemType.CHANGE_REQUEST,
        )

        result, errors, events = (
            self.manager.register_work_item_with_events(
                {},
                item,
                AgentRole.PRODUCT_MANAGER,
                actor_id=" ",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

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

    def test_register_work_items_with_events_succeeds(self):
        work_items = {}
        additions = (
            self.create_item(item_id="ITEM-1"),
            self.create_item(item_id="ITEM-2"),
        )

        result, errors, events = (
            self.manager.register_work_items_with_events(
                work_items,
                additions,
                AgentRole.PRODUCT_MANAGER,
                actor_id="Product Manager",
            )
        )

        self.assertEqual(errors, [])
        self.assertEqual(set(result.keys()), {"ITEM-1", "ITEM-2"})
        self.assertEqual(len(events), 2)

        self.assertEqual(
            {event["work_item_id"] for event in events},
            {"ITEM-1", "ITEM-2"},
        )

        for event in events:
            self.assertEqual(event["event_type"], "WORK_ITEM_CREATED")
            self.assertEqual(event["actor_role"], "Product Manager")
            self.assertEqual(event["actor_id"], "Product Manager")
            self.assertEqual(event["outcome"], "Successful")

        self.assertEqual(work_items, {})

    def test_register_work_items_with_events_rejects_blank_actor_id(self):
        additions = (self.create_item(item_id="ITEM-1"),)

        result, errors, events = (
            self.manager.register_work_items_with_events(
                {},
                additions,
                AgentRole.PRODUCT_MANAGER,
                actor_id=" ",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

    def test_register_work_items_with_events_rejects_creator_mismatch(self):
        item = replace(
            self.create_item(item_id="ITEM-1"),
            created_by="Developer",
        )

        result, errors, events = (
            self.manager.register_work_items_with_events(
                {},
                (item,),
                AgentRole.PRODUCT_MANAGER,
                actor_id="Product Manager",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

    def test_register_work_items_with_events_returns_no_events_on_registration_failure(self):
        existing_item = self.create_item(item_id="ITEM-1")
        duplicate_item = self.create_item(item_id="ITEM-1")

        result, errors, events = (
            self.manager.register_work_items_with_events(
                {"ITEM-1": existing_item},
                (duplicate_item,),
                AgentRole.PRODUCT_MANAGER,
                actor_id="Product Manager",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

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

    def test_add_relationship_with_events_succeeds(self):
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

        result, errors, events = self.manager.add_relationship_with_events(
            work_items,
            relationship,
            AgentRole.PRODUCT_MANAGER,
            actor_id="Product Manager",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertIn(relationship, result["FEATURE-1"].relationships)
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_RELATIONSHIP_ADDED",
        )
        self.assertEqual(
            events[0]["source_work_item_id"],
            "FEATURE-1",
        )
        self.assertEqual(
            events[0]["target_work_item_id"],
            "UC-1",
        )
        self.assertEqual(
            events[0]["actor_id"],
            "Product Manager",
        )
        self.assertEqual(events[0]["outcome"], "Successful")





    def test_remove_relationship_with_events_succeeds(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1",
                    "REVIEW-1",
                    RelationshipType.PARENT_CHILD,
                ),
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
                    "DEV-1",
                    RelationshipType.PARENT_CHILD,
                ),
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

        code_review = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.PROPOSED,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        requirement_1 = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            relationships=(
                WorkItemRelationship(
                    "REQ-1",
                    "TEST-1",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )
        requirement_2 = self.create_item(
            "REQ-2",
            WorkItemType.REQUIREMENT,
            relationships=(
                WorkItemRelationship(
                    "REQ-2",
                    "TEST-2",
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        test_case_1 = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        test_case_2 = self.create_item(
            "TEST-2",
            WorkItemType.TEST_CASE,
        )

        relationship_to_remove = WorkItemRelationship(
            "CR-1",
            "REQ-1",
            RelationshipType.AFFECTED_REQUIREMENT,
        )
        relationship_to_keep = WorkItemRelationship(
            "CR-1",
            "REQ-2",
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            relationships=(
                relationship_to_remove,
                relationship_to_keep,
            ),
        )

        work_items = {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REVIEW-1": code_review,
            "DEV-1": development_task,
            "REQ-1": requirement_1,
            "REQ-2": requirement_2,
            "TEST-1": test_case_1,
            "TEST-2": test_case_2,
            "CR-1": change_request,
        }

        result, errors, events = self.manager.remove_relationship_with_events(
            work_items,
            relationship_to_remove,
            AgentRole.PRODUCT_MANAGER,
            actor_id="Product Manager",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertNotIn(
            relationship_to_remove,
            result["CR-1"].relationships,
        )
        self.assertIn(
            relationship_to_keep,
            result["CR-1"].relationships,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_RELATIONSHIP_REMOVED",
        )
        self.assertEqual(events[0]["source_work_item_id"], "CR-1")
        self.assertEqual(events[0]["target_work_item_id"], "REQ-1")
        self.assertEqual(events[0]["actor_id"], "Product Manager")





    def test_add_relationships_with_events_succeeds(self):
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

        result, errors, events = self.manager.add_relationships_with_events(
            work_items,
            (relationship,),
            AgentRole.PRODUCT_MANAGER,
            actor_id="Product Manager",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_RELATIONSHIP_ADDED",
        )

    def test_add_relationship_with_events_rejects_missing_actor_id(self):
        relationship = WorkItemRelationship(
            "FEATURE-1",
            "UC-1",
            RelationshipType.PARENT_CHILD,
        )

        result, errors, events = self.manager.add_relationship_with_events(
            {},
            relationship,
            AgentRole.PRODUCT_MANAGER,
            actor_id=" ",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

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

    def test_authorized_bug_propagates_new_requirement_after_start(self):
        feature1 = self.create_item("FEATURE-1", WorkItemType.FEATURE)
        use_case1 = self.create_item("UC-1", WorkItemType.USE_CASE)
        requirement1 = self.create_item("REQ-1", WorkItemType.REQUIREMENT)

        feature2 = self.create_item("FEATURE-2", WorkItemType.FEATURE)
        use_case2 = self.create_item("UC-2", WorkItemType.USE_CASE)
        requirement2 = self.create_item("REQ-2", WorkItemType.REQUIREMENT)

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

        feature1 = replace_for_test(
            feature1,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )
        use_case1 = replace_for_test(
            use_case1,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )
        feature2 = replace_for_test(
            feature2,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-2", "UC-2", RelationshipType.PARENT_CHILD
                ),
            ),
        )
        use_case2 = replace_for_test(
            use_case2,
            relationships=(
                WorkItemRelationship(
                    "UC-2", "REQ-2", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        work_items = {
            item.id: item
            for item in (
                feature1, use_case1, requirement1,
                feature2, use_case2, requirement2, bug,
            )
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved to fix the reported defect.",
        )
        self.assertEqual(errors, [])

        started_items, errors = self.manager.start_authorized_work(
            authorized_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )
        self.assertEqual(errors, [])

        updated_bug = replace_for_test(
            started_items["BUG-1"],
            relationships=(
                *started_items["BUG-1"].relationships,
                WorkItemRelationship(
                    "BUG-1",
                    "REQ-2",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        updated_items = dict(started_items)
        updated_items["BUG-1"] = updated_bug

        result, errors = self.manager.start_authorized_work(
            updated_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        for item_id in ("BUG-1", "REQ-1", "UC-1", "FEATURE-1",
                        "REQ-2", "UC-2", "FEATURE-2"):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
                item_id,
            )


    def test_authorized_change_request_propagates_new_requirement_after_start(self):
        feature1 = self.create_item("FEATURE-1", WorkItemType.FEATURE)
        use_case1 = self.create_item("UC-1", WorkItemType.USE_CASE)
        requirement1 = self.create_item("REQ-1", WorkItemType.REQUIREMENT)

        feature2 = self.create_item("FEATURE-2", WorkItemType.FEATURE)
        use_case2 = self.create_item("UC-2", WorkItemType.USE_CASE)
        requirement2 = self.create_item("REQ-2", WorkItemType.REQUIREMENT)

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

        feature1 = replace_for_test(
            feature1,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-1", "UC-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )
        use_case1 = replace_for_test(
            use_case1,
            relationships=(
                WorkItemRelationship(
                    "UC-1", "REQ-1", RelationshipType.PARENT_CHILD
                ),
            ),
        )
        feature2 = replace_for_test(
            feature2,
            relationships=(
                WorkItemRelationship(
                    "FEATURE-2", "UC-2", RelationshipType.PARENT_CHILD
                ),
            ),
        )
        use_case2 = replace_for_test(
            use_case2,
            relationships=(
                WorkItemRelationship(
                    "UC-2", "REQ-2", RelationshipType.PARENT_CHILD
                ),
            ),
        )

        work_items = {
            item.id: item
            for item in (
                feature1, use_case1, requirement1,
                feature2, use_case2, requirement2, change_request,
            )
        }

        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved to implement the requested change.",
        )
        self.assertEqual(errors, [])

        started_items, errors = self.manager.start_authorized_work(
            authorized_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )
        self.assertEqual(errors, [])

        updated_cr = replace_for_test(
            started_items["CR-1"],
            relationships=(
                *started_items["CR-1"].relationships,
                WorkItemRelationship(
                    "CR-1",
                    "REQ-2",
                    RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )

        updated_items = dict(started_items)
        updated_items["CR-1"] = updated_cr

        result, errors = self.manager.start_authorized_work(
            updated_items,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        for item_id in ("CR-1", "REQ-1", "UC-1", "FEATURE-1",
                        "REQ-2", "UC-2", "FEATURE-2"):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
                item_id,
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
            actor_id="Developer-1",
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
            actor_id="Developer-1",
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

    def test_authorize_work_rejects_reauthorization(self):
        feature = self.create_item(
            "FEATURE-1",
            WorkItemType.FEATURE,
        )
        work_items = {
            "FEATURE-1": feature,
        }

        # First authorization should succeed.
        authorized_items, errors = self.manager.authorize_work(
            work_items,
            "FEATURE-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Initial approval.",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(authorized_items)

        original_authorized_by = (
            authorized_items["FEATURE-1"].authorized_by
        )
        original_authorized_at = (
            authorized_items["FEATURE-1"].authorized_at
        )
        original_reason = (
            authorized_items["FEATURE-1"].authorization_reason
        )

        # A second authorization should be rejected.
        result, errors = self.manager.authorize_work(
            authorized_items,
            "FEATURE-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-2",
            reason="Attempted replacement approval.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

        # Original authorization evidence must remain unchanged.
        self.assertEqual(
            authorized_items["FEATURE-1"].authorized_by,
            original_authorized_by,
        )
        self.assertEqual(
            authorized_items["FEATURE-1"].authorized_at,
            original_authorized_at,
        )
        self.assertEqual(
            authorized_items["FEATURE-1"].authorization_reason,
            original_reason,
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


    def test_transition_state_with_events_succeeds(self):
        item = self.create_item(
            state=WorkItemState.IN_WORK,
        )

        result, errors, events = (
            self.manager.transition_state_with_events(
                {"ITEM-1": item},
                "ITEM-1",
                WorkItemState.BLOCKED,
                AgentRole.DEVELOPER,
                actor_id="Developer-1",
                reason="Waiting for a dependency",
            )
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(
            result["ITEM-1"].state,
            WorkItemState.BLOCKED,
        )
        self.assertEqual(
            events[0]["actor_id"],
            "Developer-1",
        )
        self.assertEqual(
            events[0]["previous_state"],
            WorkItemState.IN_WORK.value,
        )
        self.assertEqual(
            events[0]["new_state"],
            WorkItemState.BLOCKED.value,
        )
    def test_state_transition_preserves_build_number(self):
        item = self.create_item(
            item_id="REQ-1",
            item_type=WorkItemType.REQUIREMENT,
            state=WorkItemState.PROPOSED,
            build_number="1.01",
        )

        authorized_items, errors = self.manager.authorize_work(
            {"REQ-1": item},
            "REQ-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-1",
            reason="Approved for development.",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(authorized_items)
        # Verify authorization preserves the build number.
        self.assertEqual(
            authorized_items["REQ-1"].build_number,
            "1.01",
        )
        result, errors = self.manager.transition_state(
            authorized_items,
            "REQ-1",
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)

        updated_item = result["REQ-1"]

        self.assertEqual(updated_item.build_number, "1.01")
        self.assertEqual(updated_item.state, WorkItemState.IN_WORK)

        # The original Work Item remains unchanged.
        self.assertEqual(item.build_number, "1.01")
        self.assertEqual(item.state, WorkItemState.PROPOSED)

    def test_transition_state_with_events_requires_actor_id(self):
        item = self.create_item(
            state=WorkItemState.IN_WORK,
        )

        result, errors, events = (
            self.manager.transition_state_with_events(
                {"ITEM-1": item},
                "ITEM-1",
                WorkItemState.BLOCKED,
                AgentRole.DEVELOPER,
                actor_id=" ",
                reason="Waiting for a dependency",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())



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


    def test_submit_for_test_with_events_succeeds(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_WORK,
        )

        result, errors, events = (
            self.manager.submit_for_test_with_events(
                {"DEV-1": item},
                "DEV-1",
                AgentRole.DEVELOPER,
                actor_id="Developer-1",
                implementation_complete=True,
                changes_in_main=True,
                main_build_available=True,
                review_gates_satisfied=True,
                security_gate_passed=True,
                ci_gate_passed=True,
            )
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(
            result["DEV-1"].state,
            WorkItemState.IN_TEST,
        )
        self.assertEqual(
            events[0]["actor_id"],
            "Developer-1",
        )
        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_SUBMITTED_FOR_TEST",
        )

    def test_submit_for_test_with_events_requires_actor_id(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_WORK,
        )

        result, errors, events = (
            self.manager.submit_for_test_with_events(
                {"DEV-1": item},
                "DEV-1",
                AgentRole.DEVELOPER,
                actor_id=" ",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

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


    def test_resolve_work_item_with_events_succeeds(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        result, errors, events = (
            self.manager.resolve_work_item_with_events(
                {"DEV-1": item},
                "DEV-1",
                AgentRole.QA,
                actor_id="QA-1",
                verification_passed=True,
                acceptance_criteria_met=True,
                reason="QA verification passed.",
            )
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(
            result["DEV-1"].state,
            WorkItemState.RESOLVED,
        )
        self.assertEqual(
            events[0]["actor_id"],
            "QA-1",
        )
        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_RESOLVED",
        )

    def test_resolve_work_item_with_events_requires_actor_id(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            state=WorkItemState.IN_TEST,
        )

        result, errors, events = (
            self.manager.resolve_work_item_with_events(
                {"DEV-1": item},
                "DEV-1",
                AgentRole.QA,
                actor_id=" ",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

def replace_for_test(item, **changes):
    from dataclasses import replace
    return replace(item, **changes)


if __name__ == "__main__":
    unittest.main()
