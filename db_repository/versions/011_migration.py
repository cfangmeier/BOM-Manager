from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
bompart_orderpart = Table('bompart_orderpart', pre_meta,
    Column('bompart_id', INTEGER),
    Column('orderpart_id', INTEGER),
)

orderpart = Table('orderpart', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('number', INTEGER),
    Column('order_id', INTEGER),
    Column('sku_id', INTEGER),
)

sku = Table('sku', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('json', VARCHAR),
    Column('vendor', VARCHAR),
    Column('vendor_part_number', VARCHAR),
    Column('manufacturer_part_number', VARCHAR),
    Column('manufacturer', VARCHAR),
    Column('description', VARCHAR),
    Column('fetch_timestamp', DATETIME),
    Column('price_breaks', BLOB),
)

order_sku = Table('order_sku', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('number', Integer),
    Column('order_id', Integer),
    Column('sku_id', Integer),
)

part = Table('part', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('manufacturer', String),
    Column('manufacturer_part_number', String),
)

vendorpart = Table('vendorpart', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('json', String),
    Column('vendor', String),
    Column('vendor_part_number', String),
    Column('fetch_timestamp', DateTime),
    Column('price_breaks', PickleType),
    Column('part_id', Integer),
)

bompart = Table('bompart', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('reference', VARCHAR),
    Column('value', VARCHAR),
    Column('vendor', VARCHAR),
    Column('vendor_part_number', VARCHAR),
    Column('bom_id', INTEGER),
)

bompart = Table('bompart', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('reference', String),
    Column('lookup_source', String),
    Column('lookup_id', String),
    Column('bom_id', Integer),
    Column('part_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['bompart_orderpart'].drop()
    pre_meta.tables['orderpart'].drop()
    pre_meta.tables['sku'].drop()
    post_meta.tables['order_sku'].create()
    post_meta.tables['part'].create()
    post_meta.tables['vendorpart'].create()
    pre_meta.tables['bompart'].columns['value'].drop()
    pre_meta.tables['bompart'].columns['vendor'].drop()
    pre_meta.tables['bompart'].columns['vendor_part_number'].drop()
    post_meta.tables['bompart'].columns['lookup_id'].create()
    post_meta.tables['bompart'].columns['lookup_source'].create()
    post_meta.tables['bompart'].columns['part_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['bompart_orderpart'].create()
    pre_meta.tables['orderpart'].create()
    pre_meta.tables['sku'].create()
    post_meta.tables['order_sku'].drop()
    post_meta.tables['part'].drop()
    post_meta.tables['vendorpart'].drop()
    pre_meta.tables['bompart'].columns['value'].create()
    pre_meta.tables['bompart'].columns['vendor'].create()
    pre_meta.tables['bompart'].columns['vendor_part_number'].create()
    post_meta.tables['bompart'].columns['lookup_id'].drop()
    post_meta.tables['bompart'].columns['lookup_source'].drop()
    post_meta.tables['bompart'].columns['part_id'].drop()
