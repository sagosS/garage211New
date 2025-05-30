"""add promotions

Revision ID: 892fdc531119
Revises: f320f1488d70
Create Date: 2025-05-27 20:28:03.307288

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '892fdc531119'
down_revision = 'f320f1488d70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('promotion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('image', sa.String(length=128), nullable=True),
    sa.Column('price_from', sa.Float(), nullable=True),
    sa.Column('price_to', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('promotion')
    # ### end Alembic commands ###
