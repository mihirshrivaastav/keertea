import logging
import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from tapri.config import Config
from tapri.db import close_db, initialize_database
from tapri.routes.admin import admin_bp
from tapri.routes.orders import orders_bp
from tapri.routes.storefront import storefront_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.config.update(
        STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY"),
        RAZORPAY_KEY_ID=os.getenv("RAZORPAY_KEY_ID"),
        RAZORPAY_KEY_SECRET=os.getenv("RAZORPAY_KEY_SECRET"),
    )

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app.register_blueprint(storefront_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(orders_bp)
    app.teardown_appcontext(close_db)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("Unhandled request failure", exc_info=error)
        return jsonify({"error": "Internal server error. Check server logs for details."}), 500

    with app.app_context():
        initialize_database()
        app.logger.info("Database ready at %s", app.config["DB_PATH"])

    return app
