
from collections.abc import Mapping
from typing import Any

from PhantomLogic.WorkItems.Manager.WorkItemManager import (
    WorkItemManager,
)
from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.PermissionRules import AgentRole
from PhantomLogic.WorkItems.Services.WorkItemService import (
    WorkItemService,
)


class WorkItemAgentInterface:
    """
    Restricted agent-facing interface for Work Item operations.

    The calling agent identity comes from the trusted OpenCode plugin.
    Agents cannot select their own identity or role.

    Audit events are returned to the caller. The Orchestrator remains
    responsible for submitting them to the central AuditWriter.
    """

    AGENT_ROLES = {
        "productmanager": AgentRole.PRODUCT_MANAGER,
    }

    PRODUCT_MANAGER_CREATE_TYPES = {
        WorkItemType.EPIC,
        WorkItemType.FEATURE,
        WorkItemType.USE_CASE,
        WorkItemType.REQUIREMENT,
        WorkItemType.CHANGE_REQUEST,
    }

    REQUIRED_FIELDS = {
        "id",
        "title",
        "work_item_type",
    }

    OPTIONAL_FIELDS = {
        "description",
        "priority",
        "build_number",
        "acceptance_criteria",
        "relationships",
    }

    RELATIONSHIP_FIELDS = {
        "target_id",
        "relationship_type",
    }

    @classmethod
    def create_work_items(
        cls,
        calling_agent: str,
        work_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(calling_agent, str) or not calling_agent.strip():
            return cls._failure(["Agent identity is required."])

        calling_agent = calling_agent.strip()
        agent_role = cls.AGENT_ROLES.get(calling_agent)

        if agent_role is None:
            return cls._failure([
                f"Agent '{calling_agent}' is not authorized "
                "to use this creation interface."
            ])

        if not isinstance(work_items, list) or not work_items:
            return cls._failure([
                "At least one Work Item must be supplied."
            ])

        new_work_items = []

        for index, payload in enumerate(work_items):
            errors, work_item = cls._build_work_item(
                payload,
                calling_agent,
                index,
            )

            if errors:
                return cls._failure(errors)

            new_work_items.append(work_item)

        updated_collection, errors, events = (
            WorkItemService.execute_with_events(
                WorkItemManager.register_work_items_with_events,
                tuple(new_work_items),
                agent_role,
                actor_id=calling_agent,
            )
        )

        if errors or updated_collection is None:
            return cls._failure(
                errors or ["Work Item registration did not complete."]
            )

        return {
            "success": True,
            "errors": [],
            "work_items": [
                cls._serialize_work_item(item)
                for item in new_work_items
            ],
            "events": list(events),
        }

    @classmethod
    def _build_work_item(
        cls,
        payload: Any,
        calling_agent: str,
        index: int,
    ) -> tuple[list[str], WorkItem | None]:

        if not isinstance(payload, Mapping):
            return [
                f"Work Item at index {index} must be an object."
            ], None

        supplied_fields = set(payload.keys())
        missing_fields = cls.REQUIRED_FIELDS - supplied_fields
        unsupported_fields = (
            supplied_fields
            - cls.REQUIRED_FIELDS
            - cls.OPTIONAL_FIELDS
        )

        errors = []

        if missing_fields:
            errors.append(
                f"Work Item at index {index} is missing required "
                f"fields: {sorted(missing_fields)}."
            )

        if unsupported_fields:
            errors.append(
                f"Work Item at index {index} contains unsupported "
                f"fields: {sorted(unsupported_fields)}."
            )

        if errors:
            return errors, None

        item_id = payload["id"]
        title = payload["title"]
        type_value = payload["work_item_type"]

        if not isinstance(item_id, str) or not item_id.strip():
            errors.append(
                f"Work Item at index {index} has an invalid ID."
            )

        if not isinstance(title, str) or not title.strip():
            errors.append(
                f"Work Item at index {index} has an invalid title."
            )

        work_item_type = None

        if not isinstance(type_value, str):
            errors.append(
                f"Work Item at index {index} has an invalid type."
            )
        else:
            try:
                work_item_type = WorkItemType(type_value)
            except ValueError:
                errors.append(
                    f"Work Item at index {index} has an unsupported "
                    f"Work Item type: {type_value}."
                )

        if (
            work_item_type is not None
            and work_item_type not in cls.PRODUCT_MANAGER_CREATE_TYPES
        ):
            errors.append(
                "Product Manager cannot create "
                f"'{work_item_type.value}' through this interface."
            )

        description = payload.get("description", "")
        priority = payload.get("priority")
        build_number = payload.get("build_number")
        acceptance_criteria = payload.get("acceptance_criteria", [])

        if not isinstance(description, str):
            errors.append(
                f"Work Item at index {index} has an invalid description."
            )

        if priority is not None and (
            not isinstance(priority, str) or not priority.strip()
        ):
            errors.append(
                f"Work Item at index {index} has an invalid priority."
            )

        if build_number is not None and not isinstance(build_number, str):
            errors.append(
                f"Work Item at index {index} has an invalid build number."
            )

        if not isinstance(acceptance_criteria, list):
            errors.append(
                f"Work Item at index {index} acceptance criteria "
                "must be a list."
            )
        elif any(
            not isinstance(item, str) or not item.strip()
            for item in acceptance_criteria
        ):
            errors.append(
                f"Work Item at index {index} contains invalid "
                "acceptance criteria."
            )

        relationship_errors, relationships = cls._build_relationships(
            payload.get("relationships", []),
            item_id,
            index,
        )
        errors.extend(relationship_errors)

        if errors:
            return errors, None

        return [], WorkItem(
            id=item_id.strip(),
            title=title.strip(),
            work_item_type=work_item_type,
            created_by=calling_agent,
            description=description,
            priority=priority,
            build_number=build_number,
            acceptance_criteria=tuple(acceptance_criteria),
            relationships=tuple(relationships),
        )

    @classmethod
    def _build_relationships(
        cls,
        supplied_relationships: Any,
        source_id: Any,
        index: int,
    ) -> tuple[list[str], list[WorkItemRelationship]]:

        if not isinstance(supplied_relationships, list):
            return [
                f"Work Item at index {index} relationships must be a list."
            ], []

        if not isinstance(source_id, str) or not source_id.strip():
            return [
                f"Work Item at index {index} has an invalid relationship source."
            ], []

        errors = []
        relationships = []

        for relationship_index, payload in enumerate(
            supplied_relationships
        ):
            prefix = (
                f"Work Item at index {index}, relationship "
                f"at index {relationship_index}"
            )

            if not isinstance(payload, Mapping):
                errors.append(f"{prefix} must be an object.")
                continue

            supplied_fields = set(payload.keys())

            missing_fields = (
                cls.RELATIONSHIP_FIELDS - supplied_fields
            )
            unsupported_fields = (
                supplied_fields - cls.RELATIONSHIP_FIELDS
            )

            if missing_fields:
                errors.append(
                    f"{prefix} is missing fields: "
                    f"{sorted(missing_fields)}."
                )

            if unsupported_fields:
                errors.append(
                    f"{prefix} contains unsupported fields: "
                    f"{sorted(unsupported_fields)}."
                )

            if missing_fields or unsupported_fields:
                continue

            target_id = payload["target_id"]
            relationship_value = payload["relationship_type"]

            if not isinstance(target_id, str) or not target_id.strip():
                errors.append(f"{prefix} has an invalid target ID.")
                continue

            if not isinstance(relationship_value, str):
                errors.append(
                    f"{prefix} has an invalid relationship type."
                )
                continue

            try:
                relationship_type = RelationshipType(
                    relationship_value
                )
            except ValueError:
                errors.append(
                    f"{prefix} has an unsupported relationship type: "
                    f"{relationship_value}."
                )
                continue

            relationships.append(
                WorkItemRelationship(
                    source_id=source_id.strip(),
                    target_id=target_id.strip(),
                    relationship_type=relationship_type,
                )
            )

        return errors, relationships

    @staticmethod
    def _serialize_work_item(work_item: WorkItem) -> dict[str, Any]:
        return {
            "id": work_item.id,
            "title": work_item.title,
            "work_item_type": work_item.work_item_type.value,
            "created_by": work_item.created_by,
            "state": work_item.state.value,
            "build_number": work_item.build_number,
        }

    @staticmethod
    def _failure(errors: list[str]) -> dict[str, Any]:
        return {
            "success": False,
            "errors": errors,
            "work_items": [],
            "events": [],
        }
