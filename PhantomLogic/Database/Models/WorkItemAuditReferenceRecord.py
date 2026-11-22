from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from PhantomLogic.Database.Models.DatabaseBase import DatabaseBase


class WorkItemAuditReferenceRecord(DatabaseBase):

    __tablename__ = "work_item_audit_references"

    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="ck_work_item_audit_references_position",
        ),
        {"schema": "work_items"},
    )

    work_item_id: Mapped[str] = mapped_column(
        String(),
        ForeignKey(
            "work_items.work_items.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    audit_reference: Mapped[str] = mapped_column(
        String(),
        nullable=False,
    )