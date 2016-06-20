from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
billofmaterials = Table('billofmaterials', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String),
    Column('xml', String),
    Column('timestamp', DateTime),
)

billpart = Table('billpart', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('reference', String),
    Column('bom_id', Integer),
    Column('part_id', Integer),
)

part = Table('part', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('json', VARCHAR),
    Column('DigiKeyPartNumber', VARCHAR),
)

part = Table('part', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('json', String),
    Column('part_number', String),
    Column('timestamp', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['billofmaterials'].create()
    post_meta.tables['billpart'].create()
    pre_meta.tables['part'].columns['DigiKeyPartNumber'].drop()
    post_meta.tables['part'].columns['part_number'].create()
    post_meta.tables['part'].columns['timestamp'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['billofmaterials'].drop()
    post_meta.tables['billpart'].drop()
    pre_meta.tables['part'].columns['DigiKeyPartNumber'].create()
    post_meta.tables['part'].columns['part_number'].drop()
    post_meta.tables['part'].columns['timestamp'].drop()
