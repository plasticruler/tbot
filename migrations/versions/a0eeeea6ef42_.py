"""empty message

Revision ID: a0eeeea6ef42
Revises: b4599e44dc37
Create Date: 2019-05-19 13:56:56.076558

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0eeeea6ef42'
down_revision = 'b4599e44dc37'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('equity_instrument', sa.Column('jse_code', sa.String(length=8), nullable=True))
    op.create_unique_constraint(None, 'equity_instrument', ['jse_code'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'equity_instrument', type_='unique')
    op.drop_column('equity_instrument', 'jse_code')
    # ### end Alembic commands ###
