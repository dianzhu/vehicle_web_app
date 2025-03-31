from flask import (
    Blueprint, render_template
)

bp = Blueprint('test_this', __name__, url_prefix='/testing')


@bp.route('/testing')
def testing():
    return render_template('reports/reports_main.html')
