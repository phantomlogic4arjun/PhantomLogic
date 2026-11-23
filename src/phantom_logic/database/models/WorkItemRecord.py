from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from phantom_logic.database.models.DatabaseBase import DatabaseBase


class WorkItemRecord(DatabaseBase):

    __tablename__ = "work_items"

    __table_args__ = (
        CheckConstraint(
            "work_item_type IN ("
            "'Epic', 'Feature', 'Use Case', 'Requirement', "
            "'Development Task', 'Supporting Task', 'Test Case', "
            "'Bug', 'Change Request', 'Code Review Task'"
            ")",
            name="ck_work_items_type",
        ),
        CheckConstraint(
            "("
            "work_item_type = 'Code Review Task' "
            "AND state IN ('Proposed', 'In Work', 'Review', 'Resolved')"
            ") OR ("
            "work_item_type != 'Code Review Task' "
            "AND state IN ("
            "'Proposed', 'In Work', 'In Test', "
            "'Resolved', 'Blocked', 'Removed'"
            ")"
            ")",
            name="ck_work_items_state",
        ),
        CheckConstraint(
            "blocked_return_state IS NULL OR blocked_return_state IN ("
            "'Proposed', 'In Work', 'In Test', "
            "'Resolved', 'Blocked', 'Removed'"
            ")",
            name="ck_work_items_blocked_return_state",
        ),
        {"schema": "work_items"},
    )

    id: Mapped[str] = mapped_column(String(), primary_key=True)

    title: Mapped[str] = mapped_column(String(), nullable=False)

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    work_item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_by: Mapped[str] = mapped_column(String(), nullable=False)

    build_number: Mapped[str | None] = mapped_column(String())

    priority: Mapped[str | None] = mapped_column(String())

    assigned_agent: Mapped[str | None] = mapped_column(String())

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    block_reason: Mapped[str | None] = mapped_column(Text)

    blocked_return_state: Mapped[str | None] = mapped_column(String(50))

    resolution_reason: Mapped[str | None] = mapped_column(Text)

    removal_reason: Mapped[str | None] = mapped_column(Text)

    authorized_by: Mapped[str | None] = mapped_column(String())

    authorized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    authorization_reason: Mapped[str | None] = mapped_column(Text)