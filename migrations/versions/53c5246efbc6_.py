"""empty message

Revision ID: 53c5246efbc6
Revises: 440edd881344
Create Date: 2019-06-19 21:30:16.067739

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53c5246efbc6'
down_revision = '440edd881344'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('equity_price', sa.Column('interval', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('equity_price', 'interval')
    # ### end Alembic commands ###
