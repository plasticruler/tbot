"""backward

Revision ID: a7680d6c4fb5
Revises: 
Create Date: 2019-05-16 20:23:21.990899

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a7680d6c4fb5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('equity_instrument',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('jse_code', sa.String(length=5), nullable=True),
    sa.Column('company_name', sa.String(length=100), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('company_name'),
    sa.UniqueConstraint('jse_code')
    )
    op.create_table('log_self',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(length=512), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('equity_price',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('equityinstrument_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['equityinstrument_id'], ['equity_instrument.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('bot_quote', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('faces', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.alter_column('faces', 'face_encoding',
               existing_type=mysql.VARCHAR(length=5000),
               nullable=True)
    op.add_column('image_file', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('messages_inbound', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('tag', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('user_id', sa.String(length=120), nullable=True))
    op.drop_column('users', 'userid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('userid', mysql.VARCHAR(length=120), nullable=True))
    op.drop_column('users', 'user_id')
    op.drop_column('users', 'created_on')
    op.drop_column('tag', 'created_on')
    op.drop_column('messages_inbound', 'created_on')
    op.drop_column('image_file', 'created_on')
    op.alter_column('faces', 'face_encoding',
               existing_type=mysql.VARCHAR(length=5000),
               nullable=False)
    op.drop_column('faces', 'created_on')
    op.drop_column('bot_quote', 'created_on')
    op.drop_table('equity_price')
    op.drop_table('log_self')
    op.drop_table('equity_instrument')
    # ### end Alembic commands ###
