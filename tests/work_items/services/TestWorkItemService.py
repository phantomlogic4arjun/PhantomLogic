
import unittest
from unittest.mock import patch

from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.services.WorkItemService import WorkItemService


class TestWorkItemService(unittest.TestCase):

    def setUp(self) -> None:

        self.work_item = WorkItem(
            id="REQ-001",
            title="Original requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        self.original_work_items = {
            self.work_item.id: self.work_item,
        }

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_persists_modified_work_item(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        updated_work_item = WorkItem(
            id="REQ-001",
            title="Updated requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        updated_collection = {"REQ-001": updated_work_item}

        def operation(work_items):
            return updated_collection, []

        result, errors = WorkItemService.execute(operation)

        self.assertEqual(result, updated_collection)
        self.assertEqual(errors, [])
        mock_save_all.assert_called_once_with(updated_collection)

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_persists_new_work_item(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        new_work_item = WorkItem(
            id="REQ-002",
            title="New requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        updated_collection = {
            **self.original_work_items,
            new_work_item.id: new_work_item,
        }

        def operation(work_items):
            return updated_collection, []

        result, errors = WorkItemService.execute(operation)

        self.assertEqual(result, updated_collection)
        self.assertEqual(errors, [])
        mock_save_all.assert_called_once_with({
            new_work_item.id: new_work_item,
        })

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_does_not_persist_unchanged_collection(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        def operation(work_items):
            return work_items, []

        result, errors = WorkItemService.execute(operation)

        self.assertEqual(result, self.original_work_items)
        self.assertEqual(errors, [])
        mock_save_all.assert_not_called()

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_does_not_persist_when_manager_returns_errors(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        def operation(work_items):
            return None, ["Operation rejected"]

        result, errors = WorkItemService.execute(operation)

        self.assertIsNone(result)
        self.assertEqual(errors, ["Operation rejected"])
        mock_save_all.assert_not_called()

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_does_not_persist_when_result_is_none(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        def operation(work_items):
            return None, []

        result, errors = WorkItemService.execute(operation)

        self.assertIsNone(result)
        self.assertEqual(errors, [])
        mock_save_all.assert_not_called()

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_with_events_persists_changes_and_returns_events(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        updated_work_item = WorkItem(
            id="REQ-001",
            title="Updated requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        updated_collection = {"REQ-001": updated_work_item}

        events = (
            {
                "work_item_id": "REQ-001",
                "operation": "Update",
                "actor_id": "productmanager",
            },
        )

        def operation(work_items):
            return updated_collection, [], events

        result, errors, returned_events = (
            WorkItemService.execute_with_events(operation)
        )

        self.assertEqual(result, updated_collection)
        self.assertEqual(errors, [])
        self.assertIs(returned_events, events)
        mock_save_all.assert_called_once_with(updated_collection)

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_with_events_does_not_persist_on_failure(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        events = (
            {
                "work_item_id": "REQ-001",
                "operation": "Update",
                "actor_id": "productmanager",
            },
        )

        def operation(work_items):
            return None, ["Operation rejected"], events

        result, errors, returned_events = (
            WorkItemService.execute_with_events(operation)
        )

        self.assertIsNone(result)
        self.assertEqual(errors, ["Operation rejected"])
        self.assertIs(returned_events, events)
        mock_save_all.assert_not_called()

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_rejects_physical_deletion(
        self,
        mock_get_all,
    ):

        mock_get_all.return_value = self.original_work_items

        def operation(work_items):
            return {}, []

        with self.assertRaisesRegex(
            ValueError,
            "Physical Work Item deletion is not supported",
        ):
            WorkItemService.execute(operation)

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_propagates_database_failure(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        updated_work_item = WorkItem(
            id="REQ-001",
            title="Updated requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        def operation(work_items):
            return {"REQ-001": updated_work_item}, []

        mock_save_all.side_effect = RuntimeError("Database unavailable")

        with self.assertRaisesRegex(
            RuntimeError,
            "Database unavailable",
        ):
            WorkItemService.execute(operation)

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_persists_multiple_modified_work_items(
        self,
        mock_get_all,
        mock_save_all,
    ):

        second_work_item = WorkItem(
            id="REQ-002",
            title="Second requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        original_collection = {
            "REQ-001": self.work_item,
            "REQ-002": second_work_item,
        }

        mock_get_all.return_value = original_collection

        updated_first = WorkItem(
            id="REQ-001",
            title="Updated first requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        updated_second = WorkItem(
            id="REQ-002",
            title="Updated second requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        updated_collection = {
            "REQ-001": updated_first,
            "REQ-002": updated_second,
        }

        def operation(work_items):
            return updated_collection, []

        result, errors = WorkItemService.execute(operation)

        self.assertEqual(result, updated_collection)
        self.assertEqual(errors, [])
        mock_save_all.assert_called_once_with(updated_collection)

    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.save_all"
    )
    @patch(
        "phantom_logic.work_items.services.WorkItemService."
        "WorkItemRepository.get_all"
    )
    def test_execute_forwards_keyword_arguments(
        self,
        mock_get_all,
        mock_save_all,
    ):

        mock_get_all.return_value = self.original_work_items

        updated_work_item = WorkItem(
            id="REQ-001",
            title="Authorized requirement",
            work_item_type=WorkItemType.REQUIREMENT,
            created_by="productmanager",
        )

        updated_collection = {"REQ-001": updated_work_item}

        def operation(work_items, *, actor_id, reason):
            self.assertEqual(actor_id, "architect")
            self.assertEqual(reason, "Architecture review completed")
            return updated_collection, []

        result, errors = WorkItemService.execute(
            operation,
            actor_id="architect",
            reason="Architecture review completed",
        )

        self.assertEqual(result, updated_collection)
        self.assertEqual(errors, [])
        mock_save_all.assert_called_once_with(updated_collection)


if __name__ == "__main__":
    unittest.main()
