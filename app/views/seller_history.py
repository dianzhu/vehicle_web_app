from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.views.auth import login_required, required_user_types
from app.enums.auth import UserType

from app.db import get_db

bp = Blueprint('reports', __name__, url_prefix='/reports')