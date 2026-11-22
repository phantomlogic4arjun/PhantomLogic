from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from PhantomLogic.Database.Models.DatabaseBase import DatabaseBase


class WorkItemRelationshipRecord(DatabaseBase):

    __tablename__ = "work_item_relationships"

    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ("
            "'Parent Child', 'Affected Requirement', "
            "'Violated Requirement', 'Failed Test Case'"
            ")",
            name="ck_work_item_relationships_type",
        ),
        CheckConstraint(
            "position >= 0",
            name="ck_work_item_relationships_position",
        ),
        UniqueConstraint(
            "source_id",
            "position",
            name="uq_work_item_relationships_source_position",
        ),
        Index(
            "ix_work_item_relationships_target_id",
            "target_id",
        ),
        {"schema": "work_items"},
    )

    source_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey(
            "work_items.work_items.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    target_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey(
            "work_items.work_items.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    relationship_type: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )