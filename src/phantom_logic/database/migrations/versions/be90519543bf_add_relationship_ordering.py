"""Add relationship ordering

Revision ID: be90519543bf
Revises: 28dfd258f740
Create Date: 2026-11-22 15:35:07.233431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be90519543bf'
down_revision: Union[str, Sequence[str], None] = '28dfd258f740'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "work_item_relationships",
        sa.Column("position", sa.Integer(), nullable=False),
        schema="work_items",
    )

    op.create_unique_constraint(
        "uq_work_item_relationships_source_position",
        "work_item_relationships",
        ["source_id", "position"],
        schema="work_items",
    )

    op.create_check_constraint(
        "ck_work_item_relationships_position",
        "work_item_relationships",
        "position >= 0",
        schema="work_items",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_work_item_relationships_position",
        "work_item_relationships",
        schema="work_items",
        type_="check",
    )

    op.drop_constraint(
        "uq_work_item_relationships_source_position",
        "work_item_relationships",
        schema="work_items",
        type_="unique",
    )

    op.drop_column(
        "work_item_relationships",
        "position",
        schema="work_items",
    )
