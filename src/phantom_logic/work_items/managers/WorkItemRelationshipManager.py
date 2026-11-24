
from collections.abc import Iterable, Mapping
from dataclasses import replace

from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.HierarchyRules import HierarchyRules
from phantom_logic.work_items.rules.PermissionRules import (
    AgentRole,
    PermissionRules,
    WorkItemOperation,
)
from phantom_logic.work_items.rules.RelationshipRules import RelationshipRules
from phantom_logic.work_items.managers.WorkItemValidator import WorkItemValidator


class WorkItemRelationshipManager:
    """
    Manages work-item relationships through validated, atomic operations.

    Successful operations return a new dictionary containing updated
    WorkItem instances. Original WorkItem instances and their relationship
    tuples are never modified.

    The supplied work-item collection is expected to represent a complete,
    structurally valid hierarchy after each successful operation.
    """

    @classmethod
    def add_relationship(
        cls,
        work_items: Mapping[str, WorkItem],
        relationship: WorkItemRelationship,
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """Add one relationship without mutating the original collection."""

        return cls.add_relationships(
            work_items,
            (relationship,),
            actor_role,
        )

    @classmethod
    def add_relationships(
        cls,
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """Add multiple relationships atomically."""

        return cls._apply_relationship_changes(
            work_items,
            relationships,
            actor_role,
            remove=False,
        )

    @classmethod
    def remove_relationship(
        cls,
        work_items: Mapping[str, WorkItem],
        relationship: WorkItemRelationship,
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """Remove one relationship without mutating the original collection."""

        return cls.remove_relationships(
            work_items,
            (relationship,),
            actor_role,
        )

    @classmethod
    def remove_relationships(
        cls,
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """Remove multiple relationships atomically."""

        return cls._apply_relationship_changes(
            work_items,
            relationships,
            actor_role,
            remove=True,
        )

    @classmethod
    def validate_relationship_change(
        cls,
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
        *,
        remove: bool = False,
    ) -> list[str]:
        """
        Validate a proposed relationship change without applying it.

        An empty error list means the complete proposed operation is valid.
        """

        _, errors = cls._build_candidate(
            work_items,
            relationships,
            actor_role,
            remove=remove,
        )
        return errors

    @classmethod
    def _apply_relationship_changes(
        cls,
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
        *,
        remove: bool,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        candidate, errors = cls._build_candidate(
            work_items,
            relationships,
            actor_role,
            remove=remove,
        )

        if errors:
            return None, errors

        return candidate, []

    @classmethod
    def _build_candidate(
        cls,
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
        *,
        remove: bool,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        errors: list[str] = []

        if not isinstance(work_items, Mapping):
            return None, ["Work items must be supplied as a mapping."]

        if not isinstance(actor_role, AgentRole):
            return None, ["Agent role is invalid."]

        try:
            requested_relationships = tuple(relationships)
        except TypeError:
            return None, ["Relationships must be an iterable collection."]

        if not requested_relationships:
            return None, ["At least one relationship change is required."]

        candidate = dict(work_items)

        # Validate the collection before attempting to change it.
        for work_item_id, work_item in candidate.items():
            if not isinstance(work_item, WorkItem):
                errors.append(
                    f"Work item entry '{work_item_id}' is not a WorkItem instance."
                )
                continue

            if work_item.id != work_item_id:
                errors.append(
                    f"Work item dictionary key '{work_item_id}' "
                    f"does not match work item ID '{work_item.id}'."
                )

            errors.extend(WorkItemValidator.validate_identity(work_item))

            if not isinstance(work_item.relationships, tuple):
                errors.append(
                    f"Work item '{work_item_id}' relationships must be a tuple."
                )

        if errors:
            return None, errors

        seen_requested = set()

        for relationship in requested_relationships:
            if not isinstance(relationship, WorkItemRelationship):
                errors.append(
                    "Every relationship change must be a WorkItemRelationship instance."
                )
                continue

            if relationship in seen_requested:
                errors.append(
                    f"Duplicate relationship change from "
                    f"'{relationship.source_id}' to "
                    f"'{relationship.target_id}'."
                )
                continue

            seen_requested.add(relationship)

            source = candidate.get(relationship.source_id)
            target = candidate.get(relationship.target_id)

            if source is None:
                errors.append(
                    f"Relationship source '{relationship.source_id}' does not exist."
                )
                continue

            if target is None:
                errors.append(
                    f"Relationship target '{relationship.target_id}' does not exist."
                )
                continue

            if not isinstance(source, WorkItem):
                errors.append(
                    f"Relationship source '{relationship.source_id}' "
                    "is not a WorkItem instance."
                )
                continue

            if not isinstance(target, WorkItem):
                errors.append(
                    f"Relationship target '{relationship.target_id}' "
                    "is not a WorkItem instance."
                )
                continue

            if not isinstance(relationship.relationship_type, RelationshipType):
                errors.append("Relationship type is invalid.")
                continue

            permission_errors = PermissionRules.validate_permission(
                actor_role,
                WorkItemOperation.MANAGE_RELATIONSHIPS,
                source,
            )

            errors.extend(permission_errors)

            if not isinstance(source.work_item_type, WorkItemType):
                errors.append(
                    f"Relationship source '{source.id}' has an invalid work item type."
                )
                continue

            if not isinstance(target.work_item_type, WorkItemType):
                errors.append(
                    f"Relationship target '{target.id}' has an invalid work item type."
                )
                continue

            if not RelationshipRules.is_valid_relationship(
                source.work_item_type,
                relationship.relationship_type,
                target.work_item_type,
            ):
                errors.append(
                    f"Relationship from '{source.id}' "
                    f"({source.work_item_type.value}) to "
                    f"'{target.id}' ({target.work_item_type.value}) "
                    f"using '{relationship.relationship_type.value}' "
                    "is not permitted."
                )
                continue

            current_relationships = source.relationships

            if not isinstance(current_relationships, tuple):
                continue

            if remove:
                if relationship not in current_relationships:
                    errors.append(
                        f"Relationship from '{relationship.source_id}' to "
                        f"'{relationship.target_id}' does not exist."
                    )
            elif relationship in current_relationships:
                errors.append(
                    f"Relationship from '{relationship.source_id}' to "
                    f"'{relationship.target_id}' already exists."
                )

        if errors:
            return None, errors

        # Apply requested changes to copied WorkItem instances only.
        changes_by_source: dict[str, list[WorkItemRelationship]] = {}

        for relationship in requested_relationships:
            changes_by_source.setdefault(
                relationship.source_id,
                [],
            ).append(relationship)

        for source_id, source_relationships in changes_by_source.items():
            source = candidate[source_id]

            if remove:
                updated_relationships = tuple(
                    existing
                    for existing in source.relationships
                    if existing not in source_relationships
                )
            else:
                updated_relationships = (
                    source.relationships + tuple(source_relationships)
                )

            candidate[source_id] = replace(
                source,
                relationships=updated_relationships,
            )

        # Validate every relationship in the resulting collection.
        for work_item in candidate.values():
            errors.extend(
                WorkItemValidator.validate_relationship_references(
                    work_item,
                    candidate,
                )
            )
            errors.extend(
                WorkItemValidator.validate_relationship_types(
                    work_item,
                    candidate,
                )
            )

        # Validate the complete resulting hierarchy.
        errors.extend(HierarchyRules.validate_hierarchy(candidate))

        # Bugs and Change Requests must retain at least one Requirement link.
        errors.extend(cls._validate_required_requirement_links(candidate))

        if errors:
            return None, errors

        return candidate, []

    @staticmethod
    def _validate_required_requirement_links(
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        errors = []

        required_links = {
            WorkItemType.BUG: RelationshipType.VIOLATED_REQUIREMENT,
            WorkItemType.CHANGE_REQUEST: RelationshipType.AFFECTED_REQUIREMENT,
        }

        for work_item in work_items.values():
            if not isinstance(work_item, WorkItem):
                continue

            relationship_type = required_links.get(work_item.work_item_type)

            if relationship_type is None:
                continue

            requirement_links = [
                relationship
                for relationship in work_item.relationships
                if (
                    isinstance(relationship, WorkItemRelationship)
                    and relationship.relationship_type == relationship_type
                )
            ]

            if not requirement_links:
                errors.append(
                    f"{work_item.work_item_type.value} '{work_item.id}' "
                    "must reference at least one Requirement."
                )

        return errors
