import functools
from typing import List

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app.db import get_db
from app.enums.auth import UserType

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None
        cursor.execute(
            'SELECT * FROM users WHERE UserName = %s', (username,)
        )
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not user["Password"] == password:
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['username'] = user["UserName"]
            if request.args.get("to"):
                return redirect(request.args.get("to"))
            return redirect(url_for('vehicle.vehicle_search'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            f"""
                SELECT u.*, 
                    ic.UserName AS '{UserType.INVENTORY_CLERK.value}', 
                    sp.UserName AS '{UserType.SALES_PERSON.value}', 
                    m.UserName AS '{UserType.MANAGER.value}' FROM users u
                LEFT OUTER JOIN InventoryClerkUser ic ON u.UserName = ic.UserName
                LEFT OUTER JOIN SalesPersonUser sp ON u.UserName = sp.UserName
                LEFT OUTER JOIN ManagerUser m ON u.UserName = m.UserName
                where u.UserName = %s;
            """, (username,)
        )
        g.user = cursor.fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('vehicle.vehicle_search'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', to=request.path))
        return view(**kwargs)
    return wrapped_view


def required_user_types(user_types: List[UserType]):
    def permissions_decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if user_types:
                for user_type in user_types:
                    if g.user[user_type.value]:
                        return view(**kwargs)
                return "404 not found"
            return view(**kwargs)
        return wrapped_view
    return permissions_decorator

