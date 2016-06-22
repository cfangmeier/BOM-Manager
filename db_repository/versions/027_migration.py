from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
order = Table('order', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('order_placed', BOOLEAN),
    Column('description', VARCHAR),
    Column('delivery_date', DATE),
    Column('cost_object', VARCHAR),
    Column('requestor_name', VARCHAR),
    Column('requestor_phone', VARCHAR),
    Column('supervisor_name', VARCHAR),
    Column('order_name', VARCHAR),
    Column('timestamp', DATETIME),
)

order = Table('order', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('archived', Boolean),
    Column('description', String),
    Column('delivery_date', Date),
    Column('cost_object', String),
    Column('requestor_name', String),
    Column('requestor_phone', String),
    Column('supervisor_name', String),
    Column('order_name', String),
    Column('timestamp', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['order'].columns['order_placed'].drop()
    post_meta.tables['order'].columns['archived'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['order'].columns['order_placed'].create()
    post_meta.tables['order'].columns['archived'].drop()
