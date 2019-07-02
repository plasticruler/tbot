"""empty message

Revision ID: ae21e05acfe4
Revises: 17edf1daead1
Create Date: 2019-06-30 17:23:51.911015

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ae21e05acfe4'
down_revision = '17edf1daead1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False))
    op.drop_column('users', 'active')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('active', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False))
    op.drop_column('users', 'is_active')
    # ### end Alembic commands ###
