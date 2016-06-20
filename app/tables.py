import re
from itertools import groupby
from flask import flash
from flask_table import Table, Col, LinkCol
from flask.ext.wtf import Form
from wtforms import BooleanField, SubmitField, IntegerField, StringField
from wtforms.validators import NumberRange, DataRequired
from wtforms.widgets.html5 import NumberInput, DateInput


class BOMTable(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    id = LinkCol('ID', 'bom_summary',
                 url_kwargs=dict(id='id'), attr_list=['id'])
    name = Col('Name')
    version = Col('Version')
    author = Col('Author')
    part_count = Col('Part Count')
    timestamp = Col('Uploaded on')

    def __init__(self, boms, **kwargs):
        items = []
        for bom in boms:
            items.append({'name': bom.name,
                          'version': bom.version,
                          'author': bom.author,
                          'id': bom.id,
                          'part_count': len(bom.bomparts),
                          'timestamp': bom.timestamp})
        super().__init__(items, **kwargs)


class OrderTable(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    id = LinkCol('ID', 'order_summary',
                 url_kwargs=dict(id='id'), attr_list=['id'])
    order_name = Col('Name')
    timestamp = Col('Created On')

    def __init__(self, orders, **kwargs):
        items = []
        for order in orders:
            items.append({'id': order.id,
                          'order_name': order.order_name,
                          'timestamp': order.timestamp})
        super().__init__(items, **kwargs)


class VendorLoginTable(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    name = Col('Vendors')
    logged_on = Col('')

    class F(Form):
        pass

    def _build_form(self, vendors):
        for vendor in vendors:
            field = SubmitField(label="Log in")
            setattr(self.F, vendor.name, field)
        self.form = self.F()

    def __init__(self, vendors, **kwargs):
        self._build_form(vendors)
        items = []
        for vendor in vendors:
            if vendor.logged_on:
                items.append({'name': vendor.name,
                              'logged_on': 'logged in'})
            else:
                items.append({'name': vendor.name,
                              'logged_on': getattr(self.form, vendor.name)})
        super().__init__(items, **kwargs)

    def __html__(self):
        return ('<form action="" method="post" name="login" '
                'enctype="multipart/form-data">'
                '{}</form>').format(super().__html__())


class BOMSelectorTable(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    id = Col('ID')
    name = Col('Name')
    version = Col('Version')
    author = Col('Author')
    selector = Col('Select')
    count = Col('Count')

    class F(Form):
        order_name = StringField('Order Name', validators=[DataRequired()])
        description = StringField('Description', validators=[DataRequired()])
        delivery_date = StringField('Delivery Date', widget=DateInput())
        cost_object = StringField('Cost Object', validators=[DataRequired()])
        requestor_name = StringField('Requestor Name',
                                     validators=[DataRequired()])
        requestor_phone = StringField('Requestor Phone',
                                      validators=[DataRequired()])
        supervisor_name = StringField('Supervisor Name',
                                      validators=[DataRequired()])
        order_name = StringField('Order Name', validators=[DataRequired()])
        submit = SubmitField()

    def _field_names(self, item):
        return {'selector': 'selector_{}'.format(item.id),
                'count': 'count_{}'.format(item.id)}

    def _prepare_form(self, items):
        self.inputs = []
        for i, item in enumerate(items):
            field_names = self._field_names(item)
            self.inputs.append((item.id,
                                field_names['selector'],
                                field_names['count']))

            selector = BooleanField(field_names['selector'], default=False)
            setattr(self.F, field_names['selector'], selector)

            count = IntegerField(field_names['count'],
                                 widget=NumberInput(min=1),
                                 validators=[NumberRange(min=0)],
                                 default=1)
            setattr(self.F, field_names['count'], count)

    def __init__(self, items, **kwargs):
        self._prepare_form(items)
        self.f = self.F()
        for i, item in enumerate(items):
            field_names = self._field_names(item)
            items[i] = {'id': item.id,
                        'name': item.name,
                        'version': item.version,
                        'author': item.author,
                        'selector': getattr(self.f, field_names['selector']),
                        'count': getattr(self.f, field_names['count']),
                        }
        super().__init__(items, **kwargs)


class BOMPartTableShort(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    manufacturer = Col('Manufacturer')
    manufacturer_part_number = Col('Manufacturer Part #')
    short_description = Col('Short Description')
    count = Col('Count')
    references = Col('Refs')

    def __init__(self, items, **kwargs):
        items.sort(key=lambda x: int(re.findall('[0-9]+', x.reference)[0]))
        items.sort(key=lambda x: re.findall('[A-Z]+', x.reference)[0])
        item_dicts = []

        def keyfunc(item):
            if item.part is None:
                return ('', '')
            return (item.part.manufacturer, item.part.manufacturer_part_number)
        groups = groupby(sorted(items, key=keyfunc), keyfunc)
        for key, item_list in groups:
            if key == ('', ''):
                continue
            manufacturer, manufacturer_part_number = key

            item_list = list(item_list)
            short_description = item_list[0].part.short_description
            count = len(item_list)
            references = ', '.join(part.reference for part in item_list)
            item_dict = {'manufacturer': manufacturer,
                         'short_description': short_description,
                         'manufacturer_part_number': manufacturer_part_number,
                         'count': count,
                         'references': references}
            item_dicts.append(item_dict)
        super().__init__(item_dicts, **kwargs)


class BOMPartTableFull(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    reference = Col('Ref')
    lookup_source = Col('Vendor')
    lookup_id = Col('Vendor Part #')
    manufacturer = Col('Manufacturer')
    manufacturer_part_number = Col('Manufacturer Part #')

    def __init__(self, items, **kwargs):
        items.sort(key=lambda x: int(re.findall("[0-9]+", x.reference)[0]))
        items.sort(key=lambda x: re.findall("[A-Z]+", x.reference)[0])
        item_dicts = []
        for item in items:
            if item.lookup_id is None:
                continue
            manufacturer = ""
            manufacturer_part_number = ""
            if item.part is not None:
                manufacturer = item.part.manufacturer
                manufacturer_part_number = item.part.manufacturer_part_number
            item_dict = {'reference': item.reference,
                         'lookup_source': item.lookup_source,
                         'lookup_id': item.lookup_id,
                         'manufacturer': manufacturer,
                         'manufacturer_part_number': manufacturer_part_number,
                         }
            item_dicts.append(item_dict)
        super().__init__(item_dicts, **kwargs)


class OrderPartTable(Table):
    classes = ['table', 'table-hover',
               'table-condensed', 'table-striped']
    vendor = Col('Vendor')
    vendor_part_number = Col('Vendor Part #')
    manufacturer = Col('Manufacturer')
    manufacturer_part_number = Col('Manufacturer Part #')
    used_count = Col('Used Count', td_classes=['text-right'])
    order_count = Col('Order Count')
    unit_price = Col('Unit Price', td_classes=['text-right'])
    total_price = Col('Total Price', td_classes=['text-right'])

    class F(Form):
        submit = SubmitField("Update Parts Count")
        export = SubmitField("Download Requisition Forms")

    def _field_name(self, item):
        return "order_number_{}".format(item.id)

    def _prepare_form(self):
        self.input_fields = []
        for i, item in enumerate(self.obj_items):
            field_name = self._field_name(item)
            field = IntegerField(field_name,
                                 widget=NumberInput(min=0),
                                 validators=[NumberRange(min=0)],
                                 default=item.number_ordered,
                                 )
            setattr(self.F, field_name, field)
            self.input_fields.append((field_name, item.id))

    def get_counts(self):
        counts = {}
        for field_name, obj_id in self.input_fields:
            count = getattr(self.f, field_name).data
            counts[obj_id] = count
        return counts

    def render(self):
        self.obj_items.sort(key=lambda x: x.vendorpart.vendor_part_number)
        self.obj_items.sort(key=lambda x: x.vendorpart.vendor)
        item_dicts = []
        for item in self.obj_items:
            vendor = item.vendorpart.vendor
            vendor_part_number = item.vendorpart.vendor_part_number
            manufacturer = item.vendorpart.part.manufacturer
            man_part_number = item.vendorpart.part.manufacturer_part_number
            order_count = getattr(self.f, self._field_name(item))
            try:
                unit_price = item.vendorpart.get_pricebreak(order_count.data)
                total_price = order_count.data*unit_price
            except ValueError as e:
                flash(str(e))
                unit_price = 0
                total_price = 0

            unit_price = '${:.03f}'.format(unit_price)
            total_price = '${:.03f}'.format(total_price)

            item_dict = {'vendor': vendor,
                         'vendor_part_number': vendor_part_number,
                         'manufacturer': manufacturer,
                         'manufacturer_part_number': man_part_number,
                         'used_count': item.number_used,
                         'order_count': order_count,
                         'unit_price': unit_price,
                         'total_price': total_price,
                         }
            item_dicts.append(item_dict)
        super().__init__(item_dicts)

    def __init__(self, items):
        self.obj_items = items
        self._prepare_form()
        self.f = self.F()
