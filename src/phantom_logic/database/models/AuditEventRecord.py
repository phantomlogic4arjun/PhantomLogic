from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from phantom_logic.database.models.DatabaseBase import DatabaseBase


class AuditEventRecord(DatabaseBase):

    __tablename__ = "audit_events"

    __table_args__ = (
        CheckConstraint(
            "approval_required IN ('Yes', 'No')",
            name="ck_audit_events_approval_required",
        ),
        CheckConstraint(
            "outcome IN ("
            "'Successful', 'Failed', 'Partially Completed', "
            "'Cancelled', 'Blocked'"
            ")",
            name="ck_audit_events_outcome",
        ),
        {"schema": "audit"},
    )

    audit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    requesting_party: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    responsible_agent: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    action_requested: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    affected_resources: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    approval_required: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    authorized_by: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    verification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    additional_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
