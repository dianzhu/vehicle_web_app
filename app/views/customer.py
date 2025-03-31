from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import mysql.connector

from app.views.auth import login_required
from app.db import get_db

bp = Blueprint('customers', __name__, url_prefix='/customers')

@login_required
@bp.route('/add', methods=('GET', 'POST'))
def add():
    to = request.args.get('to') # where to redirect after creation
    if request.method == 'POST':
        customerID = request.form['customerID']
        phoneNumber = request.form['phoneNumber']
        email = request.form['email']
        street = request.form['customerStreet']
        city = request.form['customerCity']
        state = request.form['customerState']
        postalCode = request.form['customerPostalCode']
        type = request.form['select']    

        error = None

        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)  # Create a cursor
            cursor.execute(
                '''INSERT INTO Customer (CustomerID, EmailAddress, Phone, StreetAddress, City, State, PostalCode, CustomerType) 
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)''',
                (customerID, email, phoneNumber, street, city, state, postalCode, type)
            )
            db.commit()
        except mysql.connector.Error as err:
            error = err

        if error is not None:
            flash(error)

        if type == "Person":
            firstName = request.form['firstName']
            lastName = request.form['lastName']

            try:
                db = get_db()
                cursor = db.cursor(dictionary=True)  # Create a cursor
                cursor.execute(
                    'INSERT INTO Individual (DriverLicenseNumber, FirstName, LastName) VALUES(%s, %s, %s)',
                    (customerID, firstName, lastName)
                )
                db.commit()
            except mysql.connector.Error as err:
                error = err

            if error is not None:
                flash(error)
            else:
                flash("Customer added successfully.")
                if to:
                    return redirect(to + f"?customerID={customerID}")
        else:
            companyName = request.form['companyName']
            firstName = request.form['firstName']
            lastName = request.form['lastName']
            title = request.form['title']

            try:
                db = get_db()
                cursor = db.cursor(dictionary=True)  # Create a cursor
                cursor.execute(
                    'INSERT INTO Company (TaxIDNumber, CompanyName, PrimaryContactFirstName, PrimaryContactLastName,PrimaryContactTitle) VALUES(%s, %s, %s, %s, %s)',
                    (customerID, companyName, firstName, lastName, title)
                )
                db.commit()
            except mysql.connector.Error as err:
                error = err

            if error is not None:
                flash(error)
            else:
                flash("Customer added successfully.")
                if to:
                    return redirect(to + f"?customerID={customerID}")

    return render_template("customers/add.html")


@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    customer = None
    failed_search = False
    session['url'] = request.args.get('to')
    if request.method == 'POST':
        name = request.form['customerID']
        error = None
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)  # Create a cursor
            cursor.execute(
                'SELECT * FROM Customer WHERE CustomerID = %s;', (name,)
            )
        except mysql.connector.Error as err:
            error = err

        if error is not None:
            flash(error)
        
        customer = cursor.fetchone()
        
        if customer is None:
            flash('No customer found in this ID.')
            failed_search = True

        return render_template("customers/search.html", customer = customer, failed_search=failed_search)

    return render_template("customers/search.html")


@bp.route('/selectCustomer', methods=['GET', 'POST'])
@login_required
def selectCustomer():
    if request.method == 'POST':
        customerID = request.form['select']
        link = session['url']
        if link:
            if request.args.get('vin'):
                return redirect(link + f"?customerID={customerID}&vin={request.args.get('vin')}")
            return redirect(link + f"?customerID={customerID}")
    flash('Please search and select a customer.')
    return redirect(url_for('customers.search'))
