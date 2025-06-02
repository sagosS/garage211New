"""add slug fields

Revision ID: 4c5e20ddc396
Revises: 7fd2f67a38b9
Create Date: 2025-06-02 11:33:20.520734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c5e20ddc396'
down_revision = '7fd2f67a38b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('news', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint('uq_news_slug', ['slug'])

    with op.batch_alter_table('promotions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint('uq_promotion_slug', ['slug'])

    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint('uq_service_slug', ['slug'])

def downgrade():
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_constraint('uq_service_slug', type_='unique')
        batch_op.drop_column('slug')

    with op.batch_alter_table('promotions', schema=None) as batch_op:
        batch_op.drop_constraint('uq_promotion_slug', type_='unique')
        batch_op.drop_column('slug')

    with op.batch_alter_table('news', schema=None) as batch_op:
        batch_op.drop_constraint('uq_news_slug', type_='unique')
        batch_op.drop_column('slug')

    # ### end Alembic commands ###
