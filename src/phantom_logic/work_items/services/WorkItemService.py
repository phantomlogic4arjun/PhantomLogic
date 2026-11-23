
from collections.abc import Callable, Mapping
from typing import Any

from phantom_logic.database.repositories.WorkItemRepository import (
    WorkItemRepository,
)
from phantom_logic.work_items.models.WorkItem import WorkItem


class WorkItemService:

    @staticmethod
    def _persist_changes(
        original_work_items: Mapping[str, WorkItem],
        updated_work_items: Mapping[str, WorkItem],
    ) -> None:

        removed_ids = (
            original_work_items.keys() - updated_work_items.keys()
        )

        if removed_ids:
            raise ValueError(
                "Physical Work Item deletion is not supported. "
                f"Removed IDs: {sorted(removed_ids)}"
            )

        changed_work_items = {
            work_item_id: work_item
            for work_item_id, work_item in updated_work_items.items()
            if (
                work_item_id not in original_work_items
                or work_item != original_work_items[work_item_id]
            )
        }

        if changed_work_items:
            WorkItemRepository.save_all(changed_work_items)

    @classmethod
    def execute(
        cls,
        operation: Callable[..., tuple[dict[str, WorkItem] | None, list[str]]],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:

        original_work_items = dict(WorkItemRepository.get_all())

        updated_work_items, errors = operation(
            original_work_items,
            *args,
            **kwargs,
        )

        if errors or updated_work_items is None:
            return updated_work_items, errors

        cls._persist_changes(
            original_work_items,
            updated_work_items,
        )

        return updated_work_items, errors

    @classmethod
    def execute_with_events(
        cls,
        operation: Callable[
            ...,
            tuple[
                dict[str, WorkItem] | None,
                list[str],
                tuple[dict[str, Any], ...],
            ],
        ],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[
        dict[str, WorkItem] | None,
        list[str],
        tuple[dict[str, Any], ...],
    ]:

        original_work_items = dict(WorkItemRepository.get_all())

        updated_work_items, errors, events = operation(
            original_work_items,
            *args,
            **kwargs,
        )

        if errors or updated_work_items is None:
            return updated_work_items, errors, events

        cls._persist_changes(
            original_work_items,
            updated_work_items,
        )

        return updated_work_items, errors, events
