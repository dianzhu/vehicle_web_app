import os
from flask import Flask, render_template
from dotenv import load_dotenv

from . import db
from .views import auth, index, reports, vehicles, parts, customer


def create_app(test_config=None):
    # load environment variables
    load_dotenv()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 404 handling
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html")

    db.init_app(app)

    app.register_blueprint(index.bp)
    app.register_blueprint(vehicles.bp) # Need registered blueprint for each
    app.add_url_rule('/', endpoint='vehicle.vehicle_search')

    app.register_blueprint(auth.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(parts.bp)
    app.register_blueprint(customer.bp)

    return app
