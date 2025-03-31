from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.views.auth import login_required, required_user_types
from app.enums.auth import UserType

from app.db import get_db

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
@login_required
@required_user_types(user_types=[UserType.MANAGER])
def reports_main():
    return render_template('reports/reports_main.html')


@bp.route('/seller_history')
@login_required
@required_user_types(user_types=[UserType.MANAGER])
def seller_history():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Retrieve the data to support the report

    seller_query = '''
        WITH	VehicleParts as (
            SELECT	pts.vin
                ,	sum(pts.Price)		as TotalPartsCost
                ,	sum(pts.Quantity)	as PartsCount
    
            FROM	PARTS   as pts
            GROUP BY pts.vin
        ),
    
            CombinedCustomer as (
            SELECT 	cus.CustomerId					as CustomerId
                ,	COALESCE(com.CompanyName, 
                            CONCAT(ind.FirstName, " ", ind.LastName))	as CustomerName
    
            FROM 		CUSTOMER 	as cus
            LEFT JOIN	COMPANY		as com on cus.CustomerId = com.TaxIDNumber
            LEFT JOIN 	INDIVIDUAL	as ind on cus.CustomerId = ind.DriverLicenseNumber
        )
    
        SELECT	cc.CustomerName					as SellerName
            ,	COUNT(veh.VIN)					as NumberOfVehiclesSold
            ,	CAST(AVG(IFNULL(veh.PurchaseValue,0)) as decimal(10,2))			as AvgPurchaseValue
            ,	CAST(AVG(IFNULL(vp.PartsCount,0)) as decimal(10,2))				as AvgNumberOfParts
            ,	CAST(AVG(IFNULL(vp.TotalPartsCost,0)) as decimal(10,2))			as AvgTotalCostOfParts
            ,	AVG(IFNULL(vp.PartsCount,0)) >= 5 OR
                AVG(IFNULL(vp.TotalPartsCost,0)) >= 500	as IsFlaggedSeller
        
        FROM 	Vehicle 	    	as veh
        LEFT JOIN	VehicleParts		as vp 	on veh.VIN = vp.VIN
        LEFT JOIN	CombinedCustomer	as cc	on veh.PurchasedFrom = cc.CustomerId
        
        GROUP BY CustomerName
        ORDER BY COUNT(VIN) desc, AVG(PurchaseValue) asc
    '''
    cursor.execute(seller_query)
    seller_results = cursor.fetchall()

    return render_template('reports/seller_history.html', sellers = seller_results)


@bp.route('/time_in_inventory')
@login_required
@required_user_types(user_types=[UserType.MANAGER])
def time_in_inventory():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Retrieve the data to support the report

    inventory_query = '''
        WITH type_avg as (
            SELECT	veh.Type								
            ,	CAST(AVG(DATEDIFF(SoldDate,PurchaseDate)+1)
                    as decimal(10,2))							as AvgDaysInInventory
    
            FROM 		Vehicle as veh
            WHERE 1=1
              AND soldDate is not null
            GROUP BY 	veh.Type
        )

        select  vt.Type											as VehicleType
            ,	cast(IFNULL(AvgDaysInInventory,"N/A") as char)	as AvgDaysInInventory
        from vehicleType vt
        left join type_avg ta on vt.type = ta.type
    '''
    cursor.execute(inventory_query)
    inventory_results = cursor.fetchall()

    return render_template('reports/inventory_time.html', inventory=inventory_results)


@bp.route('/price_per_condition')
@login_required
@required_user_types(user_types=[UserType.MANAGER])
def price_per_condition():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Retrieve the data to support the report

    price_query = '''
        WITH pivot as (
            SELECT		Type                 	as 'VehicleType'
                ,	COALESCE(AVG(
                        CASE WHEN VehicleCondition = 'Excellent'
                            THEN PurchaseValue
                        ELSE NULL
                        END),0)					as Excellent
                ,	COALESCE(AVG(
                        CASE WHEN VehicleCondition = 'Very Good' 
                            THEN PurchaseValue
                        ELSE NULL
                        END),0)					as VeryGood
                ,	COALESCE(AVG(
                        CASE WHEN VehicleCondition = 'Good' 
                            THEN PurchaseValue
                        ELSE NULL
                        END),0)					as Good
                ,	COALESCE(AVG(
                        CASE WHEN VehicleCondition = 'Fair' 
                            THEN PurchaseValue
                        ELSE NULL
                        END),0)					as Fair
        
            FROM Vehicle
            GROUP BY Type
            )
            
        SELECT 	vt.type							 				as VehicleType
            ,	cast(Ifnull(Excellent,0) as decimal(10,2))		as Excellent
            ,	cast(Ifnull(VeryGood,0) as decimal(10,2))		as VeryGood
            ,	cast(Ifnull(Good,0) as decimal(10,2))			as Good
            ,	cast(Ifnull(Fair,0) as decimal(10,2))			as Fair
        
        FROM VehicleType vt
        LEFT JOIN pivot p on vt.type = p.vehicletype
    '''
    cursor.execute(price_query)
    price_results = cursor.fetchall()

    return render_template('reports/price_per_condition.html', prices=price_results)

@bp.route('/parts_statistics')
@required_user_types(user_types=[UserType.MANAGER])
def parts_statistics():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    parts_query = '''
        Select VendorName
            ,   cast(sum(Quantity) as decimal(4,0))     as Quantity
            ,   cast(sum(Price) as decimal(10,2))       as TotalSpend
        from Parts
        group by 1
    '''
    cursor.execute(parts_query)
    parts_data = cursor.fetchall()
    return render_template('reports/parts_statistics.html', parts_stats=parts_data)

@bp.route('/monthly-sales-summary')
@required_user_types(user_types=[UserType.MANAGER])
def monthly_sales_report_summary():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = '''
        WITH PartsPrice as (
            Select	VIN
                ,	sum(Price)			as TotalPartsCost
                ,	sum(Price) * 1.1	as PartsPriceMarkup
            From Parts
            Group by 1
        )

        SELECT	Year(Veh.SoldDate) 							AS 'Year'
            ,	Month(Veh.SoldDate) 						AS 'Month'
            ,	MonthName(Veh.SoldDate)						AS 'MonthName'
            ,	COUNT(Distinct Veh.VIN) 					AS VehicleNum
            ,	SUM((1.25 * veh.PurchaseValue) + 
                    (ifnull(PartsPriceMarkup,0)))			AS SalesIncome
            ,	SUM((1.25 * Veh.PurchaseValue) +
                    ifnull(PartsPriceMarkup,0) 
                    - veh.PurchaseValue 
                    - ifnull(TotalPartsCost,0))				AS NetIncome
                
        FROM Vehicle veh
        LEFT JOIN PartsPrice pp ON veh.VIN = pp.VIN
        WHERE 1=1
          and veh.SoldDate IS NOT NULL
        GROUP BY 1,2,3        
        ORDER BY YEAR DESC,MONTH DESC                          
    '''
    cursor.execute(query)
    sales_data = cursor.fetchall()
    return render_template('reports/monthly_sales_report_summary.html', sales_data=sales_data)

@bp.route('/monthly-sales-detail/<month>/<year>')
@login_required
@required_user_types(user_types=[UserType.MANAGER])
def monthly_sales_detail(month, year):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = '''
        WITH PartsPrice as (
            Select	VIN
                ,	sum(Price)			as TotalPartsCost
                ,	sum(Price) * 1.1	as PartsPriceMarkup
            From Parts
            Group by 1
        )

        SELECT	Usr.FirstName 								AS FirstName
			,   Usr.LastName 								AS LastName
            ,	COUNT(Distinct Veh.VIN) 					AS VehicleNum
            ,	SUM((1.25 * veh.PurchaseValue) + 
                    (ifnull(PartsPriceMarkup,0)))			AS SalesIncome
                
        FROM Vehicle veh
        LEFT JOIN PartsPrice pp 		ON veh.VIN = pp.VIN
        LEFT JOIN Users usr 			ON veh.SoldBy = usr.UserName
        
        WHERE 1=1
          and Month(veh.SoldDate) = %s
          and Year(veh.SoldDate) = %s
		
        Group by 1,2
        ORDER BY VehicleNum DESC, SalesIncome DESC;
    '''
    params = [month, year]
    cursor.execute(query, tuple(params))
    sales_data = cursor.fetchall()
    date = datetime.strptime(f"{month}/1/{year}", '%m/%d/%Y').strftime('%B %Y')
    return render_template('reports/monthly_sales_detail.html', sales_data=sales_data, date=date)

