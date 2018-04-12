"""empty message

Revision ID: 11d5916f1efd
Revises: a975105b3305
Create Date: 2017-12-19 15:09:09.105000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11d5916f1efd'
down_revision = 'a975105b3305'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('name', table_name='courses')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('name', 'courses', ['name'], unique=True)
    # ### end Alembic commands ###