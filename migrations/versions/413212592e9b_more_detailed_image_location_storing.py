"""More detailed image location storing

Revision ID: 413212592e9b
Revises: f9d0c25a835e
Create Date: 2020-10-21 13:38:47.173633

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


# revision identifiers, used by Alembic.
revision = '413212592e9b'
down_revision = 'f9d0c25a835e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('image', sa.Column('geopoint', ga.types.Geometry(geometry_type='POINT', from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))
    op.add_column('image', sa.Column('lat', sa.Float(), nullable=True))
    op.add_column('image', sa.Column('location_description', sa.String(length=1024), nullable=True))
    op.add_column('image', sa.Column('lon', sa.Float(), nullable=True))
    op.drop_column('image', 'location_taken')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('image', sa.Column('location_taken', sa.VARCHAR(length=1024), autoincrement=False, nullable=True))
    op.drop_column('image', 'lon')
    op.drop_column('image', 'location_description')
    op.drop_column('image', 'lat')
    op.drop_column('image', 'geopoint')
    # ### end Alembic commands ###