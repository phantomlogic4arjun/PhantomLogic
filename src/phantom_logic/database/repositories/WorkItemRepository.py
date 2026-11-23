
from phantom_logic.database.models.WorkItemRecord import WorkItemRecord
from phantom_logic.database.models.WorkItemRelationshipRecord import (
    WorkItemRelationshipRecord,
)
from phantom_logic.database.models.WorkItemAcceptanceCriterionRecord import (
    WorkItemAcceptanceCriterionRecord,
)
from phantom_logic.database.models.WorkItemAuditReferenceRecord import (
    WorkItemAuditReferenceRecord,
)
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
from collections import defaultdict
from phantom_logic.database.DatabaseManager import DatabaseManager
from collections.abc import Mapping
from sqlalchemy import delete, select


class WorkItemRepository:
    """
    Converts between Work Item domain models and database records.

    Database access and persistence operations will be implemented
    separately from these conversion methods.
    """

    @staticmethod
    def _to_record(work_item: WorkItem) -> WorkItemRecord:
        """Convert a domain WorkItem into its database representation."""

        return WorkItemRecord(
            id=work_item.id,
            title=work_item.title,
            description=work_item.description,
            work_item_type=work_item.work_item_type.value,
            state=work_item.state.value,
            created_by=work_item.created_by,
            build_number=work_item.build_number,
            priority=work_item.priority,
            assigned_agent=work_item.assigned_agent,
            created_at=work_item.created_at,
            updated_at=work_item.updated_at,
            block_reason=work_item.block_reason,
            blocked_return_state=(
                work_item.blocked_return_state.value
                if work_item.blocked_return_state is not None
                else None
            ),
            resolution_reason=work_item.resolution_reason,
            removal_reason=work_item.removal_reason,
            authorized_by=work_item.authorized_by,
            authorized_at=work_item.authorized_at,
            authorization_reason=work_item.authorization_reason,
        )

    @staticmethod
    def _to_relationship_records(
        work_item: WorkItem,
    ) -> list[WorkItemRelationshipRecord]:
        """Convert relationships into ordered database records."""

        return [
            WorkItemRelationshipRecord(
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                relationship_type=relationship.relationship_type.value,
                position=index,
            )
            for index, relationship in enumerate(work_item.relationships)
        ]

    @staticmethod
    def _to_acceptance_criterion_records(
        work_item: WorkItem,
    ) -> list[WorkItemAcceptanceCriterionRecord]:
        """Convert acceptance criteria into ordered database records."""

        return [
            WorkItemAcceptanceCriterionRecord(
                work_item_id=work_item.id,
                position=index,
                criterion=criterion,
            )
            for index, criterion in enumerate(work_item.acceptance_criteria)
        ]

    @staticmethod
    def _to_audit_reference_records(
        work_item: WorkItem,
    ) -> list[WorkItemAuditReferenceRecord]:
        """Convert audit references into ordered database records."""

        return [
            WorkItemAuditReferenceRecord(
                work_item_id=work_item.id,
                position=index,
                audit_reference=reference,
            )
            for index, reference in enumerate(work_item.audit_references)
        ]

    @classmethod
    def _from_records(
        cls,
        record: WorkItemRecord,
        relationship_records: list[WorkItemRelationshipRecord],
        criterion_records: list[WorkItemAcceptanceCriterionRecord],
        audit_reference_records: list[WorkItemAuditReferenceRecord],
    ) -> WorkItem:
        """
        Reconstruct a complete domain WorkItem from database records.
        """

        work_item_type = WorkItemType(record.work_item_type)

        state_type = (
            CodeReviewState
            if work_item_type == WorkItemType.CODE_REVIEW_TASK
            else WorkItemState
        )

        relationships = tuple(
            WorkItemRelationship(
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                relationship_type=RelationshipType(
                    relationship.relationship_type
                ),
            )
            for relationship in sorted(
                relationship_records,
                key=lambda item: item.position,
            )
        )

        acceptance_criteria = tuple(
            item.criterion
            for item in sorted(
                criterion_records,
                key=lambda item: item.position,
            )
        )

        audit_references = tuple(
            item.audit_reference
            for item in sorted(
                audit_reference_records,
                key=lambda item: item.position,
            )
        )

        return WorkItem(
            id=record.id,
            title=record.title,
            work_item_type=work_item_type,
            created_by=record.created_by,
            build_number=record.build_number,
            description=record.description,
            state=state_type(record.state),
            priority=record.priority,
            assigned_agent=record.assigned_agent,
            created_at=record.created_at,
            updated_at=record.updated_at,
            relationships=relationships,
            acceptance_criteria=acceptance_criteria,
            block_reason=record.block_reason,
            blocked_return_state=(
                WorkItemState(record.blocked_return_state)
                if record.blocked_return_state is not None
                else None
            ),
            resolution_reason=record.resolution_reason,
            removal_reason=record.removal_reason,
            audit_references=audit_references,
            authorized_by=record.authorized_by,
            authorized_at=record.authorized_at,
            authorization_reason=record.authorization_reason,
        )


    @classmethod
    def get_all(cls) -> dict[str, WorkItem]:
        """Retrieve all Work Items with their associated records."""

        session = DatabaseManager.get_session()

        try:
            records = session.scalars(
                select(WorkItemRecord).order_by(WorkItemRecord.id)
            ).all()

            if not records:
                return {}

            relationship_records = session.scalars(
                select(WorkItemRelationshipRecord).order_by(
                    WorkItemRelationshipRecord.source_id,
                    WorkItemRelationshipRecord.position,
                )
            ).all()

            criterion_records = session.scalars(
                select(WorkItemAcceptanceCriterionRecord).order_by(
                    WorkItemAcceptanceCriterionRecord.work_item_id,
                    WorkItemAcceptanceCriterionRecord.position,
                )
            ).all()

            audit_records = session.scalars(
                select(WorkItemAuditReferenceRecord).order_by(
                    WorkItemAuditReferenceRecord.work_item_id,
                    WorkItemAuditReferenceRecord.position,
                )
            ).all()

            relationships_by_source = defaultdict(list)
            criteria_by_work_item = defaultdict(list)
            audit_references_by_work_item = defaultdict(list)

            for item in relationship_records:
                relationships_by_source[item.source_id].append(item)

            for item in criterion_records:
                criteria_by_work_item[item.work_item_id].append(item)

            for item in audit_records:
                audit_references_by_work_item[item.work_item_id].append(item)

            return {
                record.id: cls._from_records(
                    record,
                    relationships_by_source[record.id],
                    criteria_by_work_item[record.id],
                    audit_references_by_work_item[record.id],
                )
                for record in records
            }

        finally:
            session.close()

    @classmethod
    def get_by_id(cls, work_item_id: str) -> WorkItem | None:
        """Retrieve one Work Item with all its associated records."""

        session = DatabaseManager.get_session()

        try:
            record = session.get(WorkItemRecord, work_item_id)

            if record is None:
                return None

            relationship_records = session.scalars(
                select(WorkItemRelationshipRecord)
                .where(
                    WorkItemRelationshipRecord.source_id == work_item_id
                )
                .order_by(WorkItemRelationshipRecord.position)
            ).all()

            criterion_records = session.scalars(
                select(WorkItemAcceptanceCriterionRecord)
                .where(
                    WorkItemAcceptanceCriterionRecord.work_item_id
                    == work_item_id
                )
                .order_by(WorkItemAcceptanceCriterionRecord.position)
            ).all()

            audit_records = session.scalars(
                select(WorkItemAuditReferenceRecord)
                .where(
                    WorkItemAuditReferenceRecord.work_item_id
                    == work_item_id
                )
                .order_by(WorkItemAuditReferenceRecord.position)
            ).all()

            return cls._from_records(
                record,
                relationship_records,
                criterion_records,
                audit_records,
            )

        finally:
            session.close()


    @staticmethod
    def _validate_work_items(
        work_items: Mapping[str, WorkItem],
    ) -> None:
        """Validate structural consistency before persistence."""

        for work_item_id, work_item in work_items.items():

            if not isinstance(work_item, WorkItem):
                raise TypeError(
                    f"Expected WorkItem for ID '{work_item_id}'."
                )

            if work_item_id != work_item.id:
                raise ValueError(
                    f"Mapping key '{work_item_id}' does not match "
                    f"Work Item ID '{work_item.id}'."
                )

            for relationship in work_item.relationships:

                if relationship.source_id != work_item.id:
                    raise ValueError(
                        f"Relationship source ID "
                        f"'{relationship.source_id}' does not match "
                        f"Work Item ID '{work_item.id}'."
                    )



    @classmethod
    def save(cls, work_item: WorkItem) -> None:
        """Save one Work Item and all its associated records."""

        cls.save_all({work_item.id: work_item})

    @classmethod
    def save_all(
        cls,
        work_items: Mapping[str, WorkItem],
    ) -> None:
        """
        Insert or update Work Items and synchronize their associated records.

        Work Items not included in the supplied mapping are preserved.
        All changes are committed in one transaction.
        """

        if not work_items:
            return

        cls._validate_work_items(work_items)

        session = DatabaseManager.get_session()

        try:
            with session.begin():

                # Persist all main Work Item records first.
                # This ensures relationship foreign keys can be satisfied
                # when their target Work Items are part of this batch.

                for work_item in work_items.values():
                    session.merge(cls._to_record(work_item))

                session.flush()

                # Replace associated records for each supplied Work Item.

                for work_item in work_items.values():

                    session.execute(
                        delete(WorkItemRelationshipRecord).where(
                            WorkItemRelationshipRecord.source_id
                            == work_item.id
                        )
                    )

                    session.execute(
                        delete(WorkItemAcceptanceCriterionRecord).where(
                            WorkItemAcceptanceCriterionRecord.work_item_id
                            == work_item.id
                        )
                    )

                    session.execute(
                        delete(WorkItemAuditReferenceRecord).where(
                            WorkItemAuditReferenceRecord.work_item_id
                            == work_item.id
                        )
                    )

                    # Insert the current associated records.

                    session.add_all(
                        cls._to_relationship_records(work_item)
                    )

                    session.add_all(
                        cls._to_acceptance_criterion_records(work_item)
                    )

                    session.add_all(
                        cls._to_audit_reference_records(work_item)
                    )

        finally:
            session.close()
