import re
import zipfile
from datetime import datetime
from collections import namedtuple

from passlib.hash import sha256_crypt

from app import db

# Define the PriceBreak type. Too simple to make own model. Just pickle it and
# store as a binary blob in db.
PriceBreak = namedtuple('PriceBreak', ('number', 'price_dollars'))

# vendors defines the map between field keys in the KiCAD schematic and actual
# Vendor names.
vendors = {'digipart': 'Digikey'}


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    pwd_hash = db.Column(db.String)
    boms = db.relationship('BillOfMaterials', back_populates='user')
    orders = db.relationship('Order', back_populates='user')

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.pwd_hash = sha256_crypt.encrypt(password)

    @staticmethod
    def authenticate(email: str, password: str):
        """ Find and authenticate a user

        Finds a user with a known email and ensure that the password hash
        matches the one on file

        Returns:
            The matching uses if email/password matches one on file, otherwise
            None.

        """
        user = User.query.filter(User.email == email).first()
        if not user:
            return None
        pwd_ok = sha256_crypt.verify(password, user.pwd_hash)
        if not pwd_ok:
            return None
        else:
            return user

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymouse(self):
        return False

    def get_id(self):
        return str(self.id)


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

    @staticmethod
    def from_kicad_schematic_string(sch_string):
        """ Build a part from a KiCAD Schematic Component string
        For example:
        ================================================
        L QTH-090-01-F-D-A P1
        U 1 1 55CCAA2D
        P 2700 5850
        F 0 "P1" H 2700 5750 50  0000 C CNN
        F 1 "QTH-090-01-F-D-A" H 2700 5950 50  0000 C CNN
        F 2 "extras:QTH-090-XX-X-D-A" H 2700 5850 50  0001 C CNN
        F 3 "DOCUMENTATION" H 2700 5850 50  0001 C CNN
        F 4 "SAM8195-ND" H 2700 5850 60  0001 C CNN "digipart"
                1    2700 5850
                1    0    0    -1
        ================================================
        """
        part = BOMPart()
        for line in sch_string.split('\n'):
            fields = line.split()
            if fields[0] == 'L':
                part.reference = fields[2]
            if fields[0] == 'F':
                try:
                    # field 10 is name(if present), also remove quotes
                    field_name = fields[10][1:-1]
                    field_value = fields[2][1:-1]
                    part.lookup_source = vendors[field_name]
                    part.lookup_id = field_value
                except IndexError:  # No valid field name/value
                    continue
                except KeyError:  # unrecognized vendor identifier
                    continue
        return part


class BillOfMaterials(db.Model):
    __tablename__ = 'billofmaterials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    zip_file = db.Column(db.String)
    version = db.Column(db.String)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='boms')
    bomparts = db.relationship('BOMPart', back_populates='bom')
    orders = db.relationship('Order_BOM', back_populates='bom')

    @staticmethod
    def from_kicad_archive(zip_filename):
        zf = zipfile.ZipFile(zip_filename)

        def get_parts_from_schematic(sch_file):
            txt = zf.read(sch_file).decode('utf-8')
            parts = []
            regex = r'\$Comp\s*(.*?)\s*\$EndComp'
            for part_str in re.findall(regex, txt, flags=re.DOTALL):
                part = BOMPart.from_kicad_schematic_string(part_str)
                if part.reference[0] != '#':
                    parts.append(part)
            return parts
        bom = BillOfMaterials()
        bom.zip_file = zip_filename
        bom.timestamp = datetime.now()
        for file_ in zf.filelist:
            if file_.filename.endswith('.sch'):
                sch_parts = get_parts_from_schematic(file_)
                bom.bomparts.extend(sch_parts)
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

    def format_price_breaks(self):
        return '~'.join('{}:{:04f}'.format(x['BreakQuantity'], x['UnitPrice'])
                        for x in self.price_breaks)


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    vendorparts = db.relationship('Order_VendorPart', back_populates='order')
    archived = db.Column(db.Boolean)
    description = db.Column(db.String)
    delivery_date = db.Column(db.Date)
    cost_object = db.Column(db.String)
    requestor_name = db.Column(db.String)
    requestor_phone = db.Column(db.String)
    supervisor_name = db.Column(db.String)
    order_name = db.Column(db.String)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='orders')
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
