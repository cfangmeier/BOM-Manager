from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
order_vendorpart = Table('order_vendorpart', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('number', INTEGER),
    Column('order_id', INTEGER),
    Column('vendorpart_id', INTEGER),
)

order_vendorpart = Table('order_vendorpart', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('number_used', Integer),
    Column('number_ordered', Integer),
    Column('order_id', Integer),
    Column('vendorpart_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['order_vendorpart'].columns['number'].drop()
    post_meta.tables['order_vendorpart'].columns['number_ordered'].create()
    post_meta.tables['order_vendorpart'].columns['number_used'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['order_vendorpart'].columns['number'].create()
    post_meta.tables['order_vendorpart'].columns['number_ordered'].drop()
    post_meta.tables['order_vendorpart'].columns['number_used'].drop()
