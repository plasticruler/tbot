"""empty message

Revision ID: 6a965ee04048
Revises: b5acfaaf5d8b
Create Date: 2019-09-28 21:25:49.903136

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6a965ee04048'
down_revision = 'b5acfaaf5d8b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ContentProvider',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('ContentItem', 'providerid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ContentItem', sa.Column('providerid', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=6), nullable=True))
    op.drop_table('ContentProvider')
    # ### end Alembic commands ###
