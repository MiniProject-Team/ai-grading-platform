"""Persist alternative-group metadata for independent question results.

Revision ID: 0002_question_alternative_group
Revises: 0001_initial_schema
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_question_alternative_group"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evaluation_questions", sa.Column("alternative_group", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("evaluation_questions", "alternative_group")