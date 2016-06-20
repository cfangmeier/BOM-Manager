from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
billofmaterials = Table('billofmaterials', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String),
    Column('xml_file', String),
    Column('version', String),
    Column('author', String),
    Column('timestamp', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['billofmaterials'].columns['author'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['billofmaterials'].columns['author'].drop()
