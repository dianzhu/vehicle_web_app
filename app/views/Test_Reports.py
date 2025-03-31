from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.views.auth import login_required, required_user_types
from app.enums.auth import UserType

from app.db import get_db

bp = Blueprint('Test_Reports', __name__, url_prefix='/test_reports')


@bp.route('/ron_test')
@login_required
@required_user_types(user_types=[UserType.MANAGER, UserType.SALES_PERSON])
def ron_test_view():
    return f"This is a test page to see how we got routed."
