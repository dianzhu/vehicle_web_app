from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)

import mysql.connector

from app.views.auth import login_required, required_user_types
from app.enums.auth import UserType
from app.forms.validate import all_fields_required_error

from app.db import get_db

bp = Blueprint('parts', __name__, url_prefix='/parts')


@bp.route('/order/<vin>', methods=('GET', 'POST'))
@login_required
@required_user_types(user_types=[ UserType.INVENTORY_CLERK])
def order(vin):
    vendorName = request.args.get("vendorName", default="")
    error = None
    if request.method == 'POST':
        error = all_fields_required_error(request.form)
        if not error:
            try:
                db = get_db()
                cursor = db.cursor(dictionary=True)  # Create a cursor
                cursor.execute(
                    'SELECT MAX(POSequence) AS max FROM Parts WHERE VIN = %s;', (vin,)
                )
            except mysql.connector.Error as err:
                error = err
            if error:
                flash(error)
            try:
                prevPo = int(cursor.fetchone()['max'])
                po = str(prevPo + 1)
            except TypeError:
                po = "1"
            if len(po) < 3:
                po = (3-len(po)) * "0" + po
            partNumber = request.form.getlist('partNumber')
            vendor = request.form.get('vendorName')
            description = request.form.getlist('description')
            quantity = request.form.getlist('quantity')
            status = request.form.getlist('status')
            price = request.form.getlist('price')

            values = []
            for i in range(len(partNumber)):
                values.append((
                        vin,
                        partNumber[i],
                        po,
                        vendor,
                        description[i],
                        quantity[i],
                        status[i],
                        price[i]
                    ))


            try:
                db = get_db()
                cursor = db.cursor(dictionary=True)  # Create a cursor
                cursor.executemany(
                    '''INSERT INTO Parts (VIN, PartNumber, POSequence, VendorName, Description, Quantity, Status, Price) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                    values
                )
                db.commit()
            except mysql.connector.Error as err:
                error = err

        if error:
            flash(error)
        else:
            return redirect(url_for('parts.order_success', order_number=f"{vin}-{po}"))
    return render_template("parts/order.html", vin=vin, vendorName=vendorName)


@bp.route('/orderSuccess')
@login_required
@required_user_types(user_types=[UserType.INVENTORY_CLERK])
def order_success():
    order_number = request.args.get("order_number", default=None)
    if order_number:
        return render_template("parts/order_success.html", order_number=order_number)
    return redirect(url_for('parts.order'))


@bp.route('/addVendor', methods=('GET', 'POST'))
@login_required
@required_user_types(user_types=[ UserType.INVENTORY_CLERK])
def addVendor():
    if request.method == 'POST':
        name = request.form['vendorName']
        phone = request.form['vendorPhoneNumber']
        street = request.form['vendorStreet']
        city = request.form['vendorCity']
        state = request.form['vendorState']
        postal = request.form['vendorPostal']
        error = None
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)  # Create a cursor
            cursor.execute(
                'INSERT INTO Vendor (VendorName, VendorPhoneNumber, StreetAddress, City, State, PostalCode) VALUES (%s, %s, %s, %s, %s, %s)', 
                (name, phone, street, city, state, postal)
            )
            db.commit()
        except mysql.connector.Error as err:
            error = err

        if error is not None:
            flash(error)
        else:
            # Success, go to the parts order page.
            flash("Successfully Added New Vendor.")
            if request.args.get("to"):
                return redirect(request.args.get("to") + "?vendorName=" + name)
            return redirect(url_for("parts.order", vendorName = name))

    return render_template("parts/addVendor.html")


@bp.route('/searchVendor', methods=('GET', 'POST'))
@login_required
@required_user_types(user_types=[ UserType.INVENTORY_CLERK])
def searchVendor():
    to = request.args.get('to')
    session['url'] = to
    if request.method == 'POST':
        name = request.form['vendorName']
        error = None
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)  # Create a cursor
            cursor.execute(
                'SELECT * FROM vendor WHERE VendorName LIKE %s;', ('%'+ name + '%',)
            )
        except mysql.connector.Error as err:
            error = err

        if error is not None:
            flash(error)
        else:
            vendors = cursor.fetchall()
            if not vendors  :
                flash('Vendor Name Not Found.')

            return render_template("parts/searchVendor.html", vendors = vendors)

    return render_template("parts/searchVendor.html")


@bp.route('/selectVendor', methods=['GET', 'POST'])
@login_required
@required_user_types(user_types=[UserType.INVENTORY_CLERK])
def selectVendor():
    if request.method == 'POST':
        vendorName = request.form['select']
        return redirect(request.args.get("to") + "?vendorName=" + vendorName)
    flash('Please search and select a vendor.')
    return redirect(url_for('parts.searchVendor'))
