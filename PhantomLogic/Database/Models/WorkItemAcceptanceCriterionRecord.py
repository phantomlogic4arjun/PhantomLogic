from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from PhantomLogic.Database.Models.DatabaseBase import DatabaseBase


class WorkItemAcceptanceCriterionRecord(DatabaseBase):

    __tablename__ = "work_item_acceptance_criteria"

    __table_args__ = (
        CheckConstraint(
            "position >= 0",
            name="ck_work_item_acceptance_criteria_position",
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

    criterion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )