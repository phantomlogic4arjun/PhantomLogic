
import unittest
from uuid import uuid4

from sqlalchemy import delete

from PhantomLogic.Database.DatabaseManager import DatabaseManager
from PhantomLogic.Database.Models.WorkItemRecord import WorkItemRecord
from PhantomLogic.Database.Repositories.WorkItemRepository import (
    WorkItemRepository,
)
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
from PhantomLogic.WorkItems.Services.WorkItemService import WorkItemService


class TestWorkItemIntegration(unittest.TestCase):

    def setUp(self):
        self.manager = WorkItemManager()
        self.created_ids = []

    def create_id(self):
        work_item_id = f"INTEGRATION-{uuid4().hex}"
        self.created_ids.append(work_item_id)
        return work_item_id

    def create_item(
        self,
        work_item_id,
        title,
        work_item_type=WorkItemType.FEATURE,
        created_by="Product Manager",
        state=WorkItemState.PROPOSED,
        build_number=None,
        relationships=(),
        audit_references=(),
        acceptance_criteria=(),
    ):
        return WorkItem(
            id=work_item_id,
            title=title,
            work_item_type=work_item_type,
            created_by=created_by,
            state=state,
            build_number=build_number,
            relationships=relationships,
            audit_references=audit_references,
            acceptance_criteria=acceptance_criteria,
        )

    def create_valid_hierarchy(self, build_number="1.00"):

        feature_id = self.create_id()
        use_case_id = self.create_id()
        requirement_id = self.create_id()
        test_case_id = self.create_id()
        development_task_id = self.create_id()
        code_review_id = self.create_id()

        feature = self.create_item(
            feature_id,
            "Integration Feature",
            relationships=(
                WorkItemRelationship(
                    feature_id,
                    use_case_id,
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    feature_id,
                    code_review_id,
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        use_case = self.create_item(
            use_case_id,
            "Integration Use Case",
            work_item_type=WorkItemType.USE_CASE,
            relationships=(
                WorkItemRelationship(
                    use_case_id,
                    requirement_id,
                    RelationshipType.PARENT_CHILD,
                ),
                WorkItemRelationship(
                    use_case_id,
                    development_task_id,
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        requirement = self.create_item(
            requirement_id,
            "Integration Requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            build_number=build_number,
            relationships=(
                WorkItemRelationship(
                    requirement_id,
                    test_case_id,
                    RelationshipType.PARENT_CHILD,
                ),
            ),
        )

        test_case = self.create_item(
            test_case_id,
            "Integration Test Case",
            work_item_type=WorkItemType.TEST_CASE,
            build_number=build_number,
        )

        development_task = self.create_item(
            development_task_id,
            "Integration Development Task",
            work_item_type=WorkItemType.DEVELOPMENT_TASK,
        )

        code_review = self.create_item(
            code_review_id,
            "Integration Code Review",
            work_item_type=WorkItemType.CODE_REVIEW_TASK,
            state=CodeReviewState.PROPOSED,
        )

        items = (
            feature,
            use_case,
            requirement,
            test_case,
            development_task,
            code_review,
        )

        ids = {
            "feature": feature_id,
            "use_case": use_case_id,
            "requirement": requirement_id,
            "test_case": test_case_id,
            "development_task": development_task_id,
            "code_review": code_review_id,
        }

        return items, ids

    def register_hierarchy(self, items):

        return WorkItemService.execute_with_events(
            WorkItemManager.register_work_items_with_events,
            items,
            AgentRole.PRODUCT_MANAGER,
            actor_id="Product Manager",
        )

    def register_item(self, work_item, actor_role, actor_id):

        return WorkItemService.execute_with_events(
            WorkItemManager.register_work_item_with_events,
            work_item,
            actor_role,
            actor_id=actor_id,
        )

    def tearDown(self):

        if not self.created_ids:
            return

        session = DatabaseManager.get_session()

        try:
            session.execute(
                delete(WorkItemRecord).where(
                    WorkItemRecord.id.in_(self.created_ids)
                )
            )
            session.commit()

        finally:
            session.close()

    def test_register_work_item_and_persist_to_postgresql(self):

        work_item_id = self.create_id()

        work_item = self.create_item(
            work_item_id,
            "Integration Test Feature",
            acceptance_criteria=(
                "Feature is registered successfully.",
                "Feature is persisted in PostgreSQL.",
            ),
        )

        result, errors, events = self.register_item(
            work_item,
            AgentRole.PRODUCT_MANAGER,
            "Product Manager",
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertIn(work_item_id, result)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "WORK_ITEM_CREATED")
        self.assertEqual(events[0]["work_item_id"], work_item_id)
        self.assertEqual(events[0]["outcome"], "Successful")

        persisted_item = WorkItemRepository.get_by_id(work_item_id)

        self.assertIsNotNone(persisted_item)
        self.assertEqual(persisted_item.id, work_item.id)
        self.assertEqual(persisted_item.title, work_item.title)
        self.assertEqual(
            persisted_item.acceptance_criteria,
            work_item.acceptance_criteria,
        )

    def test_requirement_build_number_update_persists_both_items(self):

        items, ids = self.create_valid_hierarchy()

        result, errors, events = self.register_hierarchy(items)

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), len(items))

        result, errors, events = (
            WorkItemService.execute_with_events(
                self.manager.update_build_number_with_events,
                ids["requirement"],
                "1.01",
                AgentRole.PRODUCT_MANAGER,
                actor_id="Product Manager",
            )
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), 1)

        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_BUILD_NUMBER_UPDATED",
        )

        persisted_requirement = WorkItemRepository.get_by_id(
            ids["requirement"]
        )

        persisted_test_case = WorkItemRepository.get_by_id(
            ids["test_case"]
        )

        self.assertEqual(persisted_requirement.build_number, "1.01")
        self.assertEqual(persisted_test_case.build_number, "1.01")

    def test_state_transition_persists_to_postgresql(self):

        work_item_id = self.create_id()

        work_item = self.create_item(
            work_item_id,
            "Integration Test State Transition",
            state=WorkItemState.IN_WORK,
        )

        _, errors, _ = self.register_item(
            work_item,
            AgentRole.PRODUCT_MANAGER,
            "Product Manager",
        )

        self.assertEqual(errors, [])

        result, errors, events = (
            WorkItemService.execute_with_events(
                self.manager.transition_state_with_events,
                work_item_id,
                WorkItemState.BLOCKED,
                AgentRole.DEVELOPER,
                actor_id="Developer-1",
                reason="Integration test dependency",
            )
        )

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), 1)

        self.assertEqual(
            events[0]["event_type"],
            "WORK_ITEM_STATE_TRANSITIONED",
        )

        persisted_item = WorkItemRepository.get_by_id(work_item_id)

        self.assertEqual(
            persisted_item.state,
            WorkItemState.BLOCKED,
        )

        self.assertEqual(
            persisted_item.block_reason,
            "Integration test dependency",
        )

    def test_relationships_persist_to_postgresql(self):

        items, ids = self.create_valid_hierarchy()

        result, errors, events = self.register_hierarchy(items)

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), len(items))

        persisted_feature = WorkItemRepository.get_by_id(
            ids["feature"]
        )

        persisted_use_case = WorkItemRepository.get_by_id(
            ids["use_case"]
        )

        persisted_requirement = WorkItemRepository.get_by_id(
            ids["requirement"]
        )

        self.assertEqual(
            set(persisted_feature.relationships),
            set(items[0].relationships),
        )

        self.assertEqual(
            set(persisted_use_case.relationships),
            set(items[1].relationships),
        )

        self.assertEqual(
            persisted_requirement.relationships,
            items[2].relationships,
        )

    def test_audit_references_persist_in_original_order(self):

        work_item_id = self.create_id()

        references = (
            "AUDIT-REF-001",
            "AUDIT-REF-002",
            "AUDIT-REF-003",
        )

        work_item = self.create_item(
            work_item_id,
            "Integration Test Audit References",
            audit_references=references,
        )

        _, errors, _ = self.register_item(
            work_item,
            AgentRole.PRODUCT_MANAGER,
            "Product Manager",
        )

        self.assertEqual(errors, [])

        persisted_item = WorkItemRepository.get_by_id(work_item_id)

        self.assertEqual(
            persisted_item.audit_references,
            references,
        )

    def test_failed_operation_does_not_change_persisted_work_item(self):

        work_item_id = self.create_id()

        work_item = self.create_item(
            work_item_id,
            "Integration Test Failed Operation",
        )

        _, errors, _ = self.register_item(
            work_item,
            AgentRole.PRODUCT_MANAGER,
            "Product Manager",
        )

        self.assertEqual(errors, [])

        original_item = WorkItemRepository.get_by_id(work_item_id)

        result, errors, events = (
            WorkItemService.execute_with_events(
                self.manager.update_build_number_with_events,
                work_item_id,
                "1.01",
                AgentRole.PRODUCT_MANAGER,
                actor_id="Product Manager",
            )
        )

        self.assertIsNone(result)
        self.assertTrue(errors)
        self.assertEqual(events, ())

        persisted_item = WorkItemRepository.get_by_id(work_item_id)

        self.assertEqual(persisted_item, original_item)

    def test_batch_registration_persists_all_work_items(self):

        items, ids = self.create_valid_hierarchy()

        result, errors, events = self.register_hierarchy(items)

        self.assertEqual(errors, [])
        self.assertIsNotNone(result)
        self.assertEqual(len(events), len(items))

        self.assertEqual(
            {event["work_item_id"] for event in events},
            set(ids.values()),
        )

        for work_item_id in ids.values():

            persisted_item = WorkItemRepository.get_by_id(work_item_id)

            self.assertIsNotNone(persisted_item)
            self.assertEqual(persisted_item.id, work_item_id)


if __name__ == "__main__":
    unittest.main()
