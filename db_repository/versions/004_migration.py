from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
billpart = Table('billpart', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('reference', VARCHAR),
    Column('bom_id', INTEGER),
    Column('part_id', INTEGER),
)

part = Table('part', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('json', VARCHAR),
    Column('part_number', VARCHAR),
    Column('timestamp', DATETIME),
)

bompart = Table('bompart', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('reference', String),
    Column('value', String),
    Column('vendor', String),
    Column('vendor_part_number', String),
    Column('bom_id', Integer),
)

bompart_orderpart = Table('bompart_orderpart', post_meta,
    Column('bompart_id', Integer),
    Column('orderpart_id', Integer),
)

order = Table('order', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
)

orderpart = Table('orderpart', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('number', Integer),
)

sku = Table('sku', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('json', String),
    Column('vendor', String),
    Column('vendor_part_number', String),
    Column('manufacturer_part_number', String),
    Column('manufacturer', String),
    Column('description', String),
    Column('fetch_timestamp', DateTime),
    Column('price_breaks', PickleType),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['billpart'].drop()
    pre_meta.tables['part'].drop()
    post_meta.tables['bompart'].create()
    post_meta.tables['bompart_orderpart'].create()
    post_meta.tables['order'].create()
    post_meta.tables['orderpart'].create()
    post_meta.tables['sku'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['billpart'].create()
    pre_meta.tables['part'].create()
    post_meta.tables['bompart'].drop()
    post_meta.tables['bompart_orderpart'].drop()
    post_meta.tables['order'].drop()
    post_meta.tables['orderpart'].drop()
    post_meta.tables['sku'].drop()
