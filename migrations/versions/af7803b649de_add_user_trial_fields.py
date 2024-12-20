"""add user trial fields

Revision ID: af7803b649de
Revises: 
Create Date: 2024-12-14 14:26:02.947336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af7803b649de'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('trial_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('trial_end', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('is_trial', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('created_at')
        batch_op.drop_column('is_trial')
        batch_op.drop_column('trial_end')
        batch_op.drop_column('trial_start')

    # ### end Alembic commands ###
