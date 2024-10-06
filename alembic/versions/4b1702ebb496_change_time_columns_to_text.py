"""Change time columns to TEXT

Revision ID: 4b1702ebb496
Revises:
Create Date: 2024-09-02 10:40:08.484017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b1702ebb496'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('new_start_time', sa.Text()))
    op.add_column('events', sa.Column('new_end_time', sa.Text()))

    op.execute('UPDATE events SET new_start_time = start_time')
    op.execute('UPDATE events SET new_end_time = end_time')

    op.drop_column('events', 'start_time')
    op.drop_column('events', 'end_time')

    op.alter_column('events', 'new_start_time', new_column_name='start_time')
    op.alter_column('events', 'new_end_time', new_column_name='end_time')

def downgrade() -> None:
    op.add_column('events', sa.Column('old_start_time', sa.OriginalType()))
    op.add_column('events', sa.Column('old_end_time', sa.OriginalType()))

    op.execute('UPDATE events SET old_start_time = start_time')
    op.execute('UPDATE events SET old_end_time = end_time')

    op.drop_column('events', 'start_time')
    op.drop_column('events', 'end_time')

    op.alter_column('events', 'old_start_time', new_column_name='start_time')
    op.alter_column('events', 'old_end_time', new_column_name='end_time')
