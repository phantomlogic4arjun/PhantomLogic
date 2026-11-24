
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select

from phantom_logic.database.DatabaseManager import DatabaseManager
from phantom_logic.database.models.AuditEventRecord import (
    AuditEventRecord,
)


class AuditEventRepository:
    """
    Persists immutable audit events in PostgreSQL.

    This repository supports insertion and retrieval only.
    It does not expose update or delete operations.
    """

    @staticmethod
    def insert(entry: dict[str, Any]) -> None:
        """
        Insert one validated audit event.

        The caller is responsible for validating the input
        before invoking this method.
        """

        session = DatabaseManager.get_session()

        try:
            record = AuditEventRecord(
                audit_id=entry["audit_id"],
                timestamp=entry["timestamp"],
                requesting_party=entry["requesting_party"],
                responsible_agent=entry["responsible_agent"],
                action_requested=entry["action_requested"],
                purpose=entry["purpose"],
                affected_resources=entry["affected_resources"],
                approval_required=entry["approval_required"],
                authorized_by=entry["authorized_by"],
                outcome=entry["outcome"],
                verification=entry["verification"],
                additional_notes=entry["additional_notes"],
            )

            with session.begin():
                session.add(record)

                # Force the INSERT to execute inside this transaction.
                session.flush()

        except IntegrityError as exc:
            session.rollback()

            original_error = exc.orig

            sqlstate = getattr(
                original_error,
                "sqlstate",
                None,
            )

            constraint_name = getattr(
                getattr(original_error, "diag", None),
                "constraint_name",
                None,
            )

            if (
                sqlstate == "23505"
                and constraint_name == "audit_events_pkey"
            ):
                raise ValueError(
                    f"Duplicate Audit ID: {entry['audit_id']}"
                ) from exc

            raise RuntimeError(
                "Audit event violated a PostgreSQL integrity constraint."
            ) from exc

        except SQLAlchemyError:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def exists(audit_id: str) -> bool:
        """
        Check whether an audit event exists.

        This method is read-only and can be used for verification.
        """

        session = DatabaseManager.get_session()

        try:
            statement = (
                select(AuditEventRecord.audit_id)
                .where(AuditEventRecord.audit_id == audit_id)
            )

            return session.scalar(statement) is not None

        finally:
            session.close()
