

from collections.abc import Mapping
from datetime import datetime, timedelta

from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.RelationshipRules import RelationshipRules


class WorkItemValidator:
    """
    Central validation for WorkItem identity, structure,
    authorization evidence, and relationships.

    Validation methods return errors instead of raising exceptions
    for invalid user-supplied work-item data.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @staticmethod
    def validate_identity(work_item: WorkItem) -> list[str]:
        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        errors = []

        if not isinstance(work_item.id, str) or not work_item.id.strip():
            errors.append("Work item ID cannot be empty.")

        if (
            not isinstance(work_item.title, str)
            or not work_item.title.strip()
        ):
            errors.append("Work item title cannot be empty.")

        if not isinstance(work_item.work_item_type, WorkItemType):
            errors.append("Work item type is invalid.")

        if (
            not isinstance(work_item.created_by, str)
            or not work_item.created_by.strip()
        ):
            errors.append("Work item creator cannot be empty.")

        return errors

    # ------------------------------------------------------------------
    # Structural validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_structure(cls, work_item: WorkItem) -> list[str]:
        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        if not isinstance(work_item.work_item_type, WorkItemType):
            return [
                "Work item type is invalid; structure cannot be validated."
            ]

        errors = []

        # State validation
        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            if not isinstance(work_item.state, CodeReviewState):
                errors.append(
                    f"Code Review Task '{work_item.id}' "
                    "must use CodeReviewState."
                )
        elif not isinstance(work_item.state, WorkItemState):
            errors.append(
                f"Work item '{work_item.id}' must use WorkItemState."
            )

        # Collection immutability
        collection_fields = (
            ("relationships", work_item.relationships),
            ("acceptance criteria", work_item.acceptance_criteria),
            ("audit references", work_item.audit_references),
        )

        for field_name, value in collection_fields:
            if not isinstance(value, tuple):
                errors.append(
                    f"Work item '{work_item.id}' "
                    f"{field_name} must be immutable."
                )

        # Acceptance criteria
        if isinstance(work_item.acceptance_criteria, tuple):
            for criterion in work_item.acceptance_criteria:
                if (
                    not isinstance(criterion, str)
                    or not criterion.strip()
                ):
                    errors.append(
                        f"Work item '{work_item.id}' "
                        "contains an invalid acceptance criterion."
                    )
                    break

        # Audit references
        if isinstance(work_item.audit_references, tuple):
            for reference in work_item.audit_references:
                if (
                    not isinstance(reference, str)
                    or not reference.strip()
                ):
                    errors.append(
                        f"Work item '{work_item.id}' "
                        "contains an invalid audit reference."
                    )
                    break

        # Authorization evidence
        errors.extend(
            cls.validate_authorization_evidence(work_item)
        )

        # Required relationships can only be checked safely when
        # the relationships collection is a tuple.
        if isinstance(work_item.relationships, tuple):
            errors.extend(
                cls.validate_required_relationships(work_item)
            )

        return errors

    # ------------------------------------------------------------------
    # Authorization evidence
    # ------------------------------------------------------------------

    @staticmethod
    def validate_authorization_evidence(
        work_item: WorkItem,
    ) -> list[str]:
        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        fields = (
            work_item.authorized_by,
            work_item.authorized_at,
            work_item.authorization_reason,
        )

        # Authorization evidence is optional, but must be complete
        # whenever any authorization field is populated.
        if all(value is None for value in fields):
            return []

        if any(value is None for value in fields):
            return [
                f"Work item '{work_item.id}' "
                "has incomplete authorization evidence."
            ]

        if (
            not isinstance(work_item.authorized_by, str)
            or not work_item.authorized_by.strip()
        ):
            return [
                f"Work item '{work_item.id}' "
                "has an invalid authorization identity."
            ]

        if (
            not isinstance(work_item.authorization_reason, str)
            or not work_item.authorization_reason.strip()
        ):
            return [
                f"Work item '{work_item.id}' "
                "has an invalid authorization reason."
            ]

        timestamp = work_item.authorized_at

        if not isinstance(timestamp, datetime):
            return [
                f"Work item '{work_item.id}' authorization timestamp "
                "must be a timezone-aware UTC datetime."
            ]

        if timestamp.tzinfo is None:
            return [
                f"Work item '{work_item.id}' authorization timestamp "
                "must be a timezone-aware UTC datetime."
            ]

        try:
            is_utc = timestamp.utcoffset() == timedelta(0)
        except (TypeError, ValueError, OverflowError):
            is_utc = False

        if not is_utc:
            return [
                f"Work item '{work_item.id}' authorization timestamp "
                "must be a timezone-aware UTC datetime."
            ]

        return []

    # ------------------------------------------------------------------
    # Required relationships
    # ------------------------------------------------------------------

    @staticmethod
    def validate_required_relationships(
        work_item: WorkItem,
    ) -> list[str]:
        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        if not isinstance(work_item.work_item_type, WorkItemType):
            return [
                "Work item type is invalid; required relationships "
                "cannot be validated."
            ]

        if not isinstance(work_item.relationships, tuple):
            return []

        valid_relationships = [
            relationship
            for relationship in work_item.relationships
            if isinstance(relationship, WorkItemRelationship)
        ]

        if work_item.work_item_type == WorkItemType.BUG:
            if not any(
                relationship.relationship_type
                == RelationshipType.VIOLATED_REQUIREMENT
                for relationship in valid_relationships
            ):
                return [
                    f"Bug '{work_item.id}' must reference "
                    "at least one violated Requirement."
                ]

        elif work_item.work_item_type == WorkItemType.CHANGE_REQUEST:
            if not any(
                relationship.relationship_type
                == RelationshipType.AFFECTED_REQUIREMENT
                for relationship in valid_relationships
            ):
                return [
                    f"Change Request '{work_item.id}' must reference "
                    "at least one affected Requirement."
                ]

        return []

    # ------------------------------------------------------------------
    # Relationship reference validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_relationship_references(
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        if not isinstance(work_items, Mapping):
            return ["Work items must be supplied as a mapping."]

        if not isinstance(work_item.relationships, tuple):
            return [
                f"Work item '{work_item.id}' "
                "relationships must be immutable."
            ]

        errors = []
        seen_relationships = set()

        for relationship in work_item.relationships:
            if not isinstance(relationship, WorkItemRelationship):
                errors.append(
                    "Work item contains an invalid relationship object."
                )
                continue

            if (
                not isinstance(relationship.source_id, str)
                or not relationship.source_id.strip()
                or not isinstance(relationship.target_id, str)
                or not relationship.target_id.strip()
                or not isinstance(
                    relationship.relationship_type,
                    RelationshipType,
                )
            ):
                errors.append(
                    "Work item contains a relationship with invalid fields."
                )
                continue

            if relationship in seen_relationships:
                errors.append(
                    f"Duplicate relationship from "
                    f"'{relationship.source_id}' "
                    f"to '{relationship.target_id}'."
                )
                continue

            seen_relationships.add(relationship)

            if relationship.source_id != work_item.id:
                errors.append(
                    f"Relationship source '{relationship.source_id}' "
                    f"does not match owning work item '{work_item.id}'."
                )

            if relationship.target_id == work_item.id:
                errors.append(
                    f"Work item '{work_item.id}' cannot reference itself."
                )
                continue

            if relationship.target_id not in work_items:
                errors.append(
                    f"Relationship target '{relationship.target_id}' "
                    "does not exist."
                )

        return errors

    # ------------------------------------------------------------------
    # Relationship type validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_relationship_types(
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        if not isinstance(work_items, Mapping):
            return ["Work items must be supplied as a mapping."]

        if not isinstance(work_item.work_item_type, WorkItemType):
            return [
                "Work item type is invalid; "
                "relationship types cannot be validated."
            ]

        if not isinstance(work_item.relationships, tuple):
            return [
                f"Work item '{work_item.id}' "
                "relationships must be immutable."
            ]

        errors = []

        for relationship in work_item.relationships:
            if not isinstance(relationship, WorkItemRelationship):
                errors.append(
                    f"Work item '{work_item.id}' contains an invalid "
                    "relationship object."
                )
                continue

            if (
                not isinstance(relationship.source_id, str)
                or not isinstance(relationship.target_id, str)
                or not isinstance(
                    relationship.relationship_type,
                    RelationshipType,
                )
            ):
                continue

            target_work_item = work_items.get(
                relationship.target_id
            )

            if target_work_item is None:
                continue

            if not isinstance(target_work_item, WorkItem):
                errors.append(
                    f"Relationship target '{relationship.target_id}' "
                    "is not a WorkItem instance."
                )
                continue

            if not isinstance(
                target_work_item.work_item_type,
                WorkItemType,
            ):
                errors.append(
                    f"Relationship target '{target_work_item.id}' "
                    "has an invalid work item type."
                )
                continue

            if not RelationshipRules.is_valid_relationship(
                work_item.work_item_type,
                relationship.relationship_type,
                target_work_item.work_item_type,
            ):
                errors.append(
                    f"Relationship from '{work_item.id}' "
                    f"({work_item.work_item_type.value}) to "
                    f"'{target_work_item.id}' "
                    f"({target_work_item.work_item_type.value}) "
                    f"using '{relationship.relationship_type.value}' "
                    "is not permitted."
                )

        return errors
