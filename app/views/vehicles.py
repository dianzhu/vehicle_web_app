from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.views.auth import required_user_types, login_required
from app.enums.auth import UserType
from mysql.connector import Error
from app.db import get_db

bp = Blueprint('vehicle', __name__, url_prefix='/vehicle')


@bp.route('/search', methods=['GET', 'POST'])
def vehicle_search():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Query to count the total number of vehicles for sale
    total_vehicles_for_sale_query = '''
    SELECT COUNT(DISTINCT Vehicle.VIN) AS total_for_sale
    FROM Vehicle
    WHERE NOT EXISTS (
        SELECT 1 FROM Parts
        WHERE Parts.VIN = Vehicle.VIN AND Parts.Status in ('received', 'ordered'))
    AND Vehicle.SoldDate IS NULL
    '''
    cursor.execute(total_vehicles_for_sale_query)
    total_vehicles_for_sale = cursor.fetchone()['total_for_sale']

    vehicles_with_parts_not_installed = 0
    if g.user and (g.user['ManagerUser'] or g.user['InventoryClerkUser']):
        query_not_installed = '''
        SELECT COUNT(DISTINCT Vehicle.VIN) AS count_not_installed
        FROM Vehicle
        JOIN Parts ON Vehicle.VIN = Parts.VIN
        WHERE Parts.Status NOT IN ('installed')
        '''
        cursor.execute(query_not_installed)
        result = cursor.fetchone()
        vehicles_with_parts_not_installed = result['count_not_installed'] if result else 0

    form_values = {
        "Vehicle Type": ["vehicle_type", __get_distinct_values("VehicleType", "Type")],
        "Manufacturer": ["manufacturer", __get_distinct_values("Manufacturer", "ManufacturerName")],
        "Model Year": ["model_year", __get_distinct_values("Vehicle", "ModelYear", "DESC")],
        "Fuel Type": ["fuel_type", __get_distinct_values("Vehicle", "FuelType")],
        "Color": ["color", __get_distinct_values("Colors", "Color")]
    }

    if request.method == 'POST':
        vin = request.form.get('vin')
        vehicle_type = request.form.get('vehicle_type')
        manufacturer = request.form.get('manufacturer')
        model_year = request.form.get('model_year')
        fuel_type = request.form.get('fuel_type')
        color = request.form.get('color')
        description = request.form.get('description')

        # Redirect to vehicle_results with the search criteria as query parameters
        return redirect(url_for('vehicle.vehicle_results',
                                vin=vin,
                                vehicle_type=vehicle_type,
                                manufacturer=manufacturer,
                                model_year=model_year,
                                fuel_type=fuel_type,
                                color=color,
                                description=description))
    else:
        return render_template(
            'vehicles/vehicle_search.html',
            total_vehicles_for_sale=total_vehicles_for_sale,
            vehicles_with_parts_not_installed=vehicles_with_parts_not_installed,
            form_values=form_values
        )


@bp.route('/results')
def vehicle_results():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Retrieve search criteria from query parameters
    search_vin = request.args.get('vin', None)
    search_type = request.args.get('vehicle_type', None)
    manufacturer = request.args.get('manufacturer', None)
    model_year = request.args.get('model_year', None)
    fuel_type = request.args.get('fuel_type', None)
    color = request.args.get('color', None)
    description = request.args.get('description', None)
    part_sort = request.args.get('part_sort', None)
    number_for_sale = request.args.get('number_for_sale', None)
    vehicle_filter = request.args.get('vehicle_filter', 'all')

    # Construct SQL query based on search criteria
    query = '''
        WITH color_string AS (
                SELECT vc.VIN, GROUP_CONCAT(DISTINCT vc.Color) AS Color
                FROM VehicleColors vc
                GROUP BY vc.VIN
        )

        SELECT DISTINCT Vehicle.VIN, Vehicle.Type, Manufacturer.ManufacturerName, 
               Vehicle.ModelYear, Vehicle.ModelName, Vehicle.Mileage, Vehicle.FuelType,
               Color, Vehicle.Description,
               (Vehicle.PurchaseValue * 1.25 + COALESCE(SUM(Parts.Price), 0) * 1.10) AS SalesPrice
               
        FROM Vehicle 
        INNER JOIN color_string cs ON Vehicle.VIN = cs.VIN
        INNER JOIN Manufacturer ON Vehicle.ManufacturerName = Manufacturer.ManufacturerName
        LEFT JOIN Parts ON Vehicle.VIN = Parts.VIN
        WHERE 1=1
    '''
    params = []

    # Exclude vehicles with "pending" parts for certain users and making sure not owner
    # Same exclusion for public users
    if not g.user or (g.user["SalesPersonUser"] and not g.user["InventoryClerkUser"]):
        query += ''' AND NOT EXISTS (
            SELECT 1 FROM Parts
            WHERE Parts.VIN = Vehicle.VIN AND Parts.Status in ('received', 'ordered'))
            AND Vehicle.SoldDate IS NULL
            '''

    if search_vin:
        query += " AND Vehicle.VIN = %s"
        params.append(search_vin)
    if search_type:
        query += " AND Vehicle.Type LIKE %s"
        params.append(f"%{search_type}%")
    if manufacturer:
        query += " AND Manufacturer.ManufacturerName LIKE %s"
        params.append(f"%{manufacturer}%")
    if model_year:
        query += " AND Vehicle.ModelYear = %s"
        params.append(model_year)
    if fuel_type:
        query += " AND Vehicle.FuelType LIKE %s"
        params.append(f"%{fuel_type}%")
    if color:
        query += " AND Color like %s"
        params.append(f"%{color}%")
    if description:
        keyword = f"%{description}%"  # Prepare the keyword for SQL LIKE query
        query += " AND ("
        query += " LOWER(Manufacturer.ManufacturerName) LIKE LOWER(%s)"
        query += " OR LOWER(Vehicle.ModelYear) LIKE LOWER(%s)"
        query += " OR LOWER(Vehicle.ModelName) LIKE LOWER(%s)"
        query += " OR LOWER(Vehicle.Description) LIKE LOWER(%s)"
        query += ")"
        params.extend([keyword, keyword, keyword, keyword])  # Add keyword for each condition

    if g.user:
        if g.user['ManagerUser']:
            if vehicle_filter == 'sold':
                query += " AND Vehicle.SoldTo IS NOT NULL"
                if part_sort: # The only part sort is if its not all or unsold
                    query += " AND Parts.Status = %s"
                    params.append(part_sort)
            elif vehicle_filter == 'unsold':
                query += " AND Vehicle.SoldTo IS NULL"

    # Sort by VIN in ascending order
    query += " GROUP BY Vehicle.VIN ORDER BY Vehicle.VIN ASC"

    # Check if number for sale is valid and set the limit
    # print(f"The Number_for_sale is: {number_for_sale}")
    if number_for_sale and int(number_for_sale) > 0:
        query += " LIMIT %s"
        params.append(int(number_for_sale))

    cursor.execute(query, tuple(params))
    vehicles = cursor.fetchall()

    # print(query) # for debugging
    # print(vehicles)  # for debugging

    # Check user roles and prepare additional data if necessary
    if g.user and (g.user[UserType.INVENTORY_CLERK.value] or g.user[UserType.MANAGER.value]):

        # Render template with additional context
        return render_template('vehicles/vehicle_results.html', vehicles=vehicles,
                               show_add_vehicle_button=True)

    return render_template('vehicles/vehicle_results.html', vehicles=vehicles)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@required_user_types(user_types=[UserType.INVENTORY_CLERK])
def add_vehicle():
    customerId = request.args.get("customerID", default=request.form.get("purchased_from", default=""))
    available_colors = __get_distinct_values("Colors", "Color")
    manufacturers = __get_distinct_values("Manufacturer", "ManufacturerName")
    vehicle_types = __get_distinct_values("VehicleType", "Type")
    if request.method == 'POST':
        today = datetime.today().year + 1
        model_year = request.form.get('new_model_year')
        model = datetime.strptime(f"1/1/{model_year}", '%m/%d/%Y').year
        if model > today:
            flash(f"Cannot add vehicle with model year {model_year}")
            return render_template(
                'vehicles/vehicle_add.html',
                customerID=customerId,
                colors=available_colors,
                manufacturers=manufacturers,
                vehicle_types=vehicle_types
            )

        # Extract form data
        vin = request.form.get('new_vin')
        model_name = request.form.get('model_name')
        vehicle_type = request.form.get('type')
        description = request.form.get('new_description')
        mileage = request.form.get('mileage')
        fuel_type = request.form.get('new_fuel_type')
        manufacturer_name = request.form.get('manufacturer_name')
        purchased_from = request.form.get('purchased_from')
        purchase_date = request.form.get('purchase_date')
        purchase_value = request.form.get('purchase_value')
        condition = request.form.get('condition')
        color = request.form.getlist("color")
        entered_by = g.user['UserName']  # Assuming the logged-in user is entering this data

        # Insert data into the database
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Check if the Customer exists
        cursor.execute("SELECT * FROM Customer WHERE CustomerID = %s", (purchased_from,))
        customer = cursor.fetchone()

        if not customer:
            # Handle the case where Customer does not exist
            # For example, redirect to a form to add customer details
            flash("Customer not found. Please add the customer first.", "error")
            return redirect(url_for('customers.add', to=request.path))

        # Now insert the vehicle data
        try:
            cursor.execute("""
                INSERT INTO Vehicle (VIN, ModelYear, ModelName, Type, Description, Mileage, 
                                     FuelType, ManufacturerName, VehicleCondition, PurchasedFrom, PurchaseDate, 
                                     PurchaseValue, EnteredBy) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (vin, model_year, model_name, vehicle_type, description, mileage, fuel_type,
                      manufacturer_name, condition, purchased_from, purchase_date, purchase_value, entered_by))
            if color:
                for c in color:
                    cursor.execute("INSERT INTO VehicleColors (VIN, Color) VALUES (%s, %s);", (vin, c))
            db.commit()
            flash('Vehicle added successfully', 'success')
            return redirect(url_for('vehicle.vehicle_details', vin=vin))
        except Exception as e:
            db.rollback()
            flash(f'Error adding vehicle: {str(e)}', 'error')
    return render_template(
        'vehicles/vehicle_add.html',
        customerID=customerId,
        colors=available_colors,
        manufacturers=manufacturers,
        vehicle_types=vehicle_types
    )


@bp.route('/details/<vin>', methods=['GET', 'POST'])
def vehicle_details(vin):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        __parse_update_part_status_form(request.form)

    # Fetch vehicle details
    cursor.execute("SELECT * FROM Vehicle WHERE VIN = %s", (vin,))
    vehicle = cursor.fetchone()

    if not vehicle:
        flash("Vehicle not found", category="error")
        return redirect(url_for('vehicle.vehicle_search'))

    # Fetch parts associated with the vehicle
    cursor.execute("SELECT * FROM Parts WHERE VIN = %s", (vin,))
    parts = cursor.fetchall()

    # Calculate sales price
    sales_price = __calculate_sales_price(vehicle['PurchaseValue'], parts)

    # Get colors
    cursor.execute(
        "SELECT GROUP_CONCAT(DISTINCT Color) AS Color FROM VehicleColors WHERE VIN = %s;",
        (vin,)
    )
    colors = cursor.fetchone()
    vehicle["Color"] = colors["Color"]

    # Get purchased from customer info
    vehicle["PurchasedFrom"] = __get_customer_info_for_vehicle_details(vehicle["PurchasedFrom"])

    # Get clerk name
    vehicle["EnteredBy"] = __get_full_name_for_vehicle_details(vehicle["EnteredBy"])

    # Get seller info and sales person name if sold
    if vehicle["SoldTo"]:
        vehicle["SoldTo"] = __get_customer_info_for_vehicle_details(vehicle["SoldTo"])
        vehicle["SoldBy"] = __get_full_name_for_vehicle_details(vehicle["SoldBy"])

    # Separate user login auth for easy if statements and owner handling
    is_clerk = g.user and g.user['InventoryClerkUser']
    is_salesperson = g.user and g.user['SalesPersonUser']
    is_manager = g.user and g.user['ManagerUser']
    return render_template(
        'vehicles/vehicle_details.html',
        vehicle=vehicle,
        parts=parts,
        total_parts_price=__calculate_total_parts_price(parts),
        vehicle_has_pending_parts=__has_pending_parts(parts),
        sales_price=sales_price,
        is_clerk=is_clerk,
        is_salesperson=is_salesperson,
        is_manager=is_manager
    )


@bp.route('/add_sales_order/<vin>/<sales_price>', methods=('GET', 'POST'))
@login_required
@required_user_types(user_types=[UserType.SALES_PERSON])
def add_sales_order(vin, sales_price):
    customerId = request.args.get("customerID", default="")
    sales_person = g.user["UserName"]
    if request.method == 'POST':
        buyer = request.form['buyer']
        salesdate = request.form['salesdate']
        error = None

        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                    UPDATE Vehicle
                    SET SoldTo = %s, SoldDate = %s, SoldBy = %s
                    WHERE VIN = %s;
                """,
                (buyer, salesdate, sales_person, vin)
            )
            db.commit()
        except Error as err:
            error = err

        if error is not None:
            error = "The form data is not valid. Please fill in the form again"
            flash(error)
        else:
            flash("Sales order submitted successfully!")
            return redirect(url_for('index.index'))

    return render_template(
        'vehicles/add_sales_order.html',
        vin=vin,
        customerID=customerId,
        sales_price=float(sales_price),
        sales_person=sales_person
    )


def __calculate_sales_price(purchase_value, parts):
    # Loop through the parts of the vehicle and calculate the price
    parts_cost = sum(part['Price'] for part in parts)
    return 1.25 * purchase_value + 1.10 * parts_cost


def __calculate_total_parts_price(parts):
    return sum(part['Price'] for part in parts)


def __has_pending_parts(parts):
    for part in parts:
        if part["Status"] != 'installed':
            return True
    return False


def __parse_update_part_status_form(update_dict):
    for key in update_dict.keys():
        __update_part_status(key.split(','), update_dict[key])


def __update_part_status(keys, status):
    query = f"""
        UPDATE Parts
            SET Status = '{status}'
        WHERE VIN = '{keys[0]}'
            AND POSequence = '{keys[1]}'
            AND PartNumber = '{keys[2]}'
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(query)
    db.commit()


def __get_customer_info_for_vehicle_details(customer_id):
    customer_query = """
        SELECT * FROM Customer AS c
        LEFT OUTER JOIN Company AS b ON b.TaxIDNumber = c.CustomerID
        LEFT OUTER JOIN Individual AS i ON i.DriverLicenseNumber = c.CustomerID
        where c.CustomerID = %s;
        """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(customer_query, (customer_id,))
    customer = cursor.fetchone()
    customer_info = []
    if customer["CustomerType"] == "Business":
        customer_info += [
            customer["CompanyName"],
            f'{customer["PrimaryContactFirstName"]} {customer["PrimaryContactLastName"]}',
            f'({customer["PrimaryContactTitle"]})'
        ]
    else:
        customer_info.append(f'{customer["FirstName"]} {customer["LastName"]}')
    if customer["EmailAddress"]:
        customer_info.append(customer["EmailAddress"])
    customer_info += [
        f'({customer["Phone"][:3]}){customer["Phone"][3:6]}-{customer["Phone"][6:]}',
        f'{customer["StreetAddress"]}',
        f'{customer["City"]}, {customer["State"]}',
        f'{customer["PostalCode"]}'
    ]
    return customer_info


def __get_full_name_for_vehicle_details(username):
    user_query = "SELECT CONCAT(FirstName , ' ' , LastName) AS Name FROM Users WHERE UserName = %s;"

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(user_query, (username,))
    name = cursor.fetchone()
    return name["Name"]


def __get_distinct_values(table_name, col, order_by="ASC"):
    query = F"SELECT DISTINCT {col} FROM {table_name} ORDER BY {col} {order_by};"
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query)
    return cursor.fetchall()
