
import unittest

from unittest.mock import patch

from phantom_logic.work_items.interfaces.WorkItemAgentInterface import (
    WorkItemAgentInterface,
)
from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType


SERVICE_PATH = (
    "phantom_logic.work_items.interfaces."
    "WorkItemAgentInterface.WorkItemService"
)

REPOSITORY_PATH = (
    "phantom_logic.work_items.services."
    "WorkItemService.WorkItemRepository"
)


class TestWorkItemAgentInterface(unittest.TestCase):

    def setUp(self):
        self.feature = {
            "id": "FEAT-001",
            "title": "Inventory Management",
            "work_item_type": "Feature",
            "description": "Manage inventory operations.",
            "priority": "High",
            "build_number": "1.0.0",
            "acceptance_criteria": [
                "Users can view inventory.",
                "Users can update inventory.",
            ],
        }

    @patch(f"{REPOSITORY_PATH}.save_all")
    @patch(f"{REPOSITORY_PATH}.get_all")
    def test_product_manager_can_create_feature(
        self,
        mock_get_all,
        mock_save_all,
    ):
        mock_get_all.return_value = {}

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [self.feature],
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["work_items"]), 1)
        self.assertEqual(len(result["events"]), 1)

        created = result["work_items"][0]

        self.assertEqual(created["id"], "FEAT-001")
        self.assertEqual(created["title"], "Inventory Management")
        self.assertEqual(created["work_item_type"], "Feature")
        self.assertEqual(created["created_by"], "productmanager")
        self.assertEqual(created["state"], "Proposed")
        self.assertEqual(created["build_number"], "1.0.0")

        event = result["events"][0]

        self.assertEqual(event["event_type"], "WORK_ITEM_CREATED")
        self.assertEqual(event["work_item_id"], "FEAT-001")
        self.assertEqual(event["actor_id"], "productmanager")
        self.assertEqual(event["actor_role"], "Product Manager")
        self.assertEqual(event["outcome"], "Successful")

        mock_save_all.assert_called_once()

    @patch(f"{REPOSITORY_PATH}.save_all")
    @patch(f"{REPOSITORY_PATH}.get_all")
    def test_batch_creation_succeeds(
        self,
        mock_get_all,
        mock_save_all,
    ):
        mock_get_all.return_value = {}

        second_feature = {
            "id": "FEAT-002",
            "title": "Supplier Management",
            "work_item_type": "Feature",
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [self.feature, second_feature],
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["work_items"]), 2)
        self.assertEqual(len(result["events"]), 2)
        mock_save_all.assert_called_once()

    @patch(f"{REPOSITORY_PATH}.save_all")
    @patch(f"{REPOSITORY_PATH}.get_all")
    def test_all_independently_creatable_scope_types(
        self,
        mock_get_all,
        mock_save_all,
    ):
        mock_get_all.return_value = {}

        supported_types = [
            WorkItemType.EPIC,
            WorkItemType.FEATURE,
            WorkItemType.USE_CASE,
            WorkItemType.REQUIREMENT,
        ]

        payloads = [
            {
                "id": f"ITEM-{index}",
                "title": f"Test {item_type.value}",
                "work_item_type": item_type.value,
            }
            for index, item_type in enumerate(supported_types)
        ]

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            payloads,
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["work_items"]), 4)
        self.assertEqual(len(result["events"]), 4)
        mock_save_all.assert_called_once()

    @patch(f"{SERVICE_PATH}.execute_with_events")
    def test_change_request_relationship_is_built_by_interface(
        self,
        mock_execute,
    ):
        mock_execute.return_value = (
            {"CR-001": object()},
            [],
            ({
                "event_type": "WORK_ITEM_CREATED",
                "work_item_id": "CR-001",
                "actor_id": "productmanager",
            },),
        )

        change_request = {
            "id": "CR-001",
            "title": "Update inventory workflow",
            "work_item_type": "Change Request",
            "relationships": [
                {
                    "target_id": "REQ-001",
                    "relationship_type": "Affected Requirement",
                }
            ],
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [change_request],
        )

        self.assertTrue(result["success"])

        submitted_items = mock_execute.call_args.args[1]
        submitted_change_request = submitted_items[0]
        relationship = submitted_change_request.relationships[0]

        self.assertEqual(relationship.source_id, "CR-001")
        self.assertEqual(relationship.target_id, "REQ-001")
        self.assertEqual(
            relationship.relationship_type,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

    def test_orchestrator_cannot_use_product_manager_interface(self):
        with patch(
            f"{SERVICE_PATH}.execute_with_events"
        ) as mock_execute:
            result = WorkItemAgentInterface.create_work_items(
                "orchestrator",
                [self.feature],
            )

        self.assertFalse(result["success"])
        mock_execute.assert_not_called()

    def test_unknown_agent_is_rejected(self):
        with patch(
            f"{SERVICE_PATH}.execute_with_events"
        ) as mock_execute:
            result = WorkItemAgentInterface.create_work_items(
                "developer",
                [self.feature],
            )

        self.assertFalse(result["success"])
        mock_execute.assert_not_called()

    def test_blank_agent_identity_is_rejected(self):
        result = WorkItemAgentInterface.create_work_items(
            " ",
            [self.feature],
        )

        self.assertFalse(result["success"])
        self.assertIn(
            "Agent identity is required.",
            result["errors"],
        )

    def test_empty_batch_is_rejected(self):
        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [],
        )

        self.assertFalse(result["success"])

    def test_non_list_batch_is_rejected(self):
        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            self.feature,
        )

        self.assertFalse(result["success"])

    def test_missing_required_field_is_rejected(self):
        payload = {
            "id": "FEAT-001",
            "work_item_type": "Feature",
        }

        with patch(
            f"{SERVICE_PATH}.execute_with_events"
        ) as mock_execute:
            result = WorkItemAgentInterface.create_work_items(
                "productmanager",
                [payload],
            )

        self.assertFalse(result["success"])
        mock_execute.assert_not_called()

    def test_unsupported_work_item_field_is_rejected(self):
        payload = {
            **self.feature,
            "created_by": "orchestrator",
        }

        with patch(
            f"{SERVICE_PATH}.execute_with_events"
        ) as mock_execute:
            result = WorkItemAgentInterface.create_work_items(
                "productmanager",
                [payload],
            )

        self.assertFalse(result["success"])
        mock_execute.assert_not_called()

    def test_relationship_source_cannot_be_supplied(self):
        payload = {
            **self.feature,
            "relationships": [
                {
                    "source_id": "FORGED-ID",
                    "target_id": "REQ-001",
                    "relationship_type": "Affected Requirement",
                }
            ],
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])
        self.assertTrue(result["errors"])

    def test_invalid_relationship_type_is_rejected(self):
        payload = {
            **self.feature,
            "relationships": [
                {
                    "target_id": "REQ-001",
                    "relationship_type": "Unknown Relationship",
                }
            ],
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_relationships_must_be_a_list(self):
        payload = {
            **self.feature,
            "relationships": "REQ-001",
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_relationship_target_is_required(self):
        payload = {
            **self.feature,
            "relationships": [
                {
                    "relationship_type": "Affected Requirement",
                }
            ],
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_invalid_work_item_type_is_rejected(self):
        payload = {
            **self.feature,
            "work_item_type": "Unknown Type",
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_development_task_is_rejected(self):
        payload = {
            **self.feature,
            "work_item_type": "Development Task",
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_invalid_acceptance_criteria_is_rejected(self):
        payload = {
            **self.feature,
            "acceptance_criteria": [
                "Valid criterion",
                "",
            ],
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_invalid_build_number_is_rejected(self):
        payload = {
            **self.feature,
            "build_number": 123,
        }

        result = WorkItemAgentInterface.create_work_items(
            "productmanager",
            [payload],
        )

        self.assertFalse(result["success"])

    def test_duplicate_ids_are_rejected_by_manager(self):
        duplicate = {
            **self.feature,
            "title": "Duplicate Feature",
        }

        with patch(
            f"{REPOSITORY_PATH}.get_all",
            return_value={},
        ), patch(
            f"{REPOSITORY_PATH}.save_all"
        ) as mock_save_all:
            result = WorkItemAgentInterface.create_work_items(
                "productmanager",
                [self.feature, duplicate],
            )

        self.assertFalse(result["success"])
        self.assertTrue(result["errors"])
        self.assertEqual(result["events"], [])
        mock_save_all.assert_not_called()

    def test_database_failure_is_not_reported_as_success(self):
        with patch(
            f"{REPOSITORY_PATH}.get_all",
            return_value={},
        ), patch(
            f"{REPOSITORY_PATH}.save_all",
            side_effect=RuntimeError("Database unavailable"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Database unavailable",
            ):
                WorkItemAgentInterface.create_work_items(
                    "productmanager",
                    [self.feature],
                )


if __name__ == "__main__":
    unittest.main()
