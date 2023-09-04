"""Add reset_token column to users

Revision ID: 507f1fc94c58
Revises: 284ee8854a77
Create Date: 2023-09-04 13:58:44.213817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '507f1fc94c58'
down_revision: Union[str, None] = '284ee8854a77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add the reset_token_created_at column to the users table
    op.add_column('users', sa.Column('reset_token_created_at', sa.DateTime))

def downgrade():
    # Remove the reset_token_created_at column from the users table
    op.drop_column('users', 'reset_token_created_at')