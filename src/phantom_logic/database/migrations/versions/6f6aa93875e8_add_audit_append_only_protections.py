
"""add audit append-only protections

Revision ID: 6f6aa93875e8
Revises: 44946bbbfc98
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.

revision: str = "6f6aa93875e8"
down_revision: Union[str, Sequence[str], None] = "44946bbbfc98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Install append-only protections for audit events."""

    # Create the trigger function.
    op.execute("""
        CREATE OR REPLACE FUNCTION audit.reject_audit_mutation()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'Audit records are append-only. Operation % is prohibited.',
                TG_OP;
        END;
        $$;
    """)

    # Remove manually created triggers if they already exist.
    op.execute("""
        DROP TRIGGER IF EXISTS
        trg_audit_events_no_update_delete
        ON audit.audit_events;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS
        trg_audit_events_no_truncate
        ON audit.audit_events;
    """)

    # Prevent UPDATE and DELETE operations.
    op.execute("""
        CREATE TRIGGER trg_audit_events_no_update_delete
        BEFORE UPDATE OR DELETE
        ON audit.audit_events
        FOR EACH ROW
        EXECUTE FUNCTION audit.reject_audit_mutation();
    """)

    # Prevent TRUNCATE operations.
    op.execute("""
        CREATE TRIGGER trg_audit_events_no_truncate
        BEFORE TRUNCATE
        ON audit.audit_events
        FOR EACH STATEMENT
        EXECUTE FUNCTION audit.reject_audit_mutation();
    """)

    # Restrict direct execution of the trigger function.
    op.execute("""
        REVOKE ALL
        ON FUNCTION audit.reject_audit_mutation()
        FROM PUBLIC;
    """)


def downgrade() -> None:
    """Remove append-only triggers without dropping audit records."""

    op.execute("""
        DROP TRIGGER IF EXISTS
        trg_audit_events_no_update_delete
        ON audit.audit_events;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS
        trg_audit_events_no_truncate
        ON audit.audit_events;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS audit.reject_audit_mutation();
    """)
