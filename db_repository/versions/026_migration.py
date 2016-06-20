from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
order = Table('order', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('order_placed', Boolean),
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
    post_meta.tables['order'].columns['cost_object'].create()
    post_meta.tables['order'].columns['delivery_date'].create()
    post_meta.tables['order'].columns['description'].create()
    post_meta.tables['order'].columns['requestor_name'].create()
    post_meta.tables['order'].columns['requestor_phone'].create()
    post_meta.tables['order'].columns['supervisor_name'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['order'].columns['cost_object'].drop()
    post_meta.tables['order'].columns['delivery_date'].drop()
    post_meta.tables['order'].columns['description'].drop()
    post_meta.tables['order'].columns['requestor_name'].drop()
    post_meta.tables['order'].columns['requestor_phone'].drop()
    post_meta.tables['order'].columns['supervisor_name'].drop()
