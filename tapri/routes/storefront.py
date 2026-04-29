from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template

from tapri.services.catalog import list_public_products


storefront_bp = Blueprint("storefront", __name__)


@storefront_bp.get("/")
def index():
    return render_template("index.html")


@storefront_bp.get("/api/products")
def products():
    return jsonify(list_public_products())


@storefront_bp.get("/api/health")
def health():
    # UTC timestamps make it easier to compare logs across machines and deploys.
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})
