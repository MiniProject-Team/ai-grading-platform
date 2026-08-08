"""Create the SmartEval evaluation-history schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-08
"""

from alembic import op

from persistence.base import Base
from persistence import models  # noqa: F401 - registers all metadata tables


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
