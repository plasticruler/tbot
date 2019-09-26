"""empty message

Revision ID: 3d72bfdca6ed
Revises: 3e2e2cd91400
Create Date: 2019-09-05 20:26:50.326018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d72bfdca6ed'
down_revision = '3e2e2cd91400'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contenttag_associations',
    sa.Column('contenttag_id', sa.Integer(), nullable=True),
    sa.Column('contentitem_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['contentitem_id'], ['ContentItem.id'], ),
    sa.ForeignKeyConstraint(['contenttag_id'], ['ContentTag.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('contenttag_associations')
    # ### end Alembic commands ###
