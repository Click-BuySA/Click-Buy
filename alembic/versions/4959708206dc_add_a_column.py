"""Add a column

Revision ID: 4959708206dc
Revises: f8f37d6d1c29
Create Date: 2023-08-08 20:22:11.035913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4959708206dc'
down_revision: Union[str, None] = 'f8f37d6d1c29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
