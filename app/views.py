from collections import defaultdict
from datetime import datetime as dt
from flask import (request, redirect, url_for,
                   render_template, flash, make_response)
from flask.helpers import NotFound
from app import app, db, uploads
from .models import BillOfMaterials, Order, Order_VendorPart, Order_BOM, Part
from .forms import UploadForm, PartSearchForm
from .tables import (BOMTable, BOMPartTableShort, BOMPartTableFull,
                     BOMSelectorTable, OrderTable, VendorLoginTable,
                     OrderPartTable)
from .vendor_fetch import vendors, populate_parts
from .generate_requisition import build_requisition


@app.route("/")
@app.route("/index")
def index():
    boms = BillOfMaterials.query.all()
    bom_table = BOMTable(boms)
    orders = Order.query.all()
    order_table = OrderTable(orders)
    return render_template('index.html',
                           bom_table=bom_table,
                           order_table=order_table)


@app.route("/bom_summary", methods=['GET', 'POST'])
def bom_summary():
    bomid = request.args.get('id')
    display = request.args.get('display', 'full')
    query = BillOfMaterials.query
    query = query.filter(BillOfMaterials.id == bomid)
    bom = query.first()
    if bom is not None:
        if request.method == 'POST':
            populate_parts(bom)
        if display == 'condensed':
            parts_table = BOMPartTableShort(bom.bomparts)
        else:
            parts_table = BOMPartTableFull(bom.bomparts)
        return render_template('bom_summary.html',
                               bom=bom,
                               parts_table=parts_table)
    else:
        raise NotFound()


@app.route('/order_summary', methods=['GET', 'POST'])
def order_summary():
    orderid = request.args.get('id')
    query = Order.query
    query = query.filter(Order.id == orderid)
    order = query.first()
    if order is None:
        raise NotFound()
    parts_table = OrderPartTable(order.vendorparts)
    form = parts_table.f
    if form.validate_on_submit():
        if form.submit.data:
            counts = parts_table.get_counts()
            for part in order.vendorparts:
                part.number_ordered = counts[part.id]
            db.session.commit()
        elif form.export.data:
            zf_data = build_requisition(order)
            response = make_response(zf_data)
            disposition = "attachment; filename=myfile.zip"
            response.headers['Content-Disposition'] = disposition
            return response
    parts_table.render()

    return render_template('order_summary.html',
                           order=order,
                           parts_table=parts_table,
                           form=form)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """ User may upload a new BOM File
    """
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files['file']
        filename = uploads.save(file)
        bom = BillOfMaterials.from_file(uploads.path(filename))
        bom.version = form.version.data
        bom.author = form.author.data
        db.session.add(bom)
        db.session.commit()
        flash("File {} successfully processed.".format(filename))
        return redirect(url_for('bom_summary', id=bom.id))
    return render_template('upload.html', form=form)


@app.route("/new_order", methods=['GET', 'POST'])
def new_order():
    boms = BillOfMaterials.query.all()
    table = BOMSelectorTable(boms)
    form = table.f
    if form.validate_on_submit():
        bom_data = [(id_, getattr(form, c_name).data)
                    for id_, s_name, c_name in table.inputs
                    if getattr(form, s_name).data is True]
        if not bom_data:
            flash('Must select at least 1 BOM to include in order')
            return render_template('new_order.html',
                                   bom_table=table,
                                   form=form)
        count_lookup = {id_: count for id_, count in bom_data}
        bom_ids, _ = zip(*bom_data)
        query = BillOfMaterials.query.filter(BillOfMaterials.id.in_(bom_ids))
        vendorparts = {}
        vendorparts_count = defaultdict(int)
        order = Order()
        order.order_name = form.order_name.data
        order.description = form.description.data
        order.delivery_date = dt.strptime(form.delivery_date.data, "%m/%d/%Y")
        order.cost_object = form.cost_object.data
        order.requestor_name = form.requestor_name.data
        order.requestor_phone = form.requestor_phone.data
        order.supervisor_name = form.supervisor_name.data
        for bom in query.all():
            order_bom = Order_BOM()
            order_bom.order = order
            order_bom.bom = bom
            order_bom.bom_count = count_lookup[bom.id]
            order.boms.append(order_bom)
            db.session.add(order_bom)
            for bompart in bom.bomparts:
                try:
                    vendorpart = [part for part in bompart.part.vendorparts
                                  if part.vendor == bompart.lookup_source][0]
                    key = (vendorpart.vendor, vendorpart.vendor_part_number)
                    vendorparts[key] = vendorpart
                    vendorparts_count[key] += count_lookup[bom.id]
                except (AttributeError, IndexError) as e:
                    print(e)
        order.order_placed = False
        order.timestamp = dt.now()
        db.session.add(order)
        for key, count in vendorparts_count.items():
            order_vendorpart = Order_VendorPart()
            order_vendorpart.number_used = count
            order_vendorpart.number_ordered = count
            order_vendorpart.order = order
            order_vendorpart.vendorpart = vendorparts[key]
            order.vendorparts.append(order_vendorpart)
            db.session.add(order_vendorpart)
        db.session.commit()
        return redirect(url_for('order_summary', id=order.id))

    return render_template('new_order.html',
                           bom_table=table,
                           form=form)


@app.route('/search_part', methods=['GET', 'POST'])
def search_part():
    form = PartSearchForm()
    manufacturers = sorted(m[0] for m in
                           set(db.session.query(Part.manufacturer).all()))
    manufacturers.insert(0, '*')
    manufacturers = [(m, m) for m in manufacturers]
    form.manufacturer.choices = manufacturers
    form.manufacturer.default = '*'
    parts = []
    if form.is_submitted():
        query = Part.query
        manufacturers = form.manufacturer.data
        if '*' not in manufacturers:
            print(manufacturers)
            query = query.filter(Part.manufacturer.in_(manufacturers))
        if form.manufacturer_part_number.validate(form):
            mpn = form.manufacturer_part_number.data
            query = query.filter(Part.manufacturer_part_number == mpn)
        parts = query.all()
    return render_template('search_part.html', form=form, parts=parts)


@app.route("/login", methods=['GET', 'POST'])
def login():
    table = VendorLoginTable(vendors.values())
    if request.method == 'POST':
        selected = list(request.form.keys())[0]
        return vendors[selected].login()
    else:
        return render_template('login.html', vendor_login_table=table)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
