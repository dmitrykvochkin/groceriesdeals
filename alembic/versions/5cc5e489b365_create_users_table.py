"""create users table

Revision ID: 5cc5e489b365
Revises:
Create Date: 2026-07-24 21:02:57.582388

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5cc5e489b365"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("anonymous_key", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        op.f("ix_users_anonymous_key"), "users", ["anonymous_key"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_users_anonymous_key"), table_name="users")
    op.drop_table("users")
