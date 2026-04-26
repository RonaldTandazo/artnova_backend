"""add index artwork_schedule_pending

Revision ID: 60a9b3cf8827
Revises: 33c89609a273
Create Date: 2026-03-07 18:38:52.709086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60a9b3cf8827'
down_revision: Union[str, None] = '33c89609a273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "idx_artwork_schedule_pending",
        "artwork_schedule",
        ["schedule_status", "schedule_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "idx_artwork_schedule_pending",
        table_name="artwork_schedule"
    )
