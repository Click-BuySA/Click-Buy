"""empty message

Revision ID: 4f7082996b06
Revises: 2ee58a3dc755
Create Date: 2023-11-28 16:23:00.354813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f7082996b06'
down_revision: Union[str, None] = '2ee58a3dc755'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('prop_type', sa.String(length=255)))
    op.add_column('properties', sa.Column('agent', sa.String(length=255)))
    op.add_column('properties', sa.Column('stand_area', sa.Integer))
    op.add_column('properties', sa.Column('floor_area', sa.Integer))
    op.add_column('properties', sa.Column('carports', sa.Integer))
    op.add_column('properties', sa.Column('prop_category', sa.String(length=255)))


def downgrade() -> None:
    pass
