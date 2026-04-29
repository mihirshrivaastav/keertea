from flask import Blueprint, jsonify, request

from tapri.services.orders import create_order


orders_bp = Blueprint("orders", __name__)


@orders_bp.post("/api/orders")
def create_order_route():
    payload, status_code = create_order(request.get_json(force=True))
    return jsonify(payload), status_code
