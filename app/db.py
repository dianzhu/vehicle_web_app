import csv
from typing import List

from flask import current_app, g
import mysql.connector
import click
import sqlparse
import os

from mysql.connector import ProgrammingError, DatabaseError, IntegrityError


def get_db():
    if 'db' not in g:
        mysql_db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME")
        )
        g.db = mysql_db
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    create_tables(db)
    insert_dummy_data(db)


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def create_tables(db):
    with current_app.open_resource('schema.sql') as f:
        statements = sqlparse.split(f.read().decode("utf-8"))
        for statement in statements:
            db.cursor().execute(statement)
            db.commit()


def insert_dummy_data(db):
    dummy_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dummy_data')
    vendor_dummy_data_insert(dummy_data_dir, db)
    user_dummy_data_insert(dummy_data_dir, db)
    customer_dummy_data_insert(dummy_data_dir, db)
    vehicles_dummy_data_insert(dummy_data_dir, db)
    parts_dummy_data_insert(dummy_data_dir, db)


def vendor_dummy_data_insert(dummy_data_dir, db):
    with open(os.path.join(dummy_data_dir, "vendors.tsv")) as f:
        vendors = csv.reader(f, delimiter="\t")
        headers = next(vendors)
        vendor_data = []
        for row in vendors:
            vendor_data.append(tuple(row))
        insert_many("Vendor", tuple(headers), vendor_data, db)


def user_dummy_data_insert(dummy_data_dir, db):
    with open(os.path.join(dummy_data_dir, "users.tsv")) as f:
        users = csv.reader(f, delimiter="\t")
        headers = next(users)
        users_data = []
        inventory_clerk_data = []
        sales_person_data = []
        manager_data = []
        for row in users:
            username = row[0]
            user_types = row[-1]
            users_data.append(tuple(row[:-1]))
            if "inventory clerk" in user_types:
                inventory_clerk_data.append((username,))
            if "salesperson" in user_types:
                sales_person_data.append((username,))
            if "manager" in user_types:
                manager_data.append((username,))
        insert_many("Users", tuple(headers[:-1]), users_data, db)
        insert_many("InventoryClerkUser", ('UserName',), inventory_clerk_data, db)
        insert_many("SalesPersonUser", ('UserName',), sales_person_data, db)
        insert_many("ManagerUser", ('UserName',), manager_data, db)


def customer_dummy_data_insert(dummy_data_dir, db):
    with open(os.path.join(dummy_data_dir, "customers.tsv")) as f:
        customers = csv.reader(f, delimiter="\t")
        headers = next(customers)
        customer_id_list = ["CustomerID"]
        customer_cols = customer_id_list + headers[:7]
        companies_cols = headers[7:12]
        individuals_cols = headers[12:]
        customers_data = []
        companies_data = []
        individuals_data = []
        for row in customers:
            customer_id = ""
            if row[0] == "Person":
                individuals_data.append(tuple(row[12:]))
                customer_id = row[12]
            elif row[0] == "Business":
                companies_data.append(tuple(row[7:12]))
                customer_id = row[7]
            customers_data.append(tuple([customer_id] + row[:7]))

        insert_many("Customer", customer_cols, customers_data, db)
        insert_many("Individual", individuals_cols, individuals_data, db)
        insert_many("Company", companies_cols, companies_data, db)


def vehicles_dummy_data_insert(dummy_data_dir, db):
    with open(os.path.join(dummy_data_dir, "vehicles.tsv")) as f:
        vehicles = csv.reader(f, delimiter="\t")
        headers = next(vehicles)
        headers.pop(9)
        colors_col = ['VIN', 'Color']
        vehicle_cols = headers
        colors_data = []
        vehicles_data = []
        for row in vehicles:
            vin = row[0]
            colors = row.pop(9)
            if "," in colors:
                colors = colors.split(",")
                for color in colors:
                    colors_data.append((vin, color))
            else:
                colors_data.append((vin, colors))
            for i, elem in enumerate(row):
                row[i] = None if not elem else elem
            vehicles_data.append(tuple(row))
        insert_many("Vehicle", vehicle_cols, vehicles_data, db)
        insert_many("VehicleColors", colors_col, colors_data, db)


def parts_dummy_data_insert(dummy_data_dir, db):
    with open(os.path.join(dummy_data_dir, "parts.tsv")) as f:
        parts = csv.reader(f, delimiter="\t")
        headers = next(parts)
        parts_data = []
        for row in parts:
            parts_data.append(tuple(row))
        insert_many("Parts", headers, parts_data, db)


def insert_many(table_name, columns, values, db):
    params = "(" + ",".join(["%s" for _ in columns]).replace("'", "") + ")"
    columns = "(" + ",".join(columns).replace("'", "") + ")"
    query = f"""
                INSERT INTO {table_name} {columns} VALUES {params};
            """
    db.cursor().executemany(query, values)
    db.commit()
