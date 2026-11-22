from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType


class RelationshipRules:

    ALLOWED_RELATIONSHIPS = {
        (
            WorkItemType.EPIC,
            RelationshipType.PARENT_CHILD,
            WorkItemType.FEATURE,
        ),
        (
            WorkItemType.FEATURE,
            RelationshipType.PARENT_CHILD,
            WorkItemType.USE_CASE,
        ),
        (
            WorkItemType.FEATURE,
            RelationshipType.PARENT_CHILD,
            WorkItemType.SUPPORTING_TASK,
        ),
        (
            WorkItemType.FEATURE,
            RelationshipType.PARENT_CHILD,
            WorkItemType.CODE_REVIEW_TASK,
        ),
        (
            WorkItemType.USE_CASE,
            RelationshipType.PARENT_CHILD,
            WorkItemType.REQUIREMENT,
        ),
        (
            WorkItemType.USE_CASE,
            RelationshipType.PARENT_CHILD,
            WorkItemType.DEVELOPMENT_TASK,
        ),
        (
            WorkItemType.REQUIREMENT,
            RelationshipType.PARENT_CHILD,
            WorkItemType.TEST_CASE,
        ),
        (
            WorkItemType.CHANGE_REQUEST,
            RelationshipType.AFFECTED_REQUIREMENT,
            WorkItemType.REQUIREMENT,
        ),
        (
            WorkItemType.BUG,
            RelationshipType.VIOLATED_REQUIREMENT,
            WorkItemType.REQUIREMENT,
        ),
        (
            WorkItemType.BUG,
            RelationshipType.FAILED_TEST_CASE,
            WorkItemType.TEST_CASE,
        ),
    }

    @classmethod
    def is_valid_relationship(
        cls,
        source_type: WorkItemType,
        relationship_type: RelationshipType,
        target_type: WorkItemType,
    ) -> bool:

        relationship = (
            source_type,
            relationship_type,
            target_type,
        )

        return relationship in cls.ALLOWED_RELATIONSHIPS
