

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from PhantomLogic.WorkItems.Manager.WorkItemManager import WorkItemManager
from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from PhantomLogic.WorkItems.Models.WorkItemState import WorkItemState
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.PermissionRules import AgentRole


class TestAuthorizedWorkPropagation(unittest.TestCase):

    def setUp(self):
        self.manager = WorkItemManager()

    @staticmethod
    def create_item(
        item_id,
        item_type,
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

    def create_hierarchy(self, bug_state=WorkItemState.PROPOSED):
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

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            state=bug_state,
            relationships=(
                WorkItemRelationship(
                    "BUG-1",
                    "REQ-1",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
                WorkItemRelationship(
                    "BUG-1",
                    "REQ-2",
                    RelationshipType.VIOLATED_REQUIREMENT,
                ),
            ),
        )

        return {
            "FEATURE-1": feature,
            "UC-1": use_case,
            "REQ-1": requirement_1,
            "REQ-2": requirement_2,
            "BUG-1": bug,
        }

    def authorize_bug(self, work_items):
        return self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-001",
            reason="Authorize correction of the reported defect.",
        )

    # ----------------------------------------------------------
    # Explicit authorization
    # ----------------------------------------------------------

    def test_authorize_bug_records_evidence_without_changing_state(self):
        work_items = self.create_hierarchy()

        result, errors = self.authorize_bug(work_items)

        self.assertEqual(errors, [])

        original = work_items["BUG-1"]
        authorized = result["BUG-1"]

        self.assertEqual(authorized.state, WorkItemState.PROPOSED)
        self.assertEqual(original.state, WorkItemState.PROPOSED)
        self.assertEqual(authorized.authorized_by, "PM-001")
        self.assertEqual(
            authorized.authorization_reason,
            "Authorize correction of the reported defect.",
        )
        self.assertIsNotNone(authorized.authorized_at)
        self.assertEqual(
            authorized.authorized_at.utcoffset(),
            timedelta(0),
        )

    def test_authorize_change_request_records_evidence(self):
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
            "REQ-1": requirement,
            "CR-1": change_request,
        }

        result, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-001",
            reason="Approve requested scope change.",
        )

        self.assertEqual(errors, [])
        self.assertEqual(result["CR-1"].state, WorkItemState.PROPOSED)
        self.assertEqual(result["CR-1"].authorized_by, "PM-001")

    def test_authorization_rejects_non_product_manager(self):
        work_items = self.create_hierarchy()

        result, errors = self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.DEVELOPER,
            actor_id="DEV-001",
            reason="Attempted authorization.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_authorization_rejects_missing_actor_identity(self):
        work_items = self.create_hierarchy()

        result, errors = self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id=" ",
            reason="Valid reason.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_authorization_rejects_missing_reason(self):
        work_items = self.create_hierarchy()

        result, errors = self.manager.authorize_work(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-001",
            reason=" ",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_authorization_rejects_missing_item(self):
        result, errors = self.manager.authorize_work(
            {},
            "MISSING",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-001",
            reason="Authorize work.",
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_authorization_rejects_removed_item(self):
        work_items = self.create_hierarchy()

        work_items["BUG-1"] = replace(
            work_items["BUG-1"],
            state=WorkItemState.REMOVED,
            removal_reason="No longer required.",
        )

        result, errors = self.authorize_bug(work_items)

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_authorization_returns_audit_event_separately(self):
        work_items = self.create_hierarchy()

        result, errors, events = self.manager.authorize_work_with_events(
            work_items,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-001",
            reason="Authorize correction.",
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["event_type"],
            "WORK_AUTHORIZED",
        )
        self.assertEqual(events[0]["work_item_id"], "BUG-1")
        self.assertEqual(events[0]["actor_id"], "PM-001")
        self.assertIsNotNone(result)

    # ----------------------------------------------------------
    # Authorized propagation
    # ----------------------------------------------------------

    def test_propagation_moves_entire_affected_hierarchy_to_in_work(self):
        work_items = self.create_hierarchy()

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])

        for item_id in (
            "BUG-1",
            "REQ-1",
            "REQ-2",
            "UC-1",
            "FEATURE-1",
        ):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
                item_id,
            )

    def test_propagation_deduplicates_shared_parent_items(self):
        work_items = self.create_hierarchy()

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors, events = (
            self.manager.start_authorized_work_with_events(
                authorized,
                "BUG-1",
                AgentRole.WORK_ITEM_MANAGER,
                actor_id="Developer-1",
            )
        )

        self.assertEqual(errors, [])

        changed_ids = {
            event["work_item_id"]
            for event in events
        }

        self.assertEqual(
            changed_ids,
            {
                "BUG-1",
                "REQ-1",
                "REQ-2",
                "UC-1",
                "FEATURE-1",
            },
        )

        for event in events:
            self.assertEqual(event["actor_id"], "Developer-1")
            self.assertEqual(
                event["actor_role"],
                AgentRole.WORK_ITEM_MANAGER.value,
            )

    def test_propagation_reopens_resolved_hierarchy(self):
        work_items = self.create_hierarchy()

        for item_id in ("REQ-1", "REQ-2", "UC-1", "FEATURE-1"):
            work_items[item_id] = replace(
                work_items[item_id],
                state=WorkItemState.RESOLVED,
                resolution_reason="Previously verified.",
            )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])

        for item_id in ("REQ-1", "REQ-2", "UC-1", "FEATURE-1"):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )

    def test_propagation_can_move_in_test_items_to_in_work(self):
        work_items = self.create_hierarchy()

        for item_id in ("REQ-1", "REQ-2", "UC-1", "FEATURE-1"):
            work_items[item_id] = replace(
                work_items[item_id],
                state=WorkItemState.IN_TEST,
            )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])

        for item_id in ("REQ-1", "REQ-2", "UC-1", "FEATURE-1"):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )

    def test_propagation_preserves_blocked_state_and_updates_return_state(self):
        work_items = self.create_hierarchy()

        work_items["REQ-1"] = replace(
            work_items["REQ-1"],
            state=WorkItemState.BLOCKED,
            blocked_return_state=WorkItemState.IN_TEST,
            block_reason="Waiting for an external dependency.",
        )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])

        requirement = result["REQ-1"]

        self.assertEqual(requirement.state, WorkItemState.BLOCKED)
        self.assertEqual(
            requirement.blocked_return_state,
            WorkItemState.IN_WORK,
        )
        self.assertEqual(
            requirement.block_reason,
            "Waiting for an external dependency.",
        )

    def test_propagation_updates_blocked_source_return_state(self):
        work_items = self.create_hierarchy(
            bug_state=WorkItemState.BLOCKED,
        )

        work_items["BUG-1"] = replace(
            work_items["BUG-1"],
            blocked_return_state=WorkItemState.PROPOSED,
            block_reason="Waiting for approval dependency.",
        )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            result["BUG-1"].state,
            WorkItemState.BLOCKED,
        )
        self.assertEqual(
            result["BUG-1"].blocked_return_state,
            WorkItemState.IN_WORK,
        )

    # ----------------------------------------------------------
    # Authorization and integrity enforcement
    # ----------------------------------------------------------

    def test_propagation_rejects_missing_authorization(self):
        work_items = self.create_hierarchy()

        result, errors = self.manager.start_authorized_work(
            work_items,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_propagation_rejects_non_work_item_manager(self):
        work_items = self.create_hierarchy()

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.PRODUCT_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_propagation_rejects_removed_requirement_atomically(self):
        work_items = self.create_hierarchy()

        work_items["REQ-2"] = replace(
            work_items["REQ-2"],
            state=WorkItemState.REMOVED,
            removal_reason="Explicitly removed.",
        )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

        self.assertEqual(
            authorized["REQ-1"].state,
            WorkItemState.PROPOSED,
        )
        self.assertEqual(
            authorized["FEATURE-1"].state,
            WorkItemState.PROPOSED,
        )

    def test_propagation_rejects_removed_parent_atomically(self):
        work_items = self.create_hierarchy()

        work_items["FEATURE-1"] = replace(
            work_items["FEATURE-1"],
            state=WorkItemState.REMOVED,
            removal_reason="Feature removed.",
        )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

        self.assertEqual(
            authorized["REQ-1"].state,
            WorkItemState.PROPOSED,
        )

    def test_propagation_rejects_missing_use_case_parent(self):
        work_items = self.create_hierarchy()

        feature = work_items["FEATURE-1"]
        use_case = work_items["UC-1"]

        work_items["FEATURE-1"] = replace(
            feature,
            relationships=(),
        )

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertIsNone(result)
        self.assertTrue(errors)

    def test_propagation_does_not_mutate_original_mapping(self):
        work_items = self.create_hierarchy()

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        original_states = {
            item_id: item.state
            for item_id, item in authorized.items()
        }

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertIsNot(result, authorized)

        for item_id, original_state in original_states.items():
            self.assertEqual(
                authorized[item_id].state,
                original_state,
            )

    def test_propagation_does_not_change_unrelated_feature(self):
        work_items = self.create_hierarchy()

        unrelated_feature = self.create_item(
            "FEATURE-2",
            WorkItemType.FEATURE,
        )
        work_items["FEATURE-2"] = unrelated_feature

        authorized, errors = self.authorize_bug(work_items)
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "BUG-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            result["FEATURE-2"].state,
            WorkItemState.PROPOSED,
        )

    def test_change_request_propagates_using_affected_requirement_links(self):
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

        authorized, errors = self.manager.authorize_work(
            work_items,
            "CR-1",
            AgentRole.PRODUCT_MANAGER,
            actor_id="PM-001",
            reason="Approve requested change.",
        )
        self.assertEqual(errors, [])

        result, errors = self.manager.start_authorized_work(
            authorized,
            "CR-1",
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertEqual(errors, [])

        for item_id in ("CR-1", "REQ-1", "UC-1", "FEATURE-1"):
            self.assertEqual(
                result[item_id].state,
                WorkItemState.IN_WORK,
            )


if __name__ == "__main__":
    unittest.main()
