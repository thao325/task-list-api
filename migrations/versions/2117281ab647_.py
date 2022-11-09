"""empty message

Revision ID: 2117281ab647
Revises: 9fe357365726
Create Date: 2022-11-07 22:21:34.339744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2117281ab647'
down_revision = '9fe357365726'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('goal', sa.Column('title', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('goal', 'title')
    # ### end Alembic commands ###