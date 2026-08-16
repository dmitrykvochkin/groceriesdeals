"""add tool request count to users

Revision ID: 6b2d09af61c8
Revises: 5cc5e489b365
Create Date: 2026-07-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b2d09af61c8"
down_revision: Union[str, Sequence[str], None] = "5cc5e489b365"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "tool_request_count",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "tool_request_count")
