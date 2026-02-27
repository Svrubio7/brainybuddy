"""add supabase_id, drop google_id

Revision ID: a1b2c3d4e5f6
Revises: 464295eaeea9
Create Date: 2026-02-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "464295eaeea9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # supabase_id can be nullable at first so existing rows (if any) survive
    op.add_column("users", sa.Column("supabase_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_users_supabase_id", "users", ["supabase_id"])
    op.create_index("ix_users_supabase_id", "users", ["supabase_id"])
    # The initial migration created a UNIQUE INDEX (not a named constraint)
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "google_id")
    op.drop_column("users", "google_access_token")
    op.drop_column("users", "google_refresh_token")
    op.drop_column("users", "google_token_expiry")


def downgrade() -> None:
    op.add_column("users", sa.Column("google_token_expiry", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("google_refresh_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("google_access_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("google_id", sa.String(), nullable=True))
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.drop_index("ix_users_supabase_id", table_name="users")
    op.drop_constraint("uq_users_supabase_id", "users", type_="unique")
    op.drop_column("users", "supabase_id")
