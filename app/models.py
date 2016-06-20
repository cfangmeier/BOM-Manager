from os import path
from datetime import datetime
from collections import namedtuple

from app import db

PriceBreak = namedtuple('PriceBreak', ('number', 'price_dollars'))
vendors = {'digipart': 'Digikey'}


class Part(db.Model):
    __tablename__ = 'part'
    id = db.Column(db.Integer, primary_key=True)
    short_description = db.Column(db.String)
    manufacturer = db.Column(db.String)
    image_url = db.Column(db.String)
    manufacturer_part_number = db.Column(db.String)
    bomparts = db.relationship('BOMPart', back_populates='part')
    vendorparts = db.relationship('VendorPart', back_populates='part')


class BOMPart(db.Model):
    __tablename__ = 'bompart'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String)
    lookup_source = db.Column(db.String)
    lookup_id = db.Column(db.String)
    bom_id = db.Column(db.Integer, db.ForeignKey('billofmaterials.id'))
    bom = db.relationship('BillOfMaterials', back_populates='bomparts')
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    part = db.relationship('Part', back_populates='bomparts')


class BillOfMaterials(db.Model):
    __tablename__ = 'billofmaterials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    xml_file = db.Column(db.String)
    version = db.Column(db.String)
    author = db.Column(db.String)
    timestamp = db.Column(db.DateTime)
    bomparts = db.relationship('BOMPart', back_populates='bom')
    orders = db.relationship('Order_BOM', back_populates='bom')

    @staticmethod
    def from_file(xml_file):
        from xml.etree import ElementTree

        def find_lookup_info(comp):
            try:
                for field in comp.find('fields').findall('field'):
                    try:
                        lookup_source = vendors[field.attrib['name']]
                        lookup_id = field.text
                        return lookup_source, lookup_id
                    except KeyError:
                        continue
            except AttributeError:
                pass
            return None, None

        def find_comp_info(comp):
            reference = comp.attrib['ref']
            value = comp.find('value').text
            return reference, value

        bom = BillOfMaterials()
        bom.xml_file = xml_file
        bom.timestamp = datetime.now()

        etree = ElementTree.parse(xml_file)
        for comp in etree.iter('comp'):
            part = BOMPart()
            lookup_source, lookup_id = find_lookup_info(comp)
            part.lookup_source = lookup_source
            part.lookup_id = lookup_id
            reference, value = find_comp_info(comp)
            part.reference = reference
            part.value = value
            bom.bomparts.append(part)
        source = etree.find('design').find('source').text
        bom.name = path.splitext(path.split(source)[1])[0]
        return bom

    def lookup_parts(self):

        for bompart in self.bomparts:
            vendor = vendors[bompart.lookup_source]
            vendor_part_number = bompart.lookup_id
            query = VendorPart.query
            query = query.filter_by(vendor=vendor,
                                    vendor_part_number=vendor_part_number)
            query = query.order_by(VendorPart.fetch_timestamp).desc()
            vendor_part = query.first()
            if vendor_part:
                bompart.part = vendor_part.part
            else:
                pass

        db.commit()


class VendorPart(db.Model):
    __tablename__ = 'vendorpart'
    id = db.Column(db.Integer, primary_key=True)
    json = db.Column(db.String)
    vendor = db.Column(db.String)
    vendor_part_number = db.Column(db.String)
    fetch_timestamp = db.Column(db.DateTime)
    price_breaks = db.Column(db.PickleType)
    url = db.Column(db.String)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    part = db.relationship('Part', back_populates='vendorparts')
    orderparts = db.relationship('Order_VendorPart',
                                 back_populates='vendorpart')

    def get_pricebreak(self, n):
        breaks = []
        for break_ in self.price_breaks:
            cutoff = break_['BreakQuantity']
            price = break_['UnitPrice']
            breaks.append((cutoff, price))
        breaks.sort(reverse=True)
        if n == 0:
            return breaks[-1][1]

        for cut, price in breaks:
            if n >= cut:
                return price
        fmt = 'No price-cut found for quantity {} of vendor part {}.'
        raise ValueError(fmt.format(n, self.vendor_part_number))


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    vendorparts = db.relationship('Order_VendorPart', back_populates='order')
    order_placed = db.Column(db.Boolean)
    description = db.Column(db.String)
    delivery_date = db.Column(db.Date)
    cost_object = db.Column(db.String)
    requestor_name = db.Column(db.String)
    requestor_phone = db.Column(db.String)
    supervisor_name = db.Column(db.String)
    order_name = db.Column(db.String)
    timestamp = db.Column(db.DateTime)
    boms = db.relationship('Order_BOM', back_populates='order')


class Order_BOM(db.Model):
    __tablename__ = 'order_bom'
    id = db.Column(db.Integer, primary_key=True)
    bom_count = db.Column(db.Integer)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    order = db.relationship('Order', back_populates='boms')
    bom_id = db.Column(db.Integer, db.ForeignKey('billofmaterials.id'))
    bom = db.relationship('BillOfMaterials', back_populates='orders')


class Order_VendorPart(db.Model):
    __tablename__ = 'order_vendorpart'
    id = db.Column(db.Integer, primary_key=True)
    number_used = db.Column(db.Integer)
    number_ordered = db.Column(db.Integer)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    order = db.relationship('Order', back_populates='vendorparts')
    vendorpart_id = db.Column(db.Integer, db.ForeignKey('vendorpart.id'))
    vendorpart = db.relationship('VendorPart', back_populates='orderparts')
